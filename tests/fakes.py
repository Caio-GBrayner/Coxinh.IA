"""Agentes falsos, sem LLM nem rede, usados pelos testes de persistência e da API.

O Chef monta um recheio de batata e só acrescenta o que vier do Impasse. O
SubChef rejeita até existir um ingrediente adicionado pelo usuário, então todo
pedido chega ao Impasse depois de duas revisões.
"""

from src.schemas import CookOutput, Recipe, SubChefEvaluation


def fake_chef(state, calls=None):
    if calls is not None:
        calls["chef"] += 1
    ingredients = ["batata", *state.get("ingredient_additions", [])]
    return {
        "recipe": Recipe(
            dough="massa de batata",
            filling="recheio de " + ", ".join(ingredients),
            ingredients=ingredients,
            preparation="Cozinhe e modele.",
            utensils=["panela"],
            preparation_methods=["cozinhar"],
        ),
        "recipe_version": state["recipe_version"] + 1,
    }


def fake_subchef(state, calls=None):
    if calls is not None:
        calls["subchef"] += 1
    approved = bool(state.get("ingredient_additions"))
    return {
        "subchef_evaluation": SubChefEvaluation(
            decision="approved" if approved else "rejected",
            critique="" if approved else "Falta um item calórico no recheio.",
        )
    }


def fake_cook(state):
    recipe = Recipe.model_validate(state["recipe"])
    output = CookOutput(
        title="Coxinha de teste",
        subtitle="Feita sem LLM.",
        steps=["Cozinhe.", "Modele."],
        image_prompt="Fotografia de uma coxinha.",
        ingredients=recipe.ingredients,
        utensils=recipe.utensils,
        preparation_methods=recipe.preparation_methods,
    )
    return {
        "cook_output": output.model_dump(mode="json"),
        "recipe_steps": "1. Cozinhe.\n2. Modele.",
        "image_prompt": output.image_prompt,
        "cook_resource_validation": "incomplete",
    }


def fake_health(state):
    return {
        "health_status": "ok",
        "health_warning": "Receita fictícia.",
        "health_contraindications": [],
        "health_sources": [],
        "health_uncertainty": None,
    }


def fake_image(state):
    return {"image_url": None, "image_status": "failed"}


def install_fake_agents(monkeypatch):
    """Troca Chef e SubChef (para testes com monkeypatch) e conta as chamadas."""
    from src.graph import builder as graph_module

    calls = {"chef": 0, "subchef": 0}
    monkeypatch.setattr(graph_module, "chef_node", lambda state: fake_chef(state, calls))
    monkeypatch.setattr(graph_module, "subchef_node", lambda state: fake_subchef(state, calls))
    return calls


def install_offline_agents(graph_module):
    """Troca todos os nós que usam LLM, rede ou MCP (servidor do teste de queda)."""
    graph_module.chef_node = fake_chef
    graph_module.subchef_node = fake_subchef
    graph_module.cook_node = fake_cook
    graph_module.health_node = fake_health
    graph_module.image_node = fake_image
