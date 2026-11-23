"""Aplicação de terminal em loop para rodar e testar o Coxinh.IA.

Uso:
    python -m src.app.main            # pergunta os recursos autorizados
    python -m src.app.main --livre    # não pergunta; o Chef fica sem restrições
    python -m src.app.main --debug    # imprime também o estado bruto da execução

Comandos dentro do loop:
    /historico    lista as receitas concluídas da sessão
    /ver <id>     mostra uma receita do histórico
    /sair         encerra
"""

import argparse
import json
import os
import subprocess
import textwrap
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from src.graph import builder as graph_builder
from src.graph.impasse import ImpasseDecision, ResumeLimitReached, StateVersionConflict
from src.schemas import Recipe, SubChefEvaluation
from src.persistence.factory import build_session
from src.recipe_session import RecipeSession
from src.state import create_initial_state
from src.utils.ingredients import split_items


def read_line(prompt: str) -> str | None:
    """Lê uma linha; devolve None quando a entrada termina (Ctrl+D)."""
    try:
        return input(prompt).strip()
    except EOFError:
        return None


def parse_list(text: str) -> list[str] | None:
    """Converte texto livre ('a, b e c') em lista; texto vazio significa 'sem restrição'."""
    return split_items(text) or None


def ask_authorizations() -> dict[str, list[str] | None]:
    """Pergunta os recursos que o Chef pode usar. Vazio deixa a categoria livre."""
    print("\nRecursos autorizados (separe por vírgula; Enter = sem restrição).")
    return {
        "authorized_ingredients": parse_list(read_line("  Ingredientes: ") or ""),
        "authorized_utensils": parse_list(read_line("  Utensílios: ") or ""),
        "authorized_preparation_methods": parse_list(
            read_line("  Métodos de preparo: ") or ""
        ),
    }


def print_section(title: str, items: list[str] | str | None) -> None:
    if not items:
        return
    print(f"\n{title}")
    if isinstance(items, str):
        print(f"  {items}")
        return
    for item in items:
        print(f"  - {item}")


def print_final(response: dict[str, Any]) -> None:
    """Mostra a resposta final de uma execução concluída."""
    recipe = response["recipe"]
    health = response["health"]
    image = response["image"]

    print("\n" + "=" * 60)
    print(recipe["title"])
    print(recipe["subtitle"])
    print("=" * 60)
    print_section("Massa", recipe["dough"])
    print_section("Recheio", recipe["filling"])
    print_section("Ingredientes", recipe["ingredients"])
    print_section("Utensílios", recipe["utensils"])
    print_section("Métodos", recipe["preparation_methods"])
    print("\nModo de preparo")
    for number, step in enumerate(recipe["steps"], 1):
        print(textwrap.fill(f"{number}. {step}", width=78, initial_indent="  ", subsequent_indent="     "))

    print(f"\nAconselhamento de consumo [{health['health_status']}]")
    print(f"  {health['warning'] or health['uncertainty'] or '(sem texto)'}")
    for source in health["sources"]:
        print(f"  fonte: {source['title']} - {source['url']}")

    print(f"\nImagem [{image['status']}]: {image['url'] or '(sem imagem)'}")
    url = image["url"] or ""
    path = image_file(response)
    if path:
        print(f"  arquivo: {path}")
    elif url.startswith("images/"):
        print("  (a referência existe, mas o arquivo não está nesta máquina/pasta)")
    elif url.startswith("simulated://"):
        print("  (referência simulada: nenhuma imagem real foi gerada)")
    print(f"Validação de recursos: {response['resource_validation']}")
    print(f"\nPrompt da imagem:\n  {recipe['image_prompt']}")


def image_file(response: dict[str, Any]) -> str | None:
    """Caminho do arquivo da imagem real, ou None (simulada, falha ou ausente)."""
    url = response["image"]["url"] or ""
    if not url.startswith("images/"):
        return None
    storage = os.getenv("IMAGE_STORAGE_DIR", "data/images")
    path = os.path.abspath(os.path.join(storage, url.removeprefix("images/")))
    return path if os.path.isfile(path) else None


def offer_to_open_image(response: dict[str, Any]) -> None:
    """Pergunta se deve abrir a imagem no visualizador padrão do sistema."""
    path = image_file(response)
    if path is None:
        return
    answer = (read_line("\nAbrir a imagem? [s/N] > ") or "n").lower()
    if answer not in ("s", "sim"):
        return
    try:
        subprocess.Popen(
            ["xdg-open", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        print(f"Não consegui abrir automaticamente ({exc}). Arquivo: {path}")


CHOICES = {
    "a": "a", "aceitar": "a",
    "s": "s", "salvar": "s",
    "r": "r", "retomar": "r",
    "c": "c", "cancelar": "c",
}


def wrap(text: str, *, indent: str = "  ", limit: int = 600) -> str:
    """Quebra o texto em linhas curtas e corta o excesso."""
    text = " ".join(str(text).split())
    if len(text) > limit:
        text = text[:limit].rstrip() + "..."
    return textwrap.fill(text, width=78, initial_indent=indent, subsequent_indent=indent)


def print_impasse(result: dict[str, Any]) -> None:
    """Resume o Impasse: o que foi proposto, por que foi rejeitado e as opções."""
    recipe = result.get("recipe")
    evaluation = result.get("subchef_evaluation")

    print("\n" + "#" * 60)
    print("IMPASSE - o SubChef rejeitou a receita e precisa de você")
    print("#" * 60)
    if recipe is not None:
        print("\nMassa:")
        print(wrap(recipe.dough, limit=300))
        print("\nRecheio:")
        print(wrap(recipe.filling, limit=300))
        print(f"\nIngredientes ({len(recipe.ingredients)}):")
        for item in recipe.ingredients:
            print(f"  - {item}")
    if evaluation is not None:
        print("\nMotivo da rejeição (SubChef):")
        print(wrap(evaluation.critique, limit=700))
    print("\nO que você quer fazer?")
    print("  [a] Aceitar assim mesmo -> segue para Cozinheiro, Saúde, Imagem e resposta final")
    print("  [s] Salvar orientação   -> guarda ingredientes/dica; depois escolha [r]")
    print("  [r] Retomar             -> o Chef tenta de novo (com o que você salvou)")
    print("  [c] Cancelar            -> encerra sem receita")


def handle_impasse(
    session: RecipeSession,
    thread_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Conduz o Impasse até a execução terminar ou ser cancelada."""
    while result.get("status") == "awaiting_user":
        print_impasse(result)
        raw_choice = (read_line("\nEscolha [a/s/r/c] > ") or "c").lower()
        choice = CHOICES.get(raw_choice, "")
        key = uuid4().hex
        version = result["state_version"]

        if choice == "s":
            added = parse_list(read_line("Ingredientes a adicionar (texto livre: vírgula, \"e\" ou ;): ") or "")
            guidance = (read_line("Orientação para o Chef: ") or "").strip() or None
            if not (added or guidance):
                print("Salvar exige um ingrediente ou uma orientação. Tente de novo.")
                continue
            print("Salvo. Escolha [r] para o Chef tentar de novo.")
            decision = ImpasseDecision(
                action="save",
                expected_state_version=version,
                idempotency_key=key,
                ingredient_additions=added or [],
                user_guidance=guidance,
            )
        elif choice == "r":
            print("\nRetomando: o Chef vai criar uma nova proposta...")
            decision = ImpasseDecision(
                action="resume", expected_state_version=version, idempotency_key=key
            )
        elif choice == "a":
            print("\nAceito. Seguindo para Cozinheiro, Saúde, Imagem e finalização...")
            decision = ImpasseDecision(
                action="accept", expected_state_version=version, idempotency_key=key
            )
        elif choice == "c":
            decision = ImpasseDecision(
                action="cancel", expected_state_version=version, idempotency_key=key
            )
        else:
            print("Opção inválida. Digite só a, s, r ou c (para adicionar um ingrediente, escolha s).")
            continue

        try:
            result = session.submit_impasse_decision(thread_id, decision)
        except (ResumeLimitReached, StateVersionConflict) as exc:
            # Recusas esperadas: mostra o motivo e continua no Impasse.
            print(f"\n{exc}")
            result = session.get_state(thread_id)
        except Exception as exc:
            # Falha técnica no meio da decisão: volta ao Impasse em vez de travar.
            print(f"\nA tentativa falhou ({type(exc).__name__}: {exc}).")
            if not session.is_recoverable(thread_id):
                raise
            result = session.recover(thread_id)
            print("A criação voltou ao Impasse. Você pode tentar de novo, aceitar ou encerrar.")

    return result


def run_request(
    session: RecipeSession,
    raw_input: str,
    authorizations: dict[str, list[str] | None],
    *,
    debug: bool,
) -> None:
    thread_id = f"cli-{uuid4().hex[:8]}"
    state = create_initial_state(raw_input, thread_id)
    state.update(authorizations)

    print(f"\n[{thread_id}] criando receita...")
    result = session.start(state)
    result = handle_impasse(session, thread_id, result)

    if debug:
        print("\n--- estado bruto ---")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    if result.get("status") == "completed":
        print_final(result["final_response"])
        offer_to_open_image(result["final_response"])
    else:
        print(f"\nExecução encerrada com status: {result.get('status')}")
    print(
        f"\n[revisões={result.get('revision_count')} "
        f"tentativas={result.get('total_attempts')} id={thread_id}]"
    )


def show_history(session: RecipeSession) -> None:
    recipes = session.history.list_recipes()
    if not recipes:
        print("Nenhuma receita concluída nesta sessão.")
        return
    for recipe in recipes:
        print(f"  {recipe['id']}  {recipe['recipe']['title']}")


def show_recipe(session: RecipeSession, recipe_id: str) -> None:
    response = session.history.get_recipe(recipe_id)
    if response is None:
        print(f"Receita '{recipe_id}' não encontrada.")
        return
    print_final(response)


def install_impasse_demo() -> None:
    """Troca Chef e SubChef por versões fixas que sempre geram impasse.

    O Chef falso monta um recheio sem caloria e só usa um ingrediente novo se
    ele vier do Impasse. O SubChef falso rejeita enquanto o recheio não tiver
    um item adicionado pelo usuário. Cozinheiro, Saúde e Imagem seguem reais.
    """

    def demo_chef(state: dict[str, Any]) -> dict[str, object]:
        additions = list(state.get("ingredient_additions", []))
        guidance = state.get("user_guidance")
        filling_items = ["sapato velho", "cadarço", *additions]
        recipe = Recipe(
            dough="Massa de cimento com água de torneira, modelada como casca.",
            filling="Recheio de " + ", ".join(filling_items)
            + (f". Orientação do usuário: {guidance}" if guidance else "."),
            ingredients=["cimento", *filling_items],
            preparation="Misture o cimento, recheie e frite as bolinhas na panela.",
            utensils=["panela"],
            preparation_methods=["fritar"],
        )
        return {"recipe": recipe, "recipe_version": state["recipe_version"] + 1}

    def demo_subchef(state: dict[str, Any]) -> dict[str, object]:
        additions = state.get("ingredient_additions", [])
        if additions:
            return {
                "subchef_evaluation": SubChefEvaluation(
                    decision="approved",
                    critique="",
                    evidence=[f"O recheio agora inclui: {', '.join(additions)}."],
                )
            }
        return {
            "subchef_evaluation": SubChefEvaluation(
                decision="rejected",
                critique=(
                    "O recheio só tem sapato velho e cadarço, que não têm caloria. "
                    "Adicione pelo menos um item calórico ao recheio no Impasse "
                    "(por exemplo queijo, banana ou arroz)."
                ),
            )
        }

    graph_builder.chef_node = demo_chef
    graph_builder.subchef_node = demo_subchef


def main() -> None:
    parser = argparse.ArgumentParser(description="Loop de teste do Coxinh.IA.")
    parser.add_argument("--livre", action="store_true", help="não pergunta recursos autorizados")
    parser.add_argument("--debug", action="store_true", help="imprime o estado bruto")
    parser.add_argument(
        "--demo-impasse",
        action="store_true",
        help="usa Chef e SubChef falsos que sempre geram impasse (sem LLM)",
    )
    args = parser.parse_args()
    load_dotenv()  # antes de qualquer chamada: o LangSmith lê as variáveis na primeira execução

    if args.demo_impasse:
        install_impasse_demo()
        args.livre = True
        print("MODO DEMO: Chef e SubChef falsos. Qualquer pedido gera impasse.\n")
    session = build_session()  # PERSISTENCE=sqlite (padrão) guarda o histórico em data/
    print(__doc__)

    while True:
        line = read_line("\nO que vai na sua coxinha? > ")
        if line is None or line == "/sair":
            print("Até a próxima.")
            return
        if not line:
            continue
        if line == "/historico":
            show_history(session)
            continue
        if line.startswith("/ver"):
            show_recipe(session, line.removeprefix("/ver").strip())
            continue

        authorizations = (
            {
                "authorized_ingredients": None,
                "authorized_utensils": None,
                "authorized_preparation_methods": None,
            }
            if args.livre
            else ask_authorizations()
        )

        try:
            run_request(session, line, authorizations, debug=args.debug)
        except KeyboardInterrupt:
            print("\nExecução interrompida.")
        except Exception as exc:
            print(f"\nFalha na execução: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
