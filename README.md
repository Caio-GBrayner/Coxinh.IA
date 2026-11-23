# Coxinh.IA

<p align="center">
  <img src="./docs/design/Coxinh.IA%20%20logo%20nome.png" alt="Marca Coxinh.IA" width="520">
</p>

**O melhor harness de IA para as coxinhas mais sem sentido que você possa imaginar.**

O Coxinh.IA transforma ingredientes e ideias improváveis em receitas de coxinha. É um projeto de humor e sátira criado para estudar fluxos com agentes de IA: a receita pode ser absurda, mas o sistema precisa mostrar como chegou ao resultado e apresentar o aconselhamento de consumo com suas fontes e incertezas.

**Estado atual:** fluxo Python, API FastAPI oficial e interface React. A integra??o da interface ao contrato ass?ncrono est? em andamento. Persist?ncia SQLite, imagem via OpenRouter (ou simula??o sem chave) e observabilidade est?o dispon?veis no backend.

## Como a receita é criada

1. **Chef:** propõe uma receita estruturada a partir da entrada da pessoa.
2. **SubChef:** revisa a proposta. Se precisar de mudanças, o Chef tenta novamente, com no máximo duas revisões.
3. **Impasse:** quando a revisão não consegue avançar, pausa a execução para a pessoa adicionar orientações ou ingredientes, salvar, retomar ou encerrar. A retomada volta ao Chef e ao SubChef.
4. **Cozinheiro:** transforma a receita aprovada em título, subtítulo, passos e descrição visual, sem trocar recursos por conta própria.
5. **Saúde:** pesquisa massa, recheio e preparo na web e produz um aconselhamento informativo, com fontes e incerteza quando cabível. Não altera a receita nem decide se ela pode ser consumida.
6. **Imagem:** chama a ferramenta MCP de geração. Nesta versão, o provedor é simulado e devolve uma referência `simulated://`. Uma falha de imagem não impede a finalização.
7. **Finalização:** reúne receita, aconselhamento e estado da imagem em `final_response`.

O fluxo está montado em [`src/graph/builder.py`](./src/graph/builder.py). [`RecipeSession`](./src/recipe_session.py) coordena cada execução e guarda as receitas concluídas em um histórico em memória. Um novo pedido precisa de um novo `thread_id`; uma decisão de Impasse usa o identificador da execução pausada.

## Instalar e testar

Requer Python 3.11 ou superior. Os comandos abaixo são para PowerShell, executados na raiz do repositório:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
```

O primeiro comando cria o ambiente virtual, o segundo o ativa, o terceiro instala o projeto e as dependências de desenvolvimento, e o último executa os testes. Em Linux ou macOS, use `python3 -m venv .venv` e `source .venv/bin/activate` no lugar dos dois primeiros comandos.

Os testes usam modelos e pesquisas simulados: não exigem chaves e não devem fazer chamadas externas.

## Configurar uma execução real

Copie [`.env.example`](./.env.example) para um arquivo `.env` **na raiz do projeto**. Preencha `LLM_KEY` e `LLM_MODEL` com uma chave e um modelo compatíveis com a integração Groq. Preencha `TAVILY_API_KEY` para a pesquisa do agente de saúde. Não envie o `.env` ao Git.

`MCP_SERVER_URL` pode ficar vazio para usar as ferramentas MCP no mesmo processo. Para conectar a um servidor HTTP separado, informe uma URL como `http://127.0.0.1:8000/mcp` e execute `python -m mcp_server.server` em outro terminal. O servidor padrão oferece validação de recursos e **imagem simulada**; a ferramenta de busca web do MCP só é registrada quando uma função de busca é fornecida explicitamente. O nó de saúde consulta Tavily diretamente.

Com o ambiente configurado, a API Python da versão atual pode ser experimentada em um terminal interativo:

```python
from src.recipe_session import RecipeSession
from src.state import create_initial_state

session = RecipeSession()
state = create_initial_state("Coxinha de maçã com ração", "receita-1")
result = session.start(state)
print(result["status"])
print(result.get("final_response"))
```

`create_initial_state` monta a entrada e define o limite inicial de duas revisões. `session.start` executa o grafo até concluir ou aguardar uma decisão no Impasse. `result` contém o estado atual; `final_response` só aparece ao concluir. Consulte `session.get_state("receita-1")` para ler essa execução e `session.history.list_recipes()` para listar receitas concluídas na mesma instância. O fluxo pode chamar provedores externos e consumir cotas gratuitas conforme sua configuração.

## Executar a interface web

Na raiz do projeto, com as dependências Python instaladas e o `.env` configurado:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8080
```

Em outro terminal PowerShell, a partir da raiz (Node.js 24 foi usado na validação):

```powershell
Set-Location -LiteralPath .\frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

Abra o endereço impresso pelo Vite, normalmente `http://127.0.0.1:5173`. O proxy `/api` aponta para `127.0.0.1:8080`. Use `npm.cmd` para evitar o bloqueio de `npm.ps1` pela política de execução do PowerShell. Chaves ficam somente no backend. A API web e o MCP HTTP separado não podem ocupar a mesma porta; o MCP no mesmo processo não exige outro servidor.

Validação, a partir da raiz:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
Set-Location -LiteralPath .\frontend
npm.cmd run build
npm.cmd run lint
npm.cmd test
```

Os testes de navegador usam Microsoft Edge instalado, Vite em `5174` e a API real em `8001`, com agentes externos simulados por `tests/browser_api.py`. Nenhuma chamada paga é feita. `npm.cmd run test:visual` refaz as capturas de 1440, 1024, 768 e 390 pixels em `docs/design/review/`. Para Chrome instalado, defina `$env:PLAYWRIGHT_CHANNEL = "chrome"`. Feche serviços de teste anteriores nessas portas antes de iniciar a suíte.

O [relatório da etapa 11](docs/design/review/etapa-11.md) reúne evidências, arquivos alterados e limites. Os textos fixos estão em `frontend/src/content.ts`; receitas, saúde e imagens vêm da API.

## Rodar a API e a persistência

A API HTTP é a porta de entrada do front. Por padrão (`PERSISTENCE=sqlite`), receitas, impasses em aberto e checkpoints ficam em `data/` e sobrevivem a reinícios.

```bash
uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8080
```

O contrato está em [`docs/CONTRATO_API.md`](./docs/CONTRATO_API.md) e, com a API rodando, em `http://127.0.0.1:8080/docs`. Para subir API e servidor MCP juntos, com volume persistente: `docker compose up --build`. Para testar o fluxo pelo terminal: `python -m src.app.main --livre` (ou `--demo-impasse`, sem LLM no Chef e no SubChef).


## Estrutura principal

| Caminho | Função |
| --- | --- |
| `src/schemas.py`, `src/state.py` | Contratos da receita e estado compartilhado do grafo. |
| `src/graph/nodes/`, `src/graph/builder.py` | Agentes, geração da imagem e rotas do fluxo. |
| `src/graph/workflow.py`, `src/recipe_session.py` | Checkpoint, retomada do Impasse e histórico da sessão. |
| `src/utils/web_search.py` | Adaptador de pesquisa Tavily usado pelo agente de saúde. |
| `mcp_server/` | Ferramentas de validação, imagem simulada e interfaces opcionais de busca e Impasse. |
| `tests/` | Verificações automatizadas, sem necessidade de chamadas pagas. |
| `docs/design/design.md` | Especificação visual da futura interface. |
| `docs/plano_execucao_coxinh_ia.md` | Etapas, responsabilidades e critérios de conclusão. |

## Limites da versão atual

O histórico e os checkpoints vivem em memória: são preservados enquanto a mesma instância da aplicação estiver ativa e desaparecem quando o processo termina. Ainda não existe banco de dados nem persistência entre reinícios. A interface guarda apenas o ID ativo e a posição do carrossel na aba, consultando a API ao recarregar. O provedor real de imagens e Langfuse não estão integrados.

Uma falha de rede após `POST /api/recipes` pode deixar uma execução aceita sem o ID ter chegado ao navegador: o contrato atual só entrega o ID ao retornar. A interface consulta o histórico e não repete o POST automaticamente, mas não consegue recuperar uma execução pausada cujo ID nunca recebeu. Isso exige evolução futura do contrato de criação. No Impasse, o ID já conhecido permite consultar o estado após falha ou conflito.

A API roda em um único processo: vários processos sobre o mesmo banco SQLite não são suportados. Uma geração interrompida por queda vira `interrupted` e precisa ser refeita; impasses em aberto sobrevivem. A interface web está em construção. A imagem real depende de `OPENROUTER_API_KEY`; sem ela, o provedor simulado é usado e nenhuma imagem aparece no site.


O parecer de saúde é informativo. Trechos encontrados na web exigem interpretação cuidadosa e não tornam uma receita segura para consumo. A presença de uma URL indica a origem do trecho utilizado, sem certificar a qualidade da fonte.

## Projeto

Desenvolvido por João Santos e Caio Brayner para praticar engenharia de IA durante o bootcamp da Deloitte. A ideia nasceu de uma piada da turma sobre a coxinha da padaria do Moinho e da brincadeira da dupla de transformar qualquer ideia em um sistema de IA. A identidade e as telas planejadas estão em [`docs/design/design.md`](./docs/design/design.md).
