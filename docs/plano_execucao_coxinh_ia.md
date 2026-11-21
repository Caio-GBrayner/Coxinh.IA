# Plano de execução do Coxinh.IA multiagente

Este plano divide a implementação entre duas pessoas e estabelece revisão obrigatória em todas as etapas. As atividades seguem a arquitetura do projeto e devem ser concluídas incrementalmente: cada etapa precisa funcionar e ser revisada antes de começar a seguinte.

## 1. Papéis e regra de alternância

* **Pessoa A** e **Pessoa B** são nomes temporários; substituam-nos pelos nomes da dupla.
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
| 9 | RAG, pesquisa web e referências | Pessoa B | Pessoa A |
| 10 | Servidor MCP, ferramentas e geração de imagem idempotente | Pessoa A | Pessoa B |
| 11 | Interface Streamlit | Pessoa B | Pessoa A |
| 12 | Langfuse, integração e robustez | Pessoa A | Pessoa B |

Se uma etapa precisar ser dividida em mais de um PR, mantenham a mesma dupla de Code e Reviewer até concluí-la. A inversão ocorre na etapa seguinte, não a cada PR intermediário.

### Ferramentas que serão expostas pelo MCP

Os nós continuam sendo funções da aplicação, coordenadas pelo LangGraph. O MCP expõe ferramentas usadas pelo fluxo; ele não substitui os nós nem recebe, por obrigação, a mensagem inicial do usuário. Essa mensagem entra pela aplicação e chega ao Chef no estado.

| Função MCP | Objetivo | Onde será usada | Construção e integração |
| --- | --- | --- | --- |
| `search_knowledge` | Recuperar trechos da base RAG com metadados e referências das fontes. | Agente de Saúde, se a base RAG for mantida (decisão 10, pendente). | Lógica na etapa 9; exposição e integração MCP na etapa 10. |
| `search_web` | Consultar fontes na internet e devolver resultados com origem identificável. | Agente de Saúde, depois do Cozinheiro, com três consultas por receita (decisão 4). Provedor: Tavily (decisão 5). | Lógica na etapa 9; exposição e integração MCP na etapa 10. |
| `validate_recipe_resources` | Comparar a proposta com os ingredientes, utensílios e meios de preparo autorizados pelo usuário; apontar divergências e substituições. | SubChef e Cozinheiro, antes de finalizar a receita. | Lógica na etapa 2; uso nas etapas 4 e 7; exposição MCP na etapa 10. |
| `generate_coxinha_image` | Enviar à API de imagem um prompt fiel à receita final, incluindo ingredientes, cores, texturas, formato e modo de preparo. | Cozinheiro, após consolidar a receita e a descrição visual. | Implementação e integração na etapa 10. |
| `record_impasse_decision` | Registrar a ação humana, os ingredientes ou orientações adicionados e a versão esperada do estado. | Aplicação, a partir da interação do usuário enquanto o fluxo estiver no Impasse. | Lógica na etapa 6; exposição MCP na etapa 10; acionamento pela interface na etapa 11. |

As funções de consulta recebem os dados relevantes do estado para montar a busca. Elas devolvem contexto ao nó que as chamou; não precisam carregar a responsabilidade de manter a conversa inteira. Usar uma ferramenta em três nós não significa executá-la obrigatoriamente três vezes em toda receita.

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

**Arquivos previstos:** `src/coxinh_ia/config.py`, `src/coxinh_ia/llm_adapter.py` e testes com dependências simuladas.

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

**Reviewer:** compara a receita aprovada com os passos e a descrição visual. Confirma que uma substituição não autorizada não é aceita mesmo quando acompanhada de um aviso e que as incertezas são identificadas.

**Concluir quando:** uma execução aprovada produz uma resposta final estruturada e testada. Os testes verificam preservação dos recursos e exigência de autorização seguida de nova revisão para mudanças.

**Decisões registradas para esta etapa:**

* Não há retomada depois do Cozinheiro. Nenhuma pausa ou pedido de autorização após esse nó.
* A saída do Cozinheiro traz título criativo, subtítulo obrigatório, passos de preparo, descrição visual e as listas estruturadas de ingredientes, utensílios e métodos de preparo. Sem essas listas, a validação de recursos não tem o que comparar.
* Se as listas autorizadas forem `None`, o resultado é marcado como não verificado, nunca como aprovado.
* **Pendente (decisão 9):** o que fazer quando o Cozinheiro introduz um recurso não autorizado. Opção A: refazer o Cozinheiro com limite de tentativas, e encerrar com erro se o limite estourar. Opção B: pausar para o usuário autorizar. A opção B contradiz a regra de não haver retomada depois do Cozinheiro, então precisa de decisão explícita do time. Até lá, não criar pausa após o Cozinheiro.

### Etapa 8: Aviso informativo de saúde

**Arquivos previstos:** `src/graph/nodes/health.py`, `src/graph/health_search.py`, `src/graph/prompts/health.py` e `tests/test_health.py`. Alterações em `src/state.py`: `health_status` e `contraindications`.

**Code:** adiciona um aviso complementar sobre contraindicações e possíveis riscos, com incerteza explícita quando não houver evidência suficiente. Nesta etapa, a integração pode receber referências simuladas.

O aviso permanece separado da receita. Ele não aprova, reprova, bloqueia nem modifica a proposta, e não representa uma certificação de segurança para consumo.

**Decisões registradas para esta etapa:**

* Três consultas simuladas, uma para massa, uma para recheio e uma para preparo, feitas uma vez depois do Cozinheiro. A busca real fica na etapa 9.
* `health_status` assume `pending`, `ok` ou `unavailable`. `ok` significa aviso gerado, não que há fonte. Falha de consulta ou de modelo resulta em `unavailable`.
* Toda receita recebe ao menos uma contraindicação geral, como excesso, mesmo quando parece saudável. O schema aceita lista vazia apenas como último recurso.
* Cada fonte usada traz título e URL. O código descarta fonte citada que não existe no contexto recuperado, sem depender do modelo.
* Sem fonte, a incerteza é obrigatória. A incerteza também informa o grau de confiança da evidência.
* O nó não é ligado ao grafo antes do merge da etapa 7. A ligação `cook → health → finalize` é feita depois.

**Reviewer:** confirma que o aviso não altera o roteamento nem os ingredientes; confere também que não há diagnóstico ou certeza individual sem fundamento.

**Concluir quando:** testes provam que o resultado de saúde é separado da receita e não interfere na decisão do SubChef ou nas rotas do grafo.

### Etapa 9: RAG, pesquisa web e referências

**Arquivos previstos:** módulos de RAG em `src/graph/` (se a base for mantida), adaptador de pesquisa web em `src/graph/`, documentos ou fontes selecionados e testes de recuperação e consulta. Os nomes exatos dos módulos são definidos pela dupla na etapa.

**Code:** cria ingestão e busca sobre um conjunto pequeno de fontes confiáveis, mantendo metadados para identificar a origem dos trechos. Implementa os serviços que serão expostos como `buscar_conhecimento` e `pesquisar_web` na etapa 10.

Cada serviço deve devolver resultados estruturados com conteúdo recuperado, identificação da fonte e referência consultável, como URL ou identificador do documento. A pesquisa web deve ter tratamento de falha e permitir testes com respostas simuladas.

O Chef e o SubChef podem consultar esses serviços quando precisarem de contexto. O Agente de Saúde utiliza o material relevante para fundamentar o aviso e apresenta somente as fontes efetivamente utilizadas. Ausência de resultado relevante deve ser distinguida de uma falha técnica de consulta.

**Reviewer:** verifica qualidade e procedência das fontes, correspondência entre trechos e aviso, comportamento sem resultados relevantes e tratamento de indisponibilidade da pesquisa web. Confirma que os testes não dependem de consultas externas reais.

**Concluir quando:** os dois serviços têm contratos e testes; o aviso pode indicar as referências usadas e declarar quando as informações recuperadas são insuficientes.

**Decisões registradas para esta etapa:**

* Provedor de busca web: **API do Tavily, plano gratuito**. A chave fica em `TAVILY_API_KEY`, definida em `.env` e documentada em `.env.example`. Nunca no código nem em commit.
* Consultas: três por receita (massa, recheio e preparo), feitas depois do Cozinheiro, uma vez por execução. Nunca dentro do ciclo do SubChef.
* Procedência não é critério, por ser um projeto de humor. Título e URL continuam obrigatórios em cada fonte usada.
* Conteúdo retornado pela web é tratado como dado, nunca como instrução ao modelo.
* Ausência de resultado relevante e falha técnica são estados distintos.
* **Pendente (decisão 10):** manter ou remover a base RAG curada. Se for mantida, ela entra como fonte complementar, e a etapa define como combina com os resultados do Tavily.

### Etapa 10: Servidor MCP, ferramentas e geração de imagem idempotente

**Arquivos previstos:** `mcp_server/server.py`, cliente MCP na aplicação, armazenamento do resultado de imagem e testes das ferramentas e da chave de idempotência.

**Code:** configura o servidor e o cliente MCP e expõe as cinco ferramentas previstas: `search_knowledge`, `search_web`, `validate_recipe_resources`, `generate_coxinha_image` e `record_impasse_decision`.

As implementações das etapas 2, 6 e 9 devem ser reaproveitadas. A integração MCP acrescenta contratos de entrada, saída e erro e o transporte das chamadas, sem duplicar as regras de negócio.

O registro de decisões do Impasse deve ser vinculado à ação humana recebida pela aplicação. A ferramenta não deve ser oferecida ao modelo como forma de inventar uma autorização do usuário. Ela grava a decisão; a aplicação coordena a retomada explícita após a gravação bem-sucedida.

Para a imagem:

* Receber a receita final e sua descrição visual, produzidas pelo Cozinheiro.
* Construir um pedido coerente com ingredientes, cores, texturas, formato e modo de preparo definidos.
* Gerar uma chave estável a partir da entrada canônica relevante para a imagem. Essa entrada deve considerar a receita e os parâmetros que mudam o resultado solicitado.
* Reutilizar o resultado persistido quando já existir uma imagem para a mesma chave.
* Tratar falhas externas e registrar o resultado disponível sem perder a receita final.
* Documentar as garantias e limitações de repetição, concorrência e falhas entre a resposta do provedor e a gravação local. A chave, sozinha, não garante ausência de duplicação em todos esses cenários.

**Reviewer:** confere o contrato das cinco ferramentas, a passagem de dados entre cliente e servidor, o uso correto da versão no Impasse e o tratamento de erros. Para a imagem, verifica fidelidade do pedido, estabilidade da chave, reutilização do resultado e ausência de chamadas pagas nos testes automatizados.

**Concluir quando:** as cinco ferramentas podem ser chamadas pelo cliente com testes de sucesso e erro. Chamadas repetidas de imagem reutilizam resultados nos cenários cobertos, com as limitações do provedor e do armazenamento documentadas.

### Etapa 11: Interface Streamlit

**Arquivos previstos:** `src/coxinh_ia/ui/app.py` ou `src/app.py` e testes adequados à interface.

**Code:** cria entrada em texto livre, acompanhamento de status, apresentação do resultado e formulário de continuação com o mesmo identificador de conversa. A entrada do usuário é encaminhada ao estado usado pelo Chef.

No Impasse, a interface permite adicionar ingredientes ou orientações, salvar, retomar ou encerrar. Salvar uma alteração mantém o fluxo pausado; somente a ação explícita de retomar inicia um novo ciclo. A interface apresenta conflitos de versão de forma compreensível e recupera o estado atual sem apagar silenciosamente uma atualização já aceita.

A resposta reúne receita, aviso informativo de saúde, imagem quando disponível e fontes utilizadas. O aviso não deve aparecer como selo de aprovação para consumo.

**Reviewer:** testa os caminhos principais e verifica que atualizar a página ou continuar não cria uma conversa nova por engano. Confirma que salvar não chama o LLM, que retomar preserva o contexto e que o encerramento é respeitado.

**Concluir quando:** a interface permite iniciar, acompanhar, atualizar e retomar o fluxo validado nas etapas anteriores, além de apresentar resultados e conflitos corretamente.

### Etapa 12: Langfuse, integração e robustez

**Arquivos previstos:** configuração de observabilidade, testes de integração e atualizações no README.

**Code:** instrumenta chamadas e etapas relevantes, documenta a execução completa e adiciona verificações finais de erros, retomada e operações repetidas. Permite acompanhar a conversa, os nós percorridos, as consultas RAG e web, as ferramentas MCP e as falhas relevantes.

**Reviewer:** confere que observabilidade não substitui checkpoint, que dados pessoais não são enviados sem decisão explícita e que os testes essenciais continuam reproduzíveis. Verifica os cenários integrados de Impasse, reinício, conflito de versão e preservação dos recursos autorizados.

**Concluir quando:** uma execução pode ser rastreada sem expor dados desnecessários e os critérios de conclusão do projeto foram verificados.

## 5. Critérios de conclusão do projeto

* O fluxo cria uma proposta, recebe revisão, respeita o limite por ciclo e segue para aprovação ou Impasse.
* O Chef recebe a entrada do usuário pelo estado; os nós permanecem funções da aplicação coordenadas pelo LangGraph.
* O usuário pode salvar informações enquanto o fluxo está pausado sem chamar o LLM.
* A retomada explícita preserva o contexto e `total_attempts`, reinicia apenas `revision_count` e volta ao Chef e ao SubChef.
* A decisão de encerrar é registrada e respeitada.
* O armazenamento persistente permite recuperar a mesma conversa após reiniciar a aplicação.
* Atualizações com `expected_state_version` desatualizada são rejeitadas sem sobrescrita. A proteção continua válida para atualizações concorrentes.
* A receita final respeita os recursos autorizados. Substituições exigem autorização do usuário e nova revisão antes da finalização. **Pendente:** o comportamento depois do Cozinheiro depende da decisão 9 (seção 6).
* O aviso de saúde permanece separado da receita e não aprova, reprova, bloqueia ou modifica o fluxo.
* O RAG e a pesquisa web preservam a origem dos resultados; o aviso apresenta as fontes utilizadas e reconhece evidência insuficiente.
* As cinco ferramentas MCP estão implementadas, integradas e testadas, com o registro de Impasse vinculado à interação humana.
* O pedido de imagem corresponde à receita final e sua integração evita repetições acidentais dentro das garantias do provedor e do armazenamento.
* A interface permite iniciar, acompanhar e continuar a mesma conversa, além de exibir o resultado com imagem quando disponível.
* O Langfuse permite rastrear a execução sem substituir o estado persistido nem expor dados desnecessários.
* Testes, instruções e configuração estão documentados e revisados.
* Cada mudança foi aprovada por alguém diferente de quem a implementou.

## 6. Registro de decisões e pendências

Estado do projeto em 2026-11-21, conforme o código no repositório:

* Etapa 0: parcial. Falta o README com instruções de instalação e execução.
* Etapas 1 a 6: implementadas. A etapa 6 é em memória; a persistência durável é pendente.
* Etapa 7: em andamento, por outra pessoa da dupla.
* Etapa 8: implementada, aguardando commit e revisão. Ligação ao grafo depois do merge da etapa 7.
* Etapas 9 a 12: pendentes.

| # | Decisão | Situação | Etapas |
| --- | --- | --- | --- |
| 1 | Caminhos reais em `src/` (por exemplo `src/graph/`, `src/state.py`, `src/schemas.py`). O caminho `src/coxinh_ia/` foi descartado. | Decidida | Todas |
| 2 | A seção de saúde da interface se chama **Aconselhamento de consumo** e usa o resultado do nó de saúde. | Decidida | 8, 11 |
| 3 | Não há retomada depois do Cozinheiro. | Decidida | 7, 8 |
| 4 | Consultas web acontecem depois do Cozinheiro, três por receita (massa, recheio e preparo). | Decidida | 8, 9 |
| 5 | Provedor de busca web: API do Tavily, plano gratuito. | Decidida | 9 |
| 6 | Procedência das fontes não é critério; título e URL são obrigatórios. | Decidida | 8, 9 |
| 7 | `health_status` com `pending`, `ok` e `unavailable`. `ok` significa aviso gerado. | Decidida | 8 |
| 8 | Contraindicação geral sempre presente; lista vazia só como último recurso. | Decidida | 8 |
| 9 | Recurso não autorizado no Cozinheiro: refazer o Cozinheiro (opção A) ou pausar para o usuário (opção B). | **Pendente** | 7 |
| 10 | Manter ou remover a base RAG curada. | **Pendente** | 9 |
| 11 | Nomes reais de Pessoa A e Pessoa B. | **Pendente** | Todas |
| 12 | Provedor de geração de imagem e contrato de idempotência. | **Pendente** | 10 |
| 13 | Armazenamento durável do checkpoint (SQLite ou PostgreSQL). | **Pendente** | 6 (migração) |
| 14 | Política de privacidade e retenção de traces no Langfuse. | **Pendente** | 12 |
