# Plano de execução do Coxinh.IA multiagente

Este plano divide a implementação entre duas pessoas e estabelece revisão obrigatória em todas as etapas. As atividades seguem a arquitetura do projeto e devem ser concluídas incrementalmente: cada etapa precisa funcionar e ser revisada antes de começar a seguinte.

## 1. Papéis e regra de alternância

* **Pessoa A = Caio** e **Pessoa B = João** para as etapas restantes. O histórico das etapas anteriores permanece registrado nos respectivos PRs.
* **Code** implementa a atividade, adiciona ou atualiza testes e abre um pull request (PR).
* **Reviewer** revisa o PR, executa as verificações pertinentes e aprova ou solicita alterações.
* Quem implementou uma mudança não pode aprovar o próprio trabalho.
* A cada etapa, os papéis se invertem. A pessoa que foi Reviewer passa a ser Code na etapa seguinte.
* Se o Reviewer solicitar alterações, Code as implementa e o mesmo Reviewer confere novamente. A etapa só termina com aprovação.
* Não começar uma etapa que dependa de uma anterior ainda não aprovada.
* A regra vale para **todo o projeto**, inclusive documentação técnica, correções, refatorações e integrações futuras. Para uma correção urgente, a revisão continua obrigatória; reduzam o escopo do PR, não eliminem a revisão.

## 2. Como trabalhar em cada etapa

1. Code confirma o escopo e os critérios de conclusão da etapa.
2. Code cria uma branch curta, implementa somente esse escopo, adiciona testes e atualiza a documentação diretamente relacionada.
3. Code executa os testes e verificações disponíveis e registra os resultados no PR.
4. Reviewer confere a implementação contra os critérios abaixo e a descrição da etapa. Também executa os testes relevantes quando possível.
5. Se houver comentários, Code corrige e Reviewer revisa novamente.
6. Após a aprovação, integrar a mudança e só então avançar para a etapa seguinte.

### Checklist obrigatório do Reviewer

* A implementação atende ao comportamento e ao escopo descritos?
* Os testes cobrem o caminho principal e os casos de erro ou limite relevantes?
* Os testes e verificações indicados no PR foram executados e passaram?
* Os tipos, nomes, mensagens de erro e responsabilidades estão claros?
* Há credenciais, dados pessoais ou conteúdo `.env` incluídos por engano?
* A documentação relacionada continua correta?
* Há mudanças fora do escopo que deveriam ser removidas ou separadas?

## 3. Etapas e distribuição

| Etapa | Entrega | Code | Reviewer |
| --- | --- | --- | --- |
| 0 | Fundamentos do projeto | Pessoa A | Pessoa B |
| 1 | Modelos de dados e estado | Pessoa B | Pessoa A |
| 2 | Regras determinísticas e testes | Pessoa A | Pessoa B |
| 3 | Configuração e adaptador de LLM | Pessoa B | Pessoa A |
| 4 | Chef e SubChef | Pessoa A | Pessoa B |
| 5 | Grafo, roteamento e limite de revisões | Pessoa B | Pessoa A |
| 6 | Checkpoint, pausa, retomada e conflitos de versão | Pessoa A | Pessoa B |
| 7 | Cozinheiro e resposta final | Pessoa B | Pessoa A |
| 8 | Aviso informativo de saúde | Pessoa A | Pessoa B |
| 9 | Pesquisa web com Tavily e referências | Pessoa B | Pessoa A |
| 10 | Servidor MCP, ferramentas e geração de imagem simulada e idempotente | Pessoa A | Pessoa B |
| 10.1 | Provedor real de imagem e integração final das ferramentas | Caio | João |
| 11.0 | README e textos fixos da interface | João | Caio |
| 11 | Interface web do Coxinh.IA | João | Caio |
| 12 | Langfuse, integração e robustez | Caio | João |

Se uma etapa precisar ser dividida em mais de um PR, mantenham a mesma dupla de Code e Reviewer até concluí-la. A inversão ocorre na etapa seguinte, não a cada PR intermediário.

Na sequência atual, Caio implementa a etapa 10.1 e João revisa. João assume a preparação 11.0 e a interface 11, com revisão de Caio. Caio implementa a etapa 12 e João revisa. A preparação textual 11.0 não depende do provedor real e pode ser desenvolvida em paralelo com a etapa 10.1, mas a interface funcional deve usar os contratos aprovados. Quem escreve um PR não o aprova.

### Ferramentas que serão expostas pelo MCP

Os nós continuam sendo funções da aplicação, coordenadas pelo LangGraph. O MCP expõe ferramentas usadas pelo fluxo; ele não substitui os nós nem recebe, por obrigação, a mensagem inicial do usuário. Essa mensagem entra pela aplicação e chega ao Chef no estado.

| Função MCP | Objetivo | Onde será usada | Construção e integração |
| --- | --- | --- | --- |
| `search_web` | Consultar fontes na internet e devolver resultados com origem identificável. | Agente de Saúde, depois do Cozinheiro, com três consultas por receita (decisão 4). Provedor: Tavily (decisão 5). | Adaptador real na etapa 9; ferramenta MCP opcional criada na etapa 10, cuja ligação no servidor padrão permanece pendente. O nó de saúde já usa o adaptador diretamente. |
| `validate_recipe_resources` | Comparar a proposta com os ingredientes, utensílios e meios de preparo autorizados pelo usuário; apontar divergências e substituições. | SubChef e Cozinheiro, antes de finalizar a receita. | Lógica na etapa 2; uso nas etapas 4 e 7; exposição MCP na etapa 10. |
| `generate_coxinha_image` | Entregar ao provedor um pedido fiel à receita final, incluindo ingredientes, cores, texturas, formato e modo de preparo. | Nó de imagem, depois do aconselhamento de saúde e antes da finalização. | Contrato, idempotência e provedor simulado na etapa 10; provedor real na etapa 10.1. |
| `record_impasse_decision` | Registrar a ação humana, os ingredientes ou orientações adicionados e a versão esperada do estado. | Aplicação, a partir da interação do usuário enquanto o fluxo estiver no Impasse. | Lógica na etapa 6; exposição MCP na etapa 10; acionamento pela interface na etapa 11. |

As funções de consulta recebem os dados relevantes do estado para montar a busca. Elas devolvem contexto ao nó que as chamou; não precisam carregar a responsabilidade de manter a conversa inteira. A base RAG e a ferramenta `search_knowledge` não integram o MVP.

`record_impasse_decision` deve ser acionada pela aplicação a partir de uma ação humana identificada, não por uma decisão autônoma do LLM. Sua implementação deve reutilizar o serviço de atualização do estado da etapa 6, evitando criar uma segunda cópia independente do estado no servidor MCP.

## 4. Passo a passo das entregas

### Etapa 0: Fundamentos do projeto

**Arquivos previstos:** `pyproject.toml`, `README.md`, `.gitignore`, `.env.example` e estrutura inicial de `src/`, `mcp_server/` e `tests/`.

**Code:** define como instalar, configurar, executar e testar o projeto; declara as dependências iniciais; garante que ambientes virtuais, `.env` e credenciais não sejam versionados.

**Reviewer:** verifica se uma pessoa consegue seguir o README em um ambiente limpo, se as dependências estão declaradas e se nenhum segredo ou ambiente local está no PR.

**Concluir quando:** a configuração inicial é reproduzível e os comandos documentados funcionam.

### Etapa 1: Modelos de dados e estado

**Arquivos previstos:** `src/schemas.py`, `src/state.py` e testes correspondentes.

**Code:** define o formato validado da receita, da crítica e do estado necessário ao fluxo inicial. Inclui a entrada do usuário, os recursos autorizados, a proposta, a decisão de revisão, os contadores e as versões com responsabilidades distintas. Campos de integrações podem ser acrescentados nas etapas em que forem usados.

O estado deve distinguir:

* `recipe_version`: número da proposta de receita; começa em `0` antes da primeira proposta e avança quando o Chef cria uma nova versão.
* `revision_count`: quantidade de avaliações válidas do SubChef no ciclo atual.
* `total_attempts`: quantidade de avaliações válidas do SubChef na conversa, incluindo ciclos anteriores.
* `max_revisions`: limite de avaliações válidas do SubChef no ciclo atual, incluindo a proposta inicial.
* `state_version`: versão das atualizações do fluxo; no MVP é protegida por lock em memória, e uma implantação durável deve atualizá-la atomicamente no armazenamento compartilhado.
* `state_schema_version`: versão do formato técnico do estado.

`expected_state_version` pertence ao pedido de atualização, não ao estado. O serviço de atualização compara esse valor com `state_version` antes de aplicar a alteração.

**Reviewer:** confere nomes, tipos, campos obrigatórios e se os modelos representam claramente uma proposta, uma crítica e o status do fluxo. Verifica que revisões, avaliações e versões têm responsabilidades distintas.

**Concluir quando:** dados válidos são aceitos, dados inválidos são rejeitados com erro compreensível e os testes passam.

### Etapa 2: Regras determinísticas e testes

**Arquivos previstos:** `src/graph/routing.py`, módulo de validação de recursos ou funções equivalentes e `tests/`.

**Code:** implementa regras que não precisam de LLM: limite de revisões, contadores, estados possíveis e decisão de para onde o fluxo segue. A versão da receita é atualizada quando o Chef cria uma proposta; o controle concorrente de `state_version` é detalhado para a camada de atualização da etapa 6. Implementa também a lógica de `validar_recursos_receita`, inicialmente como serviço local.

Para evitar ambiguidade na contagem, `max_revisions = 2` permite avaliar até duas propostas naquele ciclo:

1. Cada decisão válida do SubChef incrementa `revision_count` e `total_attempts` uma vez.
2. Se a proposta for aprovada, o fluxo segue para o Cozinheiro, inclusive na última tentativa permitida.
3. Se for rejeitada e ainda houver tentativas, o fluxo retorna ao Chef.
4. Se for rejeitada na última tentativa permitida, o fluxo vai para o Impasse.
5. Uma falha técnica não é uma decisão válida e não incrementa nenhum contador.

O limite é configurável. Ao iniciar um novo ciclo após uma retomada explícita na etapa 6, zerar `revision_count`, preservar `total_attempts` e manter `recipe_version` crescente. O nome `max_revisions` permanece por compatibilidade com o estado atual, embora o limite conte avaliações, não apenas revisões.

A validação compara as listas estruturadas de ingredientes, utensílios e métodos de preparo da receita com as listas autorizadas. A comparação é exata após normalizar Unicode, caixa e espaços; não tenta inferir sinônimos nem extrair recursos do texto de preparo. Uma categoria autorizada como `None` não foi informada e fica não verificada; uma lista vazia significa que nenhum recurso daquela categoria foi autorizado. Adições de ingredientes do usuário autorizam esses ingredientes e também devem aparecer na receita.

**Reviewer:** verifica aprovação na última proposta permitida, rejeição com tentativas restantes, rejeição após esgotar as tentativas, valores inválidos e fidelidade aos recursos autorizados. Confirma que a decisão de roteamento usa campos estruturados e que uma falha técnica não é contabilizada como reprovação.

**Concluir quando:** os casos principais e de limite têm testes automatizados; recursos não autorizados são apontados; a aprovação sempre segue para o Cozinheiro e a rejeição após o limite segue para o Impasse.

### Etapa 3: Configuração e adaptador de LLM

**Arquivos usados:** `src/config.py`, `src/utils/llm_adapter.py` e testes com dependências simuladas.

**Code:** centraliza leitura e validação de configuração e cria uma interface pequena para chamar o modelo. Permite configurar temperatura por função ou agente; não registra nem versiona chaves de API.

**Reviewer:** verifica comportamento quando falta configuração, tratamento de erros e se testes podem rodar sem fazer chamadas pagas à API.

**Concluir quando:** configurações inválidas falham de forma explícita e o adaptador pode ser testado sem acesso à rede.

### Etapa 4: Chef e SubChef

**Arquivos previstos:** `src/graph/nodes/chef.py`, `src/graph/nodes/subchef.py`, `src/graph/prompts/chef.py`, `src/graph/prompts/subchef.py`, `src/graph/resource_validation.py` e testes.

**Code:** implementa o Chef para criar ou revisar uma receita estruturada a partir da entrada do usuário, das preferências, dos recursos autorizados e da crítica anterior. Incrementa `recipe_version` quando cria uma proposta. Implementa o SubChef para retornar decisão, crítica e evidências no formato definido. Integra `validate_recipe_resources` à revisão; uma violação determinística reprova a proposta antes de chamar o LLM. Usa modelos simulados nos testes.

O SubChef recebe a proposta, as regras e as autorizações estruturadas, mas não a solicitação original nem a justificativa do Chef, para reduzir ancoragem. Ele verifica critérios semânticos, como coerência mínima entre massa, recheio e preparo. Quando uma categoria de recursos não foi autorizada explicitamente, a avaliação registra que ela não foi verificada. Sua aprovação é uma aprovação da proposta dentro desses critérios, não uma liberação para consumo.

**Reviewer:** verifica se a crítica é acionável, se as saídas seguem os schemas, se os recursos autorizados são respeitados deterministicamente e se os nós não confundem criatividade com fatos ou evidências. Confirma que os testes usam modelos simulados e não fazem chamadas externas.

**Concluir quando:** ambos os nós têm testes focados e a decisão do SubChef pode ser roteada sem analisar texto livre. Uma adição ou substituição não autorizada é identificada na revisão.

### Etapa 5: Grafo, roteamento e limite de revisões

**Arquivos previstos:** `src/graph/graph.py` e testes de integração do grafo.

**Code:** implementa `build_graph()` como construtor do grafo LangGraph e conecta entrada, Chef, SubChef e as rotas para revisão, aprovação ou Impasse. Aplica as regras e os contadores da etapa 2, mantendo o limite configurado por ciclo. Como os nós Cozinheiro e Impasse ainda não fazem parte desta etapa, aprovação e Impasse encerram a execução com o status correspondente.

**Reviewer:** simula aprovação na primeira tentativa, rejeições seguidas de aprovação, aprovação na última tentativa e esgotamento do limite. Verifica que o grafo não entra em ciclo infinito nem incrementa os contadores duas vezes para a mesma decisão.

**Concluir quando:** os caminhos do grafo têm testes de integração determinísticos e respeitam o limite configurado.

### Etapa 6: Checkpoint, pausa, retomada e conflitos de versão

**Arquivos previstos:** `src/graph/impasse.py`, `src/graph/workflow.py`, integração com o checkpointer no builder e testes de pausa e retomada.

**Code:** para o MVP, usa `MemorySaver` e um serviço em memória limitado a uma instância da aplicação. Os checkpoints e registros de idempotência existem apenas enquanto o processo está ativo; a migração para armazenamento durável está documentada em `docs/CONTEXTO_MIGRACAO_PERSISTENCIA.md`. Usa o identificador estável de conversa (`thread_id`) e interrompe o grafo no Impasse. Implementa a lógica de `record_impasse_decision` e separa as ações de salvar informações, retomar e encerrar.

O comportamento esperado é:

1. **Salvar:** registra ingredientes ou orientações e mantém a execução pausada. Não chama o LLM e não reinicia os contadores.
2. **Retomar:** registra primeiro a atualização autorizada. Ao iniciar o novo ciclo, zera `revision_count`, preserva `total_attempts` e `recipe_version`, e encaminha para o Chef, seguido de nova revisão pelo SubChef.
3. **Encerrar:** registra a decisão e finaliza a execução sem chamar o LLM apenas para confirmar o encerramento.

Retomar não significa aprovar manualmente a receita nem pular diretamente para o Cozinheiro. A proposta anterior, a crítica e as informações adicionadas devem continuar disponíveis ao Chef.

O controle de versão deve proteger as atualizações do estado:

* A solicitação informa `expected_state_version` e a aplicação consulta `state_version`.
* No MVP, as ações por conversa são serializadas por um lock em processo. Se as versões divergem, a aplicação devolve um conflito explícito sem aplicar a decisão.
* Essa proteção não coordena processos ou réplicas diferentes e não sobrevive a reinícios. Antes de implantação multi-processo, comparar a versão e gravar a mudança precisa ser uma operação atômica no armazenamento compartilhado.
* Os caminhos que alteram os mesmos dados protegidos, incluindo a retomada e a integração MCP futura, devem usar o mesmo serviço de atualização e versionamento.

**Reviewer:** verifica preservação da conversa, receita e crítica; ausência de chamada ao LLM ao salvar; reinício apenas do contador do ciclo ao retomar; e encerramento explícito. Executa testes de atualização com versão antiga e de duas atualizações concorrentes baseadas na mesma versão, confirmando que não há sobrescrita silenciosa.

**Concluir quando:** testes demonstram pausa, gravação sem LLM, retomada com contexto, preservação do total de tentativas, idempotência e tratamento de conflitos no processo atual. Recuperação após reinício e coordenação entre processos ficam para a migração descrita no arquivo de contexto.

### Etapa 7: Cozinheiro, resposta final e histórico da sessão

**Arquivos previstos:** `src/graph/nodes/cook.py`, `src/graph/prompts/cook.py`,
`src/graph/finalize.py`, `src/recipe_history.py`, `src/recipe_session.py` e testes.

**Code:** transforma a proposta aprovada pelo SubChef em uma resposta em
português do Brasil, com título criativo, subtítulo obrigatório, passos de
preparo em ordem e uma descrição visual para gerar a imagem na etapa 10.

O Cozinheiro devolve listas estruturadas de ingredientes, utensílios e
métodos utilizados. O nó compara essas listas com as da proposta aprovada.
Se houver divergência, pede uma única correção ao modelo. Se a segunda saída
também divergir, a finalização falha e a receita fica fora do histórico.
Pedidos de autorização acontecem no fluxo de revisão e Impasse, antes
do Cozinheiro. Quando faltarem listas de autorização do usuário, a conferência
dessas autorizações fica marcada como `incomplete`.

O finalizador reúne os dados da proposta aprovada e a apresentação do
Cozinheiro em `final_response` e marca a execução como `completed`.
O aviso de saúde fica separado em `final_response["health"]`, com status
`pending` até a integração da etapa 8.

A sessão guarda em memória as receitas concluídas e usa o `thread_id` como
identificador de cada entrada. Cada novo pedido tem seu próprio `thread_id`,
e a galeria reúne as receitas da mesma sessão. Reenviar o resultado de uma
execução já registrada mantém uma única entrada.

**Reviewer:** compara a proposta aprovada com os passos e a descrição visual.
Confere se uma divergência nas listas declaradas aciona apenas uma correção
e se uma segunda divergência impede a finalização. Verifica também se a
galeria lista e abre as receitas da sessão pelo ID.

**Concluir quando:** os testes com modelos simulados verificam o contrato
da saída, a tentativa de correção, a conclusão direta e após retomada,
o isolamento entre sessões e a ausência de entradas duplicadas no histórico.

**Decisões registradas para esta etapa:**

* Não há retomada depois do Cozinheiro. Nenhuma pausa ou pedido de autorização após esse nó.
* A saída do Cozinheiro traz título criativo, subtítulo obrigatório, passos de preparo, descrição visual e as listas estruturadas de ingredientes, utensílios e métodos de preparo. Sem essas listas, a validação de recursos não tem o que comparar.
* Se as listas autorizadas forem `None`, o resultado é marcado como não verificado, nunca como aprovado.
* **Decidido (decisão 9, opção A):** se o Cozinheiro declarar recursos diferentes da proposta aprovada, ele tem uma tentativa de correção. Se a divergência persistir, a finalização falha. Não há pausa nem pedido de autorização depois do Cozinheiro; mudanças de recurso acontecem no ciclo de revisão e Impasse, antes dele.

### Etapa 8: Aviso informativo de saúde

**Arquivos previstos:** `src/graph/nodes/health.py`, `src/graph/health_search.py`, `src/graph/prompts/health.py` e `tests/test_health.py`. Alterações em `src/state.py`: `health_status` e `health_contraindications`. Ligação em `src/graph/builder.py`, stub automático em `tests/conftest.py` e testes de integração em `tests/test_graph.py`.

**Code:** adiciona um aviso complementar sobre contraindicações e possíveis riscos, com incerteza explícita quando não houver evidência suficiente. Nesta etapa, a integração pode receber referências simuladas.

O aviso permanece separado da receita. Ele não aprova, reprova, bloqueia nem modifica a proposta, e não representa uma certificação de segurança para consumo.

**Decisões registradas para esta etapa:**

* Três consultas simuladas, uma para massa, uma para recheio e uma para preparo, feitas uma vez depois do Cozinheiro. A busca real fica na etapa 9.
* `health_status` assume `pending`, `ok`, `insufficient` ou `unavailable`. `ok`: ao menos uma fonte válida fundamenta o aviso. `insufficient`: o aviso foi gerado, mas nenhuma fonte válida o fundamenta. `unavailable`: falha técnica de consulta ou de modelo.
* As contraindicações vêm só do que os trechos sustentam, inclusive riscos gerais como excesso quando os trechos os mencionam. Se nenhum trecho sustentar uma contraindicação, a lista é vazia e a incerteza explica isso. No estado, o campo é `health_contraindications`; na resposta final, `final_response["health"]["contraindications"]`.
* Cada fonte usada traz título e URL de origem. Trecho recuperado sem URL não conta como fonte. O código descarta fonte citada que não existe no contexto recuperado, sem depender do modelo.
* Sem fonte, a incerteza é obrigatória. A incerteza também informa o grau de confiança da evidência.
* Ligação no grafo: `cook → health → finalize`. A receita chega a `completed` mesmo quando o aviso fica `unavailable`.
* Nos testes, `tests/conftest.py` aplica um stub automático ao nó de saúde, para que nenhum teste faça chamada real ao modelo.

**Reviewer:** confirma que o aviso não altera o roteamento nem os ingredientes; confere também que não há diagnóstico ou certeza individual sem fundamento.

**Concluir quando:** testes provam que o resultado de saúde é separado da receita e não interfere na decisão do SubChef ou nas rotas do grafo.

### Etapa 9: Pesquisa web com Tavily e referências

**Arquivos entregues:** `src/utils/web_search.py`, `src/graph/health_search.py`, `src/graph/nodes/health.py`, `src/config.py` e testes. O RAG está fora do escopo do MVP. `docs/CONTEXTO_ETAPA_9.md` é um registro anterior à integração; onde divergir, prevalecem o código integrado e este plano atualizado.

**Code:** implementa três consultas web via Tavily, uma para massa, uma para recheio e uma para preparo, somente no nó de saúde após o Cozinheiro. O adaptador `search_web` valida título, URL e conteúdo, limpa o trecho, limita seu tamanho e descarta itens inválidos. A resposta do Tavily é dado externo, não instrução para o modelo.

O adaptador devolve resultados com `title`, `url` e `content`. Nenhum resultado válido é diferente de uma falha de consulta. A falha deixa o aconselhamento `unavailable`; ausência de fundamento pode deixá-lo `insufficient`. Testes simulam o cliente Tavily e o modelo, sem acesso externo.

Chef e SubChef não fazem pesquisa web nesta etapa. O Agente de Saúde usa o contexto recuperado para montar o aviso e apresenta somente as fontes efetivamente utilizadas. A conferência automática garante que títulos e URLs citados pertencem ao contexto recuperado; a avaliação semântica da fidelidade das afirmações continua sendo um trabalho da etapa 12.

**Reviewer:** verifica correspondência entre trechos e aviso, comportamento sem resultados relevantes e tratamento de indisponibilidade da pesquisa web. Confirma que os testes não dependem de consultas externas reais.

**Concluída:** PR #16 integrado na `main`. O adaptador tem contrato e testes; o aviso indica referências utilizadas e reconhece informação insuficiente.

**Decisões registradas para esta etapa:**

* Provedor de busca web: **API do Tavily, plano gratuito**. A chave fica em `TAVILY_API_KEY`, definida em `.env` e documentada em `.env.example`. Nunca no código nem em commit.
* Cota do plano gratuito: confirmar no painel do Tavily antes de projetar volume de uso. Não há retentativa automática no adaptador, porque cada tentativa pode consumir cota. Cota esgotada é falha técnica e resulta em `unavailable`.
* Limites implementados em `src/utils/web_search.py`: 3 resultados por consulta, 500 caracteres por trecho e tempo limite de 20 segundos por consulta.
* Consultas: três por receita (massa, recheio e preparo), feitas depois do Cozinheiro, uma vez por execução. Nunca dentro do ciclo do SubChef.
* Procedência não é critério, por ser um projeto de humor. Título e URL continuam obrigatórios em cada fonte usada.
* Conteúdo retornado pela web é tratado como dado, nunca como instrução ao modelo.
* Ausência de resultado relevante e falha técnica são estados distintos.
* **Decidido (decisão 10):** a base RAG não faz parte do MVP. A pesquisa web via Tavily é a fonte conectada neste fluxo. `search_knowledge` não é implementada.

### Etapa 10: Servidor MCP, ferramentas e geração de imagem simulada e idempotente

**Arquivos previstos:** `mcp_server/server.py`, cliente MCP na aplicação, armazenamento do resultado de imagem e testes das ferramentas e da chave de idempotência. O contrato detalhado das ferramentas está em `docs/CONTRATO_MCP.md`.

**Decisões registradas para esta etapa:**

* FastMCP (camada sobre o SDK oficial `mcp`), com versão fixada, e transporte streamable HTTP entre os serviços `app` e `mcp` do Docker Compose.
* O container `mcp` registra por padrão `validate_recipe_resources` e `generate_coxinha_image` com provedor simulado. A ferramenta `search_web` existe no servidor quando a dependência de busca é injetada, mas não está registrada no servidor padrão. O nó de saúde usa diretamente o adaptador Tavily. `record_impasse_decision` fica no processo da aplicação e usa a mesma `RecipeSession` que guarda o histórico.
* `search_knowledge` não é implementada no MVP (decisão 10).
* Nó novo `image` no grafo, entre a saúde e a finalização: `cook → health → image → finalize`. Falha de imagem não bloqueia a receita. Não há nó `format_output` separado; o `finalize` continua montando a resposta final (decisão 18).
* O MVP mantém checkpoints, histórico e índice de imagens em memória. Persistência durável fica para uma evolução posterior, com decisão própria de armazenamento e ciclo de vida (decisão 13).
* Idempotência da imagem em memória no MVP, com garantias e limites documentados no contrato.
* O provedor simulado devolve uma referência `simulated://`; isso não representa uma foto gerada. A ligação a um provedor real fica na etapa 10.1.
* Branch `feat/mcp-tools` integrada na `main` pelo PR #15, depois do PR #16 da etapa 9.

**Code:** configura o servidor e o cliente MCP e implementa os contratos de `search_web`, `validate_recipe_resources`, `generate_coxinha_image` e `record_impasse_decision`, com registro condicionado às dependências disponíveis. O nó `image` chama a ferramenta MCP; o `finalize` reúne receita, saúde e estado da imagem.

As implementações das etapas 2, 6 e 9 devem ser reaproveitadas. A integração MCP acrescenta contratos de entrada, saída e erro e o transporte das chamadas, sem duplicar as regras de negócio.

O registro de decisões do Impasse deve ser vinculado à ação humana recebida pela aplicação. A ferramenta não deve ser oferecida ao modelo como forma de inventar uma autorização do usuário. Ela grava a decisão; a aplicação coordena a retomada explícita após a gravação bem-sucedida.

Para a imagem:

* Receber a receita final e sua descrição visual, produzidas pelo Cozinheiro.
* Construir um pedido coerente com ingredientes, cores, texturas, formato e modo de preparo definidos.
* Gerar uma chave estável a partir da entrada canônica relevante para a imagem. Essa entrada deve considerar a receita e os parâmetros que mudam o resultado solicitado.
* Reutilizar o resultado guardado em memória quando já existir uma imagem para a mesma chave no processo.
* Tratar falhas externas e registrar o resultado disponível sem perder a receita final.
* Documentar as garantias e limitações de repetição, concorrência e falhas entre a resposta do provedor e a gravação local. A chave, sozinha, não garante ausência de duplicação em todos esses cenários.

**Reviewer:** confere os contratos das quatro ferramentas, o registro efetivo no servidor padrão, a passagem de dados entre cliente e servidor, o uso correto da versão no Impasse e o tratamento de erros. Para a imagem, verifica fidelidade do pedido, estabilidade da chave, reutilização do resultado e ausência de chamadas pagas nos testes automatizados.

**Concluída quanto à infraestrutura em memória:** PR #15 integrado na `main`. As ferramentas registradas podem ser chamadas pelo cliente com testes de sucesso e erro; a idempotência cobre o mesmo processo. A ligação opcional da busca no servidor padrão e o provedor real ficam explicitamente pendentes na etapa 10.1.

### Etapa 10.1: Provedor real de imagem e fechamento da integração MCP

**Arquivos previstos:** implementação de `ImageProvider` em `mcp_server/`, configuração do provedor e testes com cliente simulado; ajustar `build_default_server` e a documentação do contrato quando necessário.

**Code:** integra um provedor gratuito para gerar imagens utilizáveis pela interface, preservando o contrato `ImageProvider.generate`, a chave de idempotência, o tratamento de falhas e o fluxo `cook → health → image → finalize`. A opção inicial para experimento é **Recraft V4.1 Flash V2 (free)** pelo OpenRouter, cuja variante gratuita está anunciada para retirada em 28/11/2026. A escolha precisa ser substituível. Nunca trocar automaticamente para uma variante paga. Sem provedor gratuito disponível, manter a receita concluída com `image_status` de falha e imagem provisória na interface.

Definir como a imagem retornada será entregue e mantida acessível durante a sessão, inclusive se o provedor devolver dados em base64 ou uma URL temporária. Não expor chaves no navegador, logs ou repositório. A fidelidade visual ao `image_prompt` precisa de revisão humana com receitas absurdas representativas; a idempotência em memória não impede duplicação após reinício ou queda entre geração e registro.

Avaliar se há benefício real em registrar `search_web` no servidor MCP padrão. O nó de saúde já usa `src/utils/web_search.py` diretamente; não trocar esse caminho sem motivo, nem afirmar que uma ferramenta opcional está integrada ao fluxo.

**Reviewer:** verifica resultado utilizável pela interface, falha sem perda da receita, custo zero na configuração escolhida, troca de modelo e testes sem chamadas externas. Confere o vínculo entre a imagem e a receita final.

**Concluir quando:** ao menos uma execução controlada gera imagem real recuperável na sessão, a receita continua disponível quando a imagem falha, e os testes simulados cobrem os contratos. Se a variante gratuita for retirada sem substituta, documentar o bloqueio e manter o fallback visual.

### Etapa 11.0: README e textos fixos da interface

**Arquivos previstos:** `README.md`, documentação de execução em português e um arquivo de conteúdo fixo da interface, em formato e caminho definidos com o frontend. Não criar cópias divergentes do mesmo texto em documentação e código.

**Code (João):** após alinhar este plano, redige o README para explicar o que o Coxinh.IA faz, o fluxo Chef → SubChef → Impasse ou Cozinheiro → Saúde → Imagem → Finalização, a função de cada parte e como instalar, configurar, executar e testar a versão atual. Corrige o link quebrado para a documentação em português. Distingue imagem real de provedor simulado, Langfuse planejado de instrumentação existente e memória de persistência durável. Atualiza comandos quando a interface e o provedor real forem integrados.

Redige também os textos que não vêm da LLM: título e chamada da Home, apresentação do projeto, história **“Da Deloitte à Coxinh.IA”**, bloco **“A dupla por trás do Coxinh.IA”**, rótulos de navegação e ações, estado vazio do carrossel, frases de ambientação da montagem e mensagens de impasse, erro e imagem indisponível. O texto da História precisa ser factual, com informações revisadas por João e Caio; espaços para fotos continuam identificados até a escolha dos ativos. Separar cópia fixa de título, subtítulo, preparo e aviso de saúde gerados pelo fluxo.

**Reviewer (Caio):** confere fidelidade ao projeto, tom de sátira, fatos da História, links, comandos e coerência entre textos e estados reais do backend. Nenhum texto de carregamento deve fingir um evento do grafo que a interface não recebe.

**Concluir quando:** README e textos estão aprovados, com responsáveis e locais de uso definidos. Esta preparação pode avançar em paralelo à etapa 10.1, pois não chama o provedor de imagem.

### Etapa 11: Interface web do Coxinh.IA

**Arquivos previstos:** frontend web com CSS, ativos próprios e testes adequados; a estrutura de pastas e o framework serão definidos no início da etapa. Usar `docs/design/design.md` como especificação visual. Streamlit foi descartado para esta interface.

**Code:** implementa Home, História, montagem, receita pronta e carrossel infinito de receitas concluídas. Preserva a marca Coxinh.IA, os quatro recortes flutuantes definidos no design, a apresentação editorial inspirada no TÒPAS e um acabamento de interface limpo, com acessibilidade e adaptação ao celular. A revisão com UI UX Pro Max auxilia tipografia, espaçamento, contraste e hierarquia, sem substituir a especificação do projeto.

Cria entrada em texto livre, acompanhamento de status, apresentação do resultado e formulário de continuação com o mesmo identificador de conversa. A entrada do usuário é encaminhada ao estado usado pelo Chef. Frases de ambientação da montagem não podem se passar por eventos reais do grafo quando esses eventos não estiverem disponíveis.

No Impasse, a interface permite adicionar ingredientes ou orientações, salvar, retomar ou encerrar. Salvar uma alteração mantém o fluxo pausado; somente a ação explícita de retomar inicia um novo ciclo. A interface apresenta conflitos de versão de forma compreensível e recupera o estado atual sem apagar silenciosamente uma atualização já aceita.

A resposta reúne receita, aviso informativo de saúde, imagem quando disponível e fontes utilizadas. O aviso acompanha um personagem médico fictício sem credencial ou endosso profissional real e não aparece como selo de aprovação para consumo. Imagem simulada, pendente ou com falha usa apresentação provisória. O histórico fica em memória na sessão da aplicação; encerrar o processo perde essas receitas, conforme o escopo atual.

**Reviewer:** testa os caminhos principais e verifica que atualizar a página ou continuar não cria uma conversa nova por engano enquanto a mesma sessão estiver disponível. Confirma que salvar não chama o LLM, que retomar preserva o contexto, que o encerramento é respeitado e que o carrossel não duplica receitas no histórico.

**Concluir quando:** a interface permite iniciar, acompanhar, atualizar e retomar o fluxo validado nas etapas anteriores, além de apresentar resultados e conflitos corretamente.

### Etapa 12: Langfuse, integração e robustez

**Arquivos previstos:** configuração de observabilidade, testes de integração e atualizações no README.

**Code:** integra o Langfuse, que ainda não está instalado nem instrumentado no código, para acompanhar execução do grafo, chamadas de modelo, pesquisas web, ferramentas MCP, imagem e falhas relevantes. Documenta a execução completa e adiciona verificações finais de erros, retomada e operações repetidas. Avalia a fidelidade das afirmações do aviso aos trechos recuperados e a relevância da resposta, com exemplos de casos sem fonte e de conteúdo fictício, sem confundir rastreamento com prova de correção.

**Reviewer:** confere que observabilidade não substitui checkpoint, que dados pessoais não são enviados sem decisão explícita e que testes usam substitutos sem depender de serviços externos. Verifica cenários integrados de Impasse, conflito de versão e preservação dos recursos autorizados. Reinício perde o estado em memória no MVP; persistência durável fica para outra fase.

**Concluir quando:** uma execução pode ser rastreada sem expor dados desnecessários e os critérios de conclusão do projeto foram verificados.

## 5. Critérios de conclusão do projeto

* O fluxo cria uma proposta, recebe revisão, respeita o limite por ciclo e segue para aprovação ou Impasse.
* O Chef recebe a entrada do usuário pelo estado; os nós permanecem funções da aplicação coordenadas pelo LangGraph.
* O usuário pode salvar informações enquanto o fluxo está pausado sem chamar o LLM.
* A retomada explícita preserva o contexto e `total_attempts`, reinicia apenas `revision_count` e volta ao Chef e ao SubChef.
* A decisão de encerrar é registrada e respeitada.
* O histórico de uma sessão mantém receitas concluídas enquanto o processo está ativo. Reiniciar a aplicação perde esse histórico no MVP.
* Atualizações com `expected_state_version` desatualizada são rejeitadas sem sobrescrita. A proteção continua válida para atualizações concorrentes.
* A receita final respeita os recursos autorizados. Mudanças de recurso acontecem no ciclo Chef → SubChef → Impasse, antes do Cozinheiro. Se o Cozinheiro divergir da proposta aprovada, ele tem uma tentativa de correção, e depois a finalização falha (decisão 9).
* O aviso de saúde permanece separado da receita e não aprova, reprova, bloqueia ou modifica o fluxo.
* A pesquisa web preserva título e URL dos resultados; o aviso apresenta as fontes utilizadas e reconhece evidência insuficiente. A base RAG não faz parte do MVP.
* As ferramentas MCP necessárias têm contratos e testes; o registro de Impasse fica vinculado à interação humana e à mesma sessão. O registro opcional de `search_web` no servidor padrão é documentado conforme a decisão da etapa 10.1.
* O pedido de imagem corresponde à receita final. Um provedor gratuito produz referência de imagem utilizável, quando disponível; falhas preservam a receita. A integração evita repetições acidentais dentro das garantias do provedor e do armazenamento em memória.
* A interface permite iniciar, acompanhar e continuar a mesma conversa, além de exibir o resultado com imagem quando disponível.
* O Langfuse permite rastrear a execução sem substituir o estado persistido nem expor dados desnecessários.
* Testes, instruções e configuração estão documentados e revisados.
* Cada mudança foi aprovada por alguém diferente de quem a implementou.

## 6. Registro de decisões e pendências

Estado do projeto em 2026-11-22, conforme o código integrado na `main`:

* Etapa 0: parcial. O README principal é apenas uma apresentação e aponta para `docs/README.pt-br.md`, que não existe. A atualização fica na preparação 11.0, por João com revisão de Caio.
* Etapas 1 a 6: implementadas. A etapa 6 é em memória; persistência durável ficou fora do MVP.
* Etapa 7: integrada na `main` (PR #14).
* Etapa 8: integrada na `main` (PR #13), ligada ao fluxo que agora segue `cook → health → image → finalize`.
* Etapa 9: integrada na `main` (PR #16), com Tavily no nó de saúde e testes simulados.
* Etapa 10: infraestrutura MCP, nó de imagem e provedor simulado integrados na `main` (PR #15). Não há geração de imagem real. `search_web` existe como registro opcional no servidor, não no servidor padrão.
* Etapa 10.1: pendente, para integrar provedor real gratuito e fechar a entrega da imagem.
* Etapa 11.0: pendente, README e textos fixos da interface, por João com revisão de Caio.
* Etapa 11: pendente, interface web definida em `docs/design/design.md`, sem Streamlit.
* Etapa 12: pendente. Não há dependência nem instrumentação Langfuse no código.
* Persistência durável em banco de dados: fora do MVP atual; sessão, checkpoints e índice de imagem permanecem em memória.

| # | Decisão | Situação | Etapas |
| --- | --- | --- | --- |
| 1 | Caminhos reais em `src/` (por exemplo `src/graph/`, `src/state.py`, `src/schemas.py`). O caminho `src/coxinh_ia/` foi descartado. | Decidida | Todas |
| 2 | A seção de saúde da interface se chama **Aconselhamento de consumo** e usa o resultado do nó de saúde. | Decidida | 8, 11 |
| 3 | Não há retomada depois do Cozinheiro. | Decidida | 7, 8 |
| 4 | Consultas web acontecem depois do Cozinheiro, três por receita (massa, recheio e preparo). | Decidida | 8, 9 |
| 5 | Provedor de busca web: API do Tavily, plano gratuito. | Decidida | 9 |
| 6 | Procedência das fontes não é critério; título e URL são obrigatórios. | Decidida | 8, 9 |
| 7 | `health_status` com `pending`, `ok`, `insufficient` e `unavailable`. `ok` exige fonte válida; `insufficient` é aviso sem fundamento nas fontes; `unavailable` é falha técnica. | Decidida (revisada no PR #13) | 8 |
| 8 | Contraindicações vêm só do que as fontes sustentam; lista vazia quando nenhuma é sustentada. | Decidida (revisada no PR #13) | 8 |
| 9 | Recurso divergente no Cozinheiro: uma tentativa de correção e, se persistir, falha da finalização (opção A). | Decidida (PR #14) | 7 |
| 10 | A base RAG fica fora do MVP. A busca web via Tavily é a fonte conectada ao nó de saúde. | Decidida | 9 |
| 11 | Nomes reais de Pessoa A e Pessoa B. | **Pendente** | Todas |
| 12 | Contrato de idempotência em memória entregue. Testar inicialmente Recraft V4.1 Flash V2 gratuito via OpenRouter, com substituição configurável; a variante gratuita está anunciada para retirada em 28/11/2026. Não usar automaticamente modelo pago. | Provedor real pendente | 10.1 |
| 13 | No MVP, sessão, checkpoints e índice de imagens ficam em memória e são perdidos no reinício. A proposta anterior de dois arquivos SQLite pode ser reavaliada em etapa futura, fora do escopo atual. | Escopo do MVP decidido; tecnologia futura em aberto | Futura |
| 14 | Política de privacidade e retenção de traces no Langfuse. | **Pendente** | 12 |
| 15 | Servidor MCP com FastMCP (sobre o SDK oficial `mcp`) e transporte streamable HTTP entre os serviços `app` e `mcp` do Docker Compose. Substitui a decisão anterior de usar `stdio`. | Decidida (revisada) | 10 |
| 16 | Idempotência da imagem em memória no MVP, com garantias e limites documentados. | Decidida | 10 |
| 17 | `record_impasse_decision` fica no processo da aplicação, com a mesma `RecipeSession` usada para registrar o histórico; o container `mcp` expõe ferramentas sem estado compartilhado. | Decidida e implementada | 10 |
| 18 | Nó `image` entre a saúde e a finalização (`cook → health → image → finalize`); falha de imagem não bloqueia a receita; sem nó `format_output` separado. | Decidida | 10, 11 |
| 19 | SubChef e Cozinheiro continuam usando a validação determinística diretamente; o servidor MCP também expõe a ferramenta. Mudar as chamadas do grafo só se houver necessidade concreta. | Implementação atual mantida | 10 |
| 20 | A interface deve conservar a mesma sessão no servidor e o `thread_id` durante navegação e atualização da página. Definir o mecanismo de identificação da sessão antes da implementação, sem prometer recuperação após reiniciar o processo. | Pendente | 11 |
| 21 | Cota gratuita do Tavily a confirmar no painel. O adaptador faz até três consultas por receita, sem retentativa própria; cota esgotada resulta em `unavailable`. Limites implementados: 3 resultados por consulta, 500 caracteres por trecho e 20 segundos por consulta. | Implementada, cota a confirmar | 9 |
| 22 | Interface web com CSS substitui Streamlit. Preservar composição TÒPAS e identidade Coxinh.IA, com acabamento visual limpo, quatro recortes flutuantes e revisão pela UI UX Pro Max. | Decidida, implementação pendente | 11 |
