# Coxinh.IA

<p align="center">
  <img src="./docs/design/Coxinh.IA%20%20logo%20nome.png" alt="Marca Coxinh.IA" width="520">
</p>

**O melhor harness de IA para as coxinhas mais sem sentido que você possa imaginar.**

O Coxinh.IA transforma ingredientes e ideias improváveis em receitas de coxinha. É um projeto de humor e sátira criado para estudar fluxos com agentes de IA: a receita pode ser absurda, mas o sistema precisa mostrar como chegou ao resultado e apresentar o aconselhamento de consumo com suas fontes e incertezas.

**Estado atual:** API oficial em `src/api/app.py`, interface React com polling e carrossel global, persistência SQLite e imagens via OpenRouter (ou simulação sem chave).

## Como a receita é criada

1. **Chef:** propõe uma receita estruturada a partir da entrada da pessoa.
2. **SubChef:** revisa a proposta. Se precisar de mudanças, o Chef tenta novamente, com no máximo duas revisões.
3. **Impasse:** quando a revisão não consegue avançar, pausa a execução para a pessoa adicionar orientações ou ingredientes, salvar, retomar, aceitar como está ou encerrar. A retomada volta ao Chef e ao SubChef; aceitar segue ao Cozinheiro com a proposta atual.
4. **Cozinheiro:** transforma a receita aprovada em título, subtítulo, passos e descrição visual, sem trocar recursos por conta própria.
5. **Saúde:** pesquisa massa, recheio e preparo na web e produz um aconselhamento informativo, com fontes e incerteza quando cabível. Não altera a receita nem decide se ela pode ser consumida.
6. **Imagem:** chama a ferramenta MCP de geração. Sem chave OpenRouter, o provedor simulado devolve uma referência `simulated://`. Uma falha de imagem não impede a finalização.
7. **Finalização:** reúne receita, aconselhamento e estado da imagem em `final_response`.

O fluxo está montado em [`src/graph/builder.py`](./src/graph/builder.py). [`RecipeSession`](./src/recipe_session.py) coordena cada execução e guarda receitas no armazenamento configurado (SQLite na API por padrão). Um novo pedido precisa de um novo `thread_id`; uma decisão de Impasse usa o identificador da execução pausada.

## Início rápido com Docker

O jeito mais simples de rodar o projeto completo. O Docker Compose sobe três serviços:

| Serviço | Endereço | Função |
| --- | --- | --- |
| `front` | `http://127.0.0.1:3000` | Interface React servida pelo nginx. Repassa `/api` para a `api`. |
| `api` | `http://127.0.0.1:8080` (documentação em `/docs`) | FastAPI com os agentes (Chef, SubChef, Cozinheiro, Saúde, Imagem) e a persistência em SQLite. |
| `mcp` | só na rede interna (`mcp:8000`) | Ferramentas de validação e geração de imagem. |

Os bancos SQLite e as imagens ficam no volume `coxinh-data`: derrubar e subir os containers não apaga receitas nem impasses em aberto.

**1. Configure o `.env`.** Copie [`.env.example`](./.env.example) para `.env` na raiz e preencha:

| Variável | Obrigatória | Uso |
| --- | --- | --- |
| `LLM_PROVIDER`, `LLM_MODEL` | Sim | `google` ou `groq` (padrão `groq`), e o modelo do provedor, por exemplo `gemini-3.5-flash-lite` ou `openai/gpt-oss-120b`. Modelos menores falham com mais frequência ao gerar a saída estruturada. |
| `GOOGLE_API_KEY` ou `LLM_KEY` | Sim | A chave do provedor escolhido: `GOOGLE_API_KEY` para `google`, `LLM_KEY` para `groq`. |
| `TAVILY_API_KEY` | Recomendada | Pesquisa do agente de saúde. Sem ela, o aconselhamento fica `unavailable`. |
| `OPENROUTER_API_KEY` | Opcional | Imagem real. Sem ela, a imagem é simulada e não aparece no site. |
| `LANGFUSE_*`, `LANGSMITH_*` | Opcional | Rastreamento. O host do Langfuse precisa ser o da região das chaves. |

As variáveis de banco, MCP e imagens já vêm definidas no `compose.yaml`; não é preciso alterá-las para rodar no Docker.

**2. Suba tudo:**

```bash
docker compose up --build -d
docker compose ps
```

Abra `http://127.0.0.1:3000`. Criar uma receita chama o LLM e as demais APIs configuradas, e pode consumir cota ou gerar custo.

**Comandos do dia a dia:**

```bash
docker compose up -d                 # sobe sem reconstruir
docker compose up --build -d api     # reconstrói e sobe um serviço (api, mcp ou front)
docker compose logs -f api           # acompanha os logs de um serviço
docker compose down                  # derruba os containers e mantém os dados
docker compose down && docker compose up -d   # aplica mudanças no .env
```

- **Mudou o `.env`?** Use `down` e `up -d`. O `docker compose restart` reinicia os containers sem reler o `.env`.
- **`build` não sobe nada:** `docker compose build` só gera as imagens. Quem cria e liga os containers é o `up`.
- **`docker compose down -v` apaga o volume** com todas as receitas, impasses e imagens. Use apenas para começar do zero.
- **Teste de queda:** `docker compose kill api` seguido de `docker compose up -d api`. Um impasse em aberto continua disponível depois.
- **Portas ocupadas:** 3000 e 8080 precisam estar livres no host.

## Exemplo de fluxo

```mermaid
flowchart TD
    P[Pedido] --> C[Chef]
    C --> S[SubChef]
    S -->|aprovada| K[Cozinheiro]
    S -->|rejeitada, ainda há revisões| C
    S -->|rejeitada, sem revisões| I{Impasse}
    I -->|save: guarda ajustes| I
    I -->|resume: tenta de novo| C
    I -->|accept: aceita como está| K
    I -->|cancel| X[Encerrada]
    K --> H[Saúde] --> M[Imagem] --> F[Finalização]
```

Uma execução que passa pelo Impasse (exemplo ilustrativo; o conteúdo varia a cada execução porque os agentes usam um modelo de linguagem):

| Passo | O que acontece | `status` | `state_version` |
| --- | --- | --- | --- |
| 1 | Pedido: "Tenho um sapato velho, um cadarço, meio saco de cimento e um cabo USB. Quero fritar na panela." | `running` | 0 |
| 2 | O Chef propõe massa de cimento e recheio de sapato e cadarço. | `running` | 0 |
| 3 | O SubChef rejeita: o recheio não tem nenhum ingrediente com caloria. O Chef tenta de novo e é rejeitado outra vez (2 de 2 revisões). | `awaiting_user` | 0 |
| 4 | Impasse. A pessoa envia `save` com `queijo e carne`. Nada roda, a conversa continua pausada. | `awaiting_user` | 1 |
| 5 | A pessoa envia `resume`. O Chef usa o queijo e a carne no recheio e o SubChef aprova. | `running` | 2 |
| 6 | Cozinheiro (título, subtítulo, passos), Saúde (aviso com fontes), Imagem e Finalização. | `completed` | 2 |

Em qualquer ponto do passo 4, `accept` leva direto ao Cozinheiro com a proposta rejeitada, e `cancel` encerra sem receita.

## Testar o Impasse e a aplicação

O Impasse é a parte que depende de uma decisão humana e a mais difícil de provocar de propósito. Os modelos de linguagem variam entre execuções: se um pedido não cair no Impasse, rode de novo.

### Pedidos para experimentar

| Pedido | O que esperar |
| --- | --- |
| `Tenho frango, queijo e mandioca. Quero fritar na panela.` | Normalmente aprovado sem Impasse, com receita, aviso de saúde e imagem. |
| `Tenho um sapato velho, um cadarço, meio saco de cimento e um cabo USB. Quero fritar na panela.` | Cai no Impasse: o recheio não tem ingrediente com caloria. |
| `Tenho uma pastilha de urânio, um tijolo e uma bateria. Quero assar no forno.` | Pode virar receita fictícia, cair no Impasse ou, mais raramente, ser recusado pelo modelo. Nesse último caso o sistema repete a chamada até 3 vezes (Groq) e, se falhar, mostra o erro sem travar. |
| Pedido vazio ou só com espaços | A tela pede uma ideia; a API responde 422. |
| Pedido com mais de 4000 caracteres | A API responde 422. |

### Ingredientes no Impasse

O campo "Adicionar ingrediente" aceita texto livre. Vírgula, `;`, quebra de linha, "e" e marcadores de lista separam os itens.

| Digite | Resultado |
| --- | --- |
| `queijo, carne e fogão` | Três itens: `queijo`, `carne`, `fogão`. |
| `- queijo`, `* carne moída` e `2. massa de mandioca` em linhas separadas | Três itens, sem os marcadores. |
| `PÃO francês; Manteiga` | Dois itens. A comparação ignora acento e maiúsculas, então `pão francês` na receita conta. |
| ` , ; ` | Recusado: "Informe pelo menos um ingrediente ou uma orientação." Nada quebra. |
| `trufa` (a receita não usa) | Volta ao Impasse com o motivo em português: "Itens adicionados no Impasse que a receita ainda não usa: trufa." |
| `fogão` | Conta mesmo que a receita o use só como utensílio. |

### O que verificar

- **Aceitar sempre funciona:** `accept` conclui a receita mesmo com itens salvos que ela não usa.
- **Limite de retomadas:** depois de 4 ciclos de revisão, `resume` é recusado (409 `resume_limit_reached`) e o botão "Continuar criação" fica desativado. Salvar, aceitar e cancelar continuam disponíveis.
- **Falha no meio:** se uma retomada falhar por erro técnico (por exemplo, limite de uso do modelo), a tela volta ao Impasse com um aviso e a próxima decisão funciona.
- **Queda do servidor:** derrube a API no meio de um Impasse (`docker compose kill api`), suba de novo (`docker compose up -d api`) e confirme que o Impasse continua disponível.

### Impasse sem modelo de linguagem

Para exercitar as quatro ações sem custo e de forma repetível, use o modo de demonstração no terminal. O Chef e o SubChef são substituídos por versões fixas que sempre geram Impasse:

```bash
python -m src.app.main --demo-impasse
```

No Impasse, `a` aceita, `s` salva ingredientes e orientação, `r` retoma e `c` cancela.

### Testes automáticos

```bash
python -m pytest -q                                  # toda a suíte, sem chamadas externas
python -m pytest -q tests/test_impasse_recovery.py   # texto livre, falhas e limite de retomadas
python -m pytest -q tests/test_crash_recovery.py     # derruba a API com SIGKILL no meio do Impasse
```

### Decidir o Impasse pela API

```bash
curl -X POST http://127.0.0.1:8080/recipes/<thread_id>/impasse \
  -H 'Content-Type: application/json' \
  -d '{"action": "save", "expected_state_version": 0, "idempotency_key": "salvar-1", "ingredient_additions": "queijo, carne e fogão"}'
```

Use o `state_version` atual de `GET /recipes/<thread_id>` e uma `idempotency_key` nova a cada decisão. O contrato completo está em [`docs/CONTRATO_API.md`](./docs/CONTRATO_API.md).

## Testar no LangGraph Studio com LangSmith

O Studio mostra cada nó do grafo, o estado em cada passo e permite retomar o Impasse à mão. Ele usa o grafo de [`src/graph/studio.py`](./src/graph/studio.py), registrado em [`langgraph.json`](./langgraph.json), com a mesma lógica da aplicação e uma entrada reduzida.

```bash
python -m pip install "langgraph-cli[inmem]"
langgraph dev --no-browser --no-reload --port 2024
```

O endereço do Studio aparece no log do servidor. Para ver os rastros no LangSmith, defina no `.env` `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY` e `LANGSMITH_PROJECT`. Use `--no-reload`: sem ele, o servidor reinicia sem parar por causa dos arquivos do ambiente virtual. O Studio guarda as execuções localmente, na pasta `.langgraph_api/` (ignorada pelo Git), e não no SQLite da aplicação.

**1. Entrada.** Cole este JSON como entrada do grafo `coxinha`:

```json
{
  "raw_input": "Tenho um sapato velho, um cadarço, meio saco de cimento e um cabo USB. Quero fritar na panela.",
  "thread_id": "teste-1"
}
```

**2. Impasse.** Quando o fluxo pausar, o Studio mostra uma interrupção com a receita, a crítica e o `state_version`. O Studio só aceita JSON válido como resposta: texto solto como `aceitar` gera `JSON.parse: unexpected non-whitespace character`. Cada decisão tem estes campos:

| Campo | Regra |
| --- | --- |
| `action` | `save`, `resume`, `accept` ou `cancel`. |
| `expected_state_version` | O `state_version` mostrado na interrupção. Em um Impasse novo é `0`. |
| `idempotency_key` | Obrigatório: qualquer texto não vazio. Use um valor diferente a cada decisão. No Studio a chave não é conferida; na API, reutilizá-la com outro conteúdo é rejeitado. |
| `ingredient_additions` | Texto livre ou lista. Só para `save` e `resume`. |
| `user_guidance` | Texto livre. Só para `save` e `resume`. |

Salvar ingredientes e orientação (continua pausado; o `state_version` sobe para `1`):

```json
{
  "action": "save",
  "expected_state_version": 0,
  "idempotency_key": "salvar-1",
  "ingredient_additions": "queijo, carne e fogão",
  "user_guidance": "Use o queijo e a carne como recheio."
}
```

Retomar, para o Chef tentar de novo com o que foi salvo. Use o `state_version` novo:

```json
{
  "action": "resume",
  "expected_state_version": 1,
  "idempotency_key": "retomar-1"
}
```

Aceitar a proposta como está, seguindo para Cozinheiro, Saúde, Imagem e finalização:

```json
{
  "action": "accept",
  "expected_state_version": 0,
  "idempotency_key": "aceitar-1"
}
```

Encerrar sem receita:

```json
{
  "action": "cancel",
  "expected_state_version": 0,
  "idempotency_key": "cancelar-1"
}
```

`accept` e `cancel` não aceitam `ingredient_additions` nem `user_guidance`. Se o Studio responder `State version conflict: expected 0, current version is 1`, a decisão anterior já foi aplicada: use o `state_version` mostrado agora.

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

`MCP_SERVER_URL` pode ficar vazio para usar as ferramentas MCP no mesmo processo. Para conectar a um servidor HTTP separado, informe uma URL como `http://127.0.0.1:8000/mcp` e execute `python -m mcp_server.server` em outro terminal. O servidor padrão oferece validação de recursos e imagens via OpenRouter ou simuladas sem chave; a ferramenta de busca web do MCP só é registrada quando uma função de busca é fornecida explicitamente. O nó de saúde consulta Tavily diretamente.

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
.\.venv\Scripts\python.exe -m uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8081
```

Em outro terminal PowerShell, a partir da raiz (Node.js 24 foi usado na validação):

```powershell
Set-Location -LiteralPath .\frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

Abra o endereço impresso pelo Vite, normalmente `http://127.0.0.1:5173`. O proxy `/api` remove esse prefixo e aponta para `127.0.0.1:8081`. Para outro host, configure `VITE_API_URL` antes do build e `CORS_ORIGINS` no backend. Use `npm.cmd` para evitar o bloqueio de `npm.ps1` pela política de execução do PowerShell. Chaves ficam somente no backend. A API web e o MCP HTTP separado não podem ocupar a mesma porta; o MCP no mesmo processo não exige outro servidor.

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
uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8081
```

O contrato está em [`docs/CONTRATO_API.md`](./docs/CONTRATO_API.md) e, com a API rodando, em `http://127.0.0.1:8081/docs`. Para subir front, API e MCP juntos, veja [Início rápido com Docker](#início-rápido-com-docker) ou execute `docker compose up --build` para iniciar os serviços com volume persistente. Para testar o fluxo pelo terminal: `python -m src.app.main --livre` (ou `--demo-impasse`, sem LLM no Chef e no SubChef).


## Estrutura principal

| Caminho | Função |
| --- | --- |
| `src/schemas.py`, `src/state.py` | Contratos da receita e estado compartilhado do grafo. |
| `src/graph/nodes/`, `src/graph/builder.py` | Agentes, geração da imagem e rotas do fluxo. |
| `src/graph/workflow.py`, `src/recipe_session.py` | Checkpoint, retomada do Impasse e carrossel global. |
| `src/api/app.py` | API HTTP (FastAPI) usada pelo front. |
| `src/persistence/` | SQLite para receitas, decisões do Impasse e checkpoints. |
| `src/utils/web_search.py` | Adaptador de pesquisa Tavily usado pelo agente de saúde. |
| `mcp_server/` | Ferramentas de validação, imagem (OpenRouter ou simulada) e interfaces opcionais de busca e Impasse. |
| `frontend/` | Interface React (Vite), com `Dockerfile` e `nginx.conf` para o compose. |
| `compose.yaml`, `Dockerfile` | Serviços `front`, `api` e `mcp` e o volume de dados. |
| `tests/` | Verificações automatizadas, sem necessidade de chamadas pagas. |
| `docs/design/design.md` | Especificação visual da interface. |
| `docs/plano_execucao_coxinh_ia.md` | Etapas, responsabilidades e critérios de conclusão. |

## Limites da versão atual

A interface guarda o ID ativo e a posição do carrossel na aba. O carrossel é global e a API usa SQLite por padrão.

Uma falha de rede após `POST /recipes` pode deixar uma execução aceita sem o ID ter chegado ao navegador: a resposta 202 pode se perder antes de entregar o ID. A interface consulta o histórico e não repete o POST automaticamente, mas não consegue recuperar uma execução pausada cujo ID nunca recebeu. Isso exige evolução futura do contrato de criação. No Impasse, o ID já conhecido permite consultar o estado após falha ou conflito.

A API roda em um único processo: vários processos sobre o mesmo banco SQLite não são suportados. Uma geração interrompida por queda vira `interrupted` e precisa ser refeita; impasses em aberto sobrevivem. A imagem real depende de `OPENROUTER_API_KEY`; sem ela, o provedor simulado é usado e nenhuma imagem aparece no site.


O parecer de saúde é informativo. Trechos encontrados na web exigem interpretação cuidadosa e não tornam uma receita segura para consumo. A presença de uma URL indica a origem do trecho utilizado, sem certificar a qualidade da fonte.

## Projeto

Desenvolvido por João Santos e Caio Brayner para praticar engenharia de IA durante o bootcamp da Deloitte. A ideia nasceu de uma piada da turma sobre a coxinha da padaria do Moinho e da brincadeira da dupla de transformar qualquer ideia em um sistema de IA. A identidade e as telas planejadas estão em [`docs/design/design.md`](./docs/design/design.md).
