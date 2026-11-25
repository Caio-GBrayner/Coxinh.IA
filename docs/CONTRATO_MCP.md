# Contrato do servidor MCP (etapa 10)

**Situação:** rascunho para revisão. Nada aqui está implementado. Os pontos marcados como **A confirmar** dependem de decisão da dupla.

Complementa `docs/plano_execucao_coxinh_ia.md` (etapa 10 e seção 6). Em caso de divergência sobre escopo, o plano prevalece.

## 1. Princípios

* Os nós continuam sendo funções da aplicação, coordenadas pelo LangGraph. O MCP expõe ferramentas; ele não substitui nós nem recebe a mensagem inicial do usuário.
* O MCP não duplica regras de negócio. Cada ferramenta chama a função que já existe e acrescenta contrato de entrada, saída e erro.
* Os modelos Pydantic existentes (`Recipe`, `ImpasseDecision`, `ResourceValidationResult`) são reaproveitados, sem cópia paralela dos campos.
* Nenhum teste automatizado faz chamada de rede nem chamada paga.
* Segredos (chaves de API) vêm de variáveis de ambiente e nunca aparecem em respostas, logs ou testes.

## 2. Transporte e modo de execução

**Decidido:** FastMCP (camada sobre o SDK oficial `mcp`), com a versão fixada no `pyproject.toml`. O transporte entre os containers é streamable HTTP, na rede do Docker Compose. Isso substitui a decisão anterior de usar `stdio`, que não atravessa containers.

**Serviços do Compose**

| Serviço | Responsabilidade | Persistência |
| --- | --- | --- |
| `app` (serviço `api`) | API HTTP, grafo LangGraph, estado das conversas e decisões do Impasse. | SQLite (`data/coxinh.db` e `data/checkpoints.db`) no volume `coxinh-data`. |
| `mcp` | Ferramentas sem estado compartilhado: `validate_recipe_resources`, `generate_coxinha_image` e `search_web`. | Arquivos de imagem em `data/images`, no mesmo volume, nomeados pela chave de idempotência. |

Os dois serviços não compartilham arquivo SQLite; compartilham apenas a pasta de imagens, que a `api` serve em `/images`. A aplicação chama o `mcp` por HTTP, por exemplo em `http://mcp:8000/mcp`.

**Estado do Impasse.** O estado vive na aplicação (`InMemoryWorkflow`, em `src/graph/workflow.py`), e o plano proíbe criar uma segunda cópia dele no servidor. Por isso `record_impasse_decision` fica no processo da aplicação, que a expõe pela mesma interface de ferramenta, sem passar pelo container `mcp`. Registrar a ferramenta com `create_server(session=session)`, reutilizando a mesma `RecipeSession` da aplicação.

**Ordem de entrega.** Primeiro tudo em memória, como MVP. Depois, a persistência em SQLite como etapa própria (ver `docs/CONTEXTO_MIGRACAO_PERSISTENCIA.md`).

`mcp_server/server.py` expõe uma função `create_server(...)` que recebe as dependências (provedor de imagem, adaptador de busca e índice de imagens). Assim o mesmo código serve ao container e aos testes, que usam transporte em memória.

## 3. Convenção de resposta e de erro

* Sucesso: objeto JSON com os campos descritos em cada ferramenta.
* Erro: resposta marcada como erro pelo SDK, com corpo `{"error": {"code": "<código>", "message": "<texto>", "details": {...}}}`. O mecanismo exato de marcação é definido na implementação, conforme a versão do SDK.

Códigos de erro previstos:

| Código | Quando |
| --- | --- |
| `invalid_input` | Entrada reprovada pela validação do contrato. |
| `workflow_not_found` | Não existe conversa para o `thread_id`. |
| `input_blocked` | O guardrail recusou o texto da decisão. `details.guard_code` diz o motivo; nada foi registrado. |
| `workflow_not_paused` | A conversa não está aguardando decisão do Impasse. |
| `state_version_conflict` | `expected_state_version` diferente da versão atual. `details` traz `expected` e `current`. |
| `idempotency_key_reuse` | A mesma chave foi usada com uma decisão diferente. |
| `provider_unavailable` | Falha do provedor externo (imagem ou busca). |

## 4. Ferramentas

### 4.1 `validate_recipe_resources`

* **Objetivo:** comparar a receita com os ingredientes, utensílios e métodos autorizados.
* **Lógica:** `validate_recipe_resources` em `src/graph/resource_validation.py` (etapa 2).
* **Estado:** sem estado e idempotente.

**Entrada**

| Campo | Tipo | Observação |
| --- | --- | --- |
| `recipe` | `Recipe` | Receita completa. |
| `authorized_ingredients` | lista de textos ou `null` | `null` significa "não informado" e a categoria fica não verificada. Lista vazia significa "nenhum autorizado". |
| `authorized_utensils` | lista de textos ou `null` | Igual. |
| `authorized_preparation_methods` | lista de textos ou `null` | Igual. |
| `ingredient_additions` | lista de textos | Padrão `[]`. Autoriza e exige o ingrediente na receita. |

**Saída:** `ResourceValidationResult` — `status` (`passed`, `rejected` ou `incomplete`), `unauthorized_ingredients`, `unauthorized_utensils`, `unauthorized_preparation_methods`, `missing_ingredient_additions` e `unchecked_categories`.

**Erros:** `invalid_input` (receita inválida ou recurso vazio).

**Quem chama:** SubChef e Cozinheiro. **A confirmar:** hoje os dois nós chamam a função diretamente. Decidir se continuam assim (ferramenta disponível a outros clientes) ou passam a chamar pelo cliente MCP.

### 4.2 `record_impasse_decision`

* **Objetivo:** registrar a ação humana no Impasse.
* **Lógica:** `RecipeSession.submit_impasse_decision`, que delega ao workflow da etapa 6 e registra receitas concluídas no histórico da sessão.
* **Acionamento:** somente pela aplicação, a partir de uma ação humana identificada. **Nunca é oferecida ao modelo** como ferramenta, para que ele não invente uma autorização do usuário.

**Entrada**

| Campo | Tipo | Observação |
| --- | --- | --- |
| `thread_id` | texto | Identificador estável da conversa. |
| `action` | `save`, `resume`, `accept` ou `cancel` | `accept` segue a receita rejeitada para o Cozinheiro. |
| `expected_state_version` | inteiro ≥ 0 | Versão que o pedido esperava encontrar. |
| `idempotency_key` | texto não vazio | Repetir a mesma chave com o mesmo conteúdo devolve o resultado original. |
| `ingredient_additions` | lista de textos | Obrigatório em `save` se não houver `user_guidance`; proibido em `accept` e `cancel`. |
| `user_guidance` | texto ou `null` | Mesma regra. |

As regras de combinação vêm de `ImpasseDecision` e não são reescritas no servidor.

**Saída (projeção reduzida, sem o estado completo):** `thread_id`, `status`, `user_action`, `state_version`, `revision_count`, `total_attempts`, `recipe_version`.

**Erros:** `invalid_input`, `input_blocked`, `workflow_not_found`, `workflow_not_paused`, `state_version_conflict`, `idempotency_key_reuse`.

**Atenção:** com `resume`, a chamada continua o grafo (Chef, SubChef, Cozinheiro, Saúde) até concluir ou pausar de novo; com `accept`, segue direto para Cozinheiro, Saúde, Imagem e finalização. As duas podem demorar e chamar o LLM. O cliente deve ter um tempo limite adequado. `save` e `cancel` não chamam o LLM.

**Uso atual:** o caminho oficial do Impasse para o front é a API HTTP (`POST /recipes/{thread_id}/impasse`, ver `docs/CONTRATO_API.md`). Esta ferramenta continua disponível para testes e clientes MCP, mas usa uma `RecipeSession` própria quando registrada fora da API.

### 4.3 `generate_coxinha_image`

* **Objetivo:** gerar uma imagem fiel à receita final.
* **Provedor:** definido na decisão 12. Até lá, provedor simulado atrás de uma interface pequena.

**Entrada**

| Campo | Tipo | Observação |
| --- | --- | --- |
| `recipe` | `Recipe` | Receita final. |
| `image_prompt` | texto | Descrição visual produzida pelo Cozinheiro. |
| `prompt_version` | texto | Padrão `v1`. Muda quando o modelo do pedido muda. |

**Pedido ao provedor:** montado por um modelo de texto fixo que combina `image_prompt` com massa, recheio, ingredientes e métodos da receita (cores, texturas, formato e efeitos do preparo), e acrescenta que a imagem é ilustrativa, não uma fotografia de alimento real ou seguro.

**Chave de idempotência (proposta, a confirmar):** SHA-256 de um JSON canônico com `dough`, `filling`, `ingredients`, `preparation_methods`, `image_prompt`, `prompt_version` e o nome do provedor. Canonicalização: normalização Unicode (NFKC), espaços colapsados, caixa preservada nos textos livres e listas ordenadas. Título e subtítulo ficam fora da chave por não mudarem a imagem. Nenhum valor aleatório entra na chave.

**Saída:** `status` (`generated` ou `reused`), `image_reference` (URL ou referência de armazenamento, nunca o binário), `idempotency_key` e `provider_request_id` (ou `null`).

**Erros:** `invalid_input`, `provider_unavailable`. Uma falha do provedor não apaga a receita final: o chamador mantém `final_response` e marca o estado da imagem como falho.

**Armazenamento:** no MVP, dicionário em memória no processo do servidor `mcp`, por chave. Na etapa de persistência, o índice passa a um SQLite próprio do `mcp`, em volume próprio. Garantias e limites do MVP:

* Chamadas repetidas com a mesma chave no mesmo processo reutilizam o resultado.
* Chamadas simultâneas com a mesma chave são serializadas por chave, para gerar uma única vez.
* Se o processo reiniciar, ou se houver mais de um processo, o registro se perde e uma imagem nova pode ser gerada.
* Se o provedor responder e o processo falhar antes de gravar o resultado, a imagem pode ser gerada de novo. A chave sozinha não evita esse caso.

**Campos do estado já existentes:** `recipe_hash`, `idempotency_key`, `image_url`, `image_status`, `image_prompt`.

### 4.4 `search_web`

* **Depende da etapa 9.** Até a função real existir, o servidor usa um substituto com a mesma assinatura.
* **Provedor:** Tavily, plano gratuito (decisão 5).

**Entrada:** `query` (texto não vazio). O número de resultados é uma constante da função da etapa 9, não um parâmetro da ferramenta.

**Saída:** `status` (`ok` ou `no_results`) e `results`, lista de `{title, url, content}`. Ausência de resultado é `no_results` com lista vazia, e não é erro.

**Erros:** `invalid_input`, `provider_unavailable`. A diferença entre as duas situações segue a regra do nó de saúde: lista vazia leva a `insufficient`, falha leva a `unavailable`.

**A confirmar com o João:** a assinatura final da função da etapa 9. Proposta: `pesquisar_web(query: str) -> list[dict[str, str]]`.

**Quem chama:** o nó de saúde, depois do Cozinheiro (decisão 4). O conteúdo retornado é dado, nunca instrução ao modelo.

### 4.5 `search_knowledge`

* **Adiada:** a base RAG está fora do escopo (decisão 10). Esta ferramenta não é implementada por ora, e o servidor expõe quatro ferramentas. Se o RAG voltar, o contrato abaixo serve de ponto de partida.

**Entrada (proposta):** `query` e `top_k`. **Saída (proposta):** lista de `{title, source, section, content}`, com `source` sendo URL ou identificador do documento.

**Erros:** `invalid_input`, `provider_unavailable`.

## 5. Quem chama o quê

| Ferramenta | Chamada por | Exposta ao modelo? |
| --- | --- | --- |
| `validate_recipe_resources` | SubChef e Cozinheiro | Não precisa; é regra determinística. |
| `record_impasse_decision` | Aplicação, após ação humana | **Não.** |
| `generate_coxinha_image` | Fluxo, depois da receita final | Não; recebe dados já consolidados. |
| `search_web` | Nó de saúde | Não; o nó monta a consulta. |
| `search_knowledge` | Adiada (RAG fora do escopo) | Não. |

**Decidido:** a imagem é gerada por um nó `image`, entre o aviso de saúde e a finalização: `cook → health → image → finalize`. Falha de imagem não bloqueia a receita: o nó registra o estado da imagem como falho e o fluxo segue. Não há nó `format_output` separado; o `finalize` continua montando a resposta final.

## 6. Testes previstos

* Listagem: o servidor expõe as cinco ferramentas, com nomes e esquemas esperados.
* Cada ferramenta: caminho de sucesso e cada código de erro da seção 3 que se aplique.
* `record_impasse_decision`: versão desatualizada, chave repetida com mesmo conteúdo, chave repetida com conteúdo diferente, conversa inexistente e conversa não pausada.
* Imagem: chave estável para a mesma entrada, chave diferente quando a receita muda, reutilização do resultado, falha do provedor sem perda da receita e nenhuma chamada paga.
* Busca: lista vazia (`no_results`) distinta de falha (`provider_unavailable`), com substituto no lugar da API.
* Cliente: chamada de ponta a ponta por transporte em memória, sem processo externo.

## 7. Ordem de implementação

1. Aprovar este contrato.
2. Fixar a versão do FastMCP em `pyproject.toml` e criar o esqueleto de `create_server(...)` com as ferramentas registradas.
3. `validate_recipe_resources` e `record_impasse_decision`, com testes.
4. `generate_coxinha_image` com provedor simulado e armazenamento em memória.
5. Cliente MCP na aplicação e teste de ponta a ponta.
6. `search_web` ligada à função real, depois que a etapa 9 for aprovada.
7. Nó `image` no grafo, chamando `generate_coxinha_image`, e Docker Compose com `app` e `mcp`.
8. Persistência em SQLite, em etapa própria.

## 8. Pendências

| Pendência | Responsável | Bloqueia |
| --- | --- | --- |
| Confirmar que `record_impasse_decision` fica no processo da aplicação (seção 2) | Dupla | Ferramenta `record_impasse_decision` |
| Assinatura de `pesquisar_web` | João (etapa 9) | Ligação de `search_web` |
| Retomar o RAG, hoje adiado (decisão 10) | Dupla | `search_knowledge` |
| Provedor de imagem (decisão 12) | Dupla | Provedor real |
| Cliente guarda só o `thread_id` no navegador (decisão 20, a confirmar) | Dupla | Interface (etapa 11) |
| SubChef e Cozinheiro chamam a validação por MCP? | Dupla | Integração da validação |
| Armazenamento durável | Dupla | Fora do MVP |
