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
| `buscar_conhecimento` | Recuperar trechos da base RAG com metadados e referências das fontes. | Chef, SubChef e Agente de Saúde, quando precisarem de contexto. | Lógica na etapa 9; exposição e integração MCP na etapa 10. |
| `pesquisar_web` | Consultar fontes na internet e devolver resultados com origem identificável. | Chef, SubChef e Agente de Saúde, quando a consulta for necessária. | Lógica na etapa 9; exposição e integração MCP na etapa 10. |
| `validar_recursos_receita` | Comparar a proposta com os ingredientes, utensílios e meios de preparo autorizados pelo usuário; apontar divergências e substituições. | SubChef e Cozinheiro, antes de finalizar a receita. | Lógica na etapa 2; uso nas etapas 4 e 7; exposição MCP na etapa 10. |
| `gerar_imagem_coxinha` | Enviar à API de imagem um prompt fiel à receita final, incluindo ingredientes, cores, texturas, formato e modo de preparo. | Cozinheiro, após consolidar a receita e a descrição visual. | Implementação e integração na etapa 10. |
| `registrar_decisao_impasse` | Registrar a ação humana, os ingredientes ou orientações adicionados e a versão esperada do estado. | Aplicação, a partir da interação do usuário enquanto o fluxo estiver no Impasse. | Lógica na etapa 6; exposição MCP na etapa 10; acionamento pela interface na etapa 11. |

As funções de consulta recebem os dados relevantes do estado para montar a busca. Elas devolvem contexto ao nó que as chamou; não precisam carregar a responsabilidade de manter a conversa inteira. Usar uma ferramenta em três nós não significa executá-la obrigatoriamente três vezes em toda receita.

`registrar_decisao_impasse` deve ser acionada pela aplicação a partir de uma ação humana identificada, não por uma decisão autônoma do LLM. Sua implementação deve reutilizar o serviço de atualização persistente da etapa 6, evitando criar uma segunda cópia independente do estado no servidor MCP.

## 4. Passo a passo das entregas

### Etapa 0: Fundamentos do projeto

**Arquivos previstos:** `pyproject.toml`, `README.md`, `.gitignore`, `.env.example` e estrutura inicial de `src/`, `mcp_server/` e `tests/`.

**Code:** define como instalar, configurar, executar e testar o projeto; declara as dependências iniciais; garante que ambientes virtuais, `.env` e credenciais não sejam versionados.

**Reviewer:** verifica se uma pessoa consegue seguir o README em um ambiente limpo, se as dependências estão declaradas e se nenhum segredo ou ambiente local está no PR.

**Concluir quando:** a configuração inicial é reproduzível e os comandos documentados funcionam.

### Etapa 1: Modelos de dados e estado

**Arquivos previstos:** `src/coxinh_ia/schemas.py`, `src/coxinh_ia/state.py` e testes correspondentes.

**Code:** define o formato validado da receita, da crítica e do estado necessário ao fluxo inicial. Inclui a entrada do usuário, os recursos autorizados, a proposta, a decisão de revisão, os contadores de tentativas e a versão. Campos de persistência e integrações podem ser acrescentados nas etapas em que forem usados.

O estado deve distinguir:

* `tentativas_ciclo`: quantidade de propostas avaliadas pelo SubChef no ciclo atual.
* `tentativas_total`: quantidade acumulada de propostas avaliadas na conversa, incluindo ciclos anteriores.
* `version`: revisão atual do registro persistido que contém o estado da receita e os dados protegidos contra alterações concorrentes.

`expected_version` representa a versão que quem solicitou uma atualização acredita estar vigente. Esse valor pertence ao pedido de atualização e será comparado com a versão persistida na etapa 6.

**Reviewer:** confere nomes, tipos, campos obrigatórios e se os modelos representam claramente uma proposta, uma crítica e o status do fluxo. Verifica que os dois contadores têm responsabilidades distintas.

**Concluir quando:** dados válidos são aceitos, dados inválidos são rejeitados com erro compreensível e os testes passam.

### Etapa 2: Regras determinísticas e testes

**Arquivos previstos:** `src/coxinh_ia/routing.py`, módulo de validação de recursos ou funções equivalentes e `tests/`.

**Code:** implementa regras que não precisam de LLM: limite de tentativas, contadores, incremento de versão, estados possíveis e decisão de para onde o fluxo segue. Implementa também a lógica de `validar_recursos_receita`, inicialmente como serviço local.

Para evitar ambiguidade na contagem:

1. Uma decisão válida do SubChef sobre uma proposta conta como uma tentativa avaliada e incrementa os dois contadores uma vez.
2. Se a proposta for aprovada, o fluxo segue para o Cozinheiro, inclusive quando a aprovação ocorrer na última tentativa permitida.
3. Se for rejeitada e `tentativas_ciclo` estiver abaixo do limite, o fluxo volta ao Chef com a crítica.
4. Se for rejeitada e o limite tiver sido atingido, o fluxo vai para o Impasse.
5. Falha técnica de uma chamada não equivale a rejeição da proposta e não deve consumir uma tentativa de revisão como se houvesse uma decisão do SubChef.

O limite é configurável. Por exemplo, um limite de duas tentativas permite avaliar duas propostas naquele ciclo. A regra de reinício do contador fica vinculada à retomada explícita da etapa 6.

A validação de recursos compara a receita com o pedido autorizado vigente, incluindo alterações feitas pelo usuário no Impasse. O contrato deve deixar explícito como identificar ingredientes, utensílios e meios de preparo, para que a comparação não dependa de interpretar uma justificativa em texto livre.

**Reviewer:** verifica aprovação, rejeição, limite atingido, valores inválidos e fidelidade aos recursos autorizados. Confirma que a decisão de roteamento usa campos estruturados e que uma falha técnica não é contabilizada como reprovação.

**Concluir quando:** os casos principais e de limite têm testes automatizados; recursos não autorizados são apontados; aprovação na última tentativa segue corretamente para o Cozinheiro.

### Etapa 3: Configuração e adaptador de LLM

**Arquivos previstos:** `src/coxinh_ia/config.py`, `src/coxinh_ia/llm_adapter.py` e testes com dependências simuladas.

**Code:** centraliza leitura e validação de configuração e cria uma interface pequena para chamar o modelo. Permite configurar temperatura por função ou agente; não registra nem versiona chaves de API.

**Reviewer:** verifica comportamento quando falta configuração, tratamento de erros e se testes podem rodar sem fazer chamadas pagas à API.

**Concluir quando:** configurações inválidas falham de forma explícita e o adaptador pode ser testado sem acesso à rede.

### Etapa 4: Chef e SubChef

**Arquivos previstos:** `src/coxinh_ia/nodes/chef.py`, `src/coxinh_ia/nodes/subchef.py` e testes.

**Code:** implementa o Chef para criar ou revisar uma receita estruturada a partir da entrada do usuário, do contexto e da crítica anterior. Implementa o SubChef para retornar decisão, crítica e evidências no formato definido. Integra a validação de recursos da etapa 2 à revisão e usa respostas simuladas nos testes.

O SubChef verifica os critérios do projeto, como massa, recheio, modo de preparo e respeito ao pedido. Sua aprovação é uma aprovação da proposta dentro desses critérios, não uma liberação para consumo.

**Reviewer:** verifica se a crítica é acionável, se a saída segue os schemas, se os recursos autorizados são respeitados e se os nós não confundem criatividade com fatos ou evidências.

**Concluir quando:** ambos os nós têm testes focados e a decisão do SubChef pode ser roteada sem analisar texto livre. Uma adição ou substituição não autorizada é identificada na revisão.

### Etapa 5: Grafo, roteamento e limite de revisões

**Arquivos previstos:** `src/coxinh_ia/graph.py` e testes de integração do grafo.

**Code:** conecta entrada, Chef, SubChef e as rotas para revisão, aprovação ou Impasse. Aplica as regras e os contadores da etapa 2, mantendo o limite configurado por ciclo.

**Reviewer:** simula aprovação na primeira tentativa, rejeições seguidas de aprovação, aprovação na última tentativa e esgotamento do limite. Verifica que o grafo não entra em ciclo infinito nem incrementa os contadores duas vezes para a mesma decisão.

**Concluir quando:** os caminhos do grafo têm testes de integração determinísticos e respeitam o limite configurado.

### Etapa 6: Checkpoint, pausa, retomada e conflitos de versão

**Arquivos previstos:** `src/coxinh_ia/checkpoint.py`, serviço de atualização do estado e registro de decisões do Impasse, ou módulos equivalentes, além dos testes de persistência e retomada.

**Code:** adiciona armazenamento persistente, identificador estável de conversa (`thread_id`) e pausa no Impasse. Implementa a lógica de `registrar_decisao_impasse` e separa as ações de salvar informações, retomar e encerrar.

O comportamento esperado é:

1. **Salvar:** registra ingredientes ou orientações e mantém a execução pausada. Não chama o LLM e não reinicia os contadores.
2. **Retomar:** registra primeiro a atualização autorizada. Ao iniciar o novo ciclo, zera `tentativas_ciclo`, preserva `tentativas_total` e encaminha para o Chef, seguido de nova revisão pelo SubChef.
3. **Encerrar:** registra a decisão e finaliza a execução sem chamar o LLM apenas para confirmar o encerramento.

Retomar não significa aprovar manualmente a receita nem pular diretamente para o Cozinheiro. A proposta anterior, a crítica e as informações adicionadas devem continuar disponíveis ao Chef.

O controle de versão deve proteger as atualizações do estado:

* A solicitação informa `expected_version` e a aplicação consulta a versão persistida.
* Quando as versões coincidem, a aplicação aplica a alteração e incrementa `version`.
* Quando divergem, a aplicação devolve um conflito explícito, sem sobrescrever o estado atual. O solicitante deve recuperar o estado atualizado antes de decidir uma nova atualização.
* Comparar a versão e gravar a mudança deve constituir uma operação atômica, isto é, protegida para que outra atualização não se intercale entre a conferência e a gravação. Uma comparação isolada em Python seguida de uma gravação desprotegida não cumpre esse requisito.
* Os caminhos que alteram os mesmos dados protegidos, incluindo a retomada e a integração MCP futura, devem usar a mesma regra de persistência e versionamento.

**Reviewer:** verifica preservação da conversa, receita e crítica; ausência de chamada ao LLM ao salvar; reinício apenas do contador do ciclo ao retomar; e encerramento explícito. Executa testes de atualização com versão antiga e de duas atualizações concorrentes baseadas na mesma versão, confirmando que não há sobrescrita silenciosa.

**Concluir quando:** testes demonstram pausa, gravação sem LLM, retomada com contexto, preservação do total de tentativas e tratamento de conflitos. Um teste também encerra e recria a instância da aplicação ou do grafo usando o armazenamento persistente, comprovando a recuperação da conversa após reinício.

### Etapa 7: Cozinheiro e resposta final

**Arquivos previstos:** `src/coxinh_ia/nodes/cook.py`, `src/coxinh_ia/finalize.py` e testes.

**Code:** transforma a receita aprovada em passos, prepara sua descrição visual e reúne os resultados disponíveis. Usa a validação de recursos para conferir a versão final contra os ingredientes, utensílios e meios de preparo autorizados.

O Cozinheiro não pode acrescentar ou substituir recursos por conta própria. Avisar que fez uma substituição não equivale a obter autorização. Se uma mudança for necessária, ela deve ser apresentada ao usuário; após autorização e atualização do estado, a proposta volta ao Chef e ao SubChef antes de ser finalizada. O mecanismo de pausa e atualização da etapa 6 pode ser reutilizado para essa interação.

A descrição visual deve acompanhar a receita final: massa, recheio, cores, texturas, formato e efeitos do modo de preparo. Ela será usada pela ferramenta de imagem na etapa 10.

**Reviewer:** compara a receita aprovada com os passos e a descrição visual. Confirma que uma substituição não autorizada não é aceita mesmo quando acompanhada de um aviso e que as incertezas são identificadas.

**Concluir quando:** uma execução aprovada produz uma resposta final estruturada e testada. Os testes verificam preservação dos recursos e exigência de autorização seguida de nova revisão para mudanças.

### Etapa 8: Aviso informativo de saúde

**Arquivos previstos:** `src/coxinh_ia/nodes/health.py` e testes.

**Code:** adiciona um aviso complementar sobre contraindicações e possíveis riscos, com incerteza explícita quando não houver evidência suficiente. Nesta etapa, a integração pode receber referências simuladas.

O aviso permanece separado da receita. Ele não aprova, reprova, bloqueia nem modifica a proposta, e não representa uma certificação de segurança para consumo.

**Reviewer:** confirma que o aviso não altera o roteamento nem os ingredientes; confere também que não há diagnóstico ou certeza individual sem fundamento.

**Concluir quando:** testes provam que o resultado de saúde é separado da receita e não interfere na decisão do SubChef ou nas rotas do grafo.

### Etapa 9: RAG, pesquisa web e referências

**Arquivos previstos:** módulos em `src/coxinh_ia/rag/`, adaptador de pesquisa web, documentos ou fontes selecionados e testes de recuperação e consulta.

**Code:** cria ingestão e busca sobre um conjunto pequeno de fontes confiáveis, mantendo metadados para identificar a origem dos trechos. Implementa os serviços que serão expostos como `buscar_conhecimento` e `pesquisar_web` na etapa 10.

Cada serviço deve devolver resultados estruturados com conteúdo recuperado, identificação da fonte e referência consultável, como URL ou identificador do documento. A pesquisa web deve ter tratamento de falha e permitir testes com respostas simuladas.

O Chef e o SubChef podem consultar esses serviços quando precisarem de contexto. O Agente de Saúde utiliza o material relevante para fundamentar o aviso e apresenta somente as fontes efetivamente utilizadas. Ausência de resultado relevante deve ser distinguida de uma falha técnica de consulta.

**Reviewer:** verifica qualidade e procedência das fontes, correspondência entre trechos e aviso, comportamento sem resultados relevantes e tratamento de indisponibilidade da pesquisa web. Confirma que os testes não dependem de consultas externas reais.

**Concluir quando:** os dois serviços têm contratos e testes; o aviso pode indicar as referências usadas e declarar quando as informações recuperadas são insuficientes.

### Etapa 10: Servidor MCP, ferramentas e geração de imagem idempotente

**Arquivos previstos:** `mcp_server/server.py`, cliente MCP na aplicação, armazenamento do resultado de imagem e testes das ferramentas e da chave de idempotência.

**Code:** configura o servidor e o cliente MCP e expõe as cinco ferramentas previstas: `buscar_conhecimento`, `pesquisar_web`, `validar_recursos_receita`, `gerar_imagem_coxinha` e `registrar_decisao_impasse`.

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
* A retomada explícita preserva o contexto e `tentativas_total`, reinicia apenas `tentativas_ciclo` e volta ao Chef e ao SubChef.
* A decisão de encerrar é registrada e respeitada.
* O armazenamento persistente permite recuperar a mesma conversa após reiniciar a aplicação.
* Atualizações com `expected_version` desatualizada são rejeitadas sem sobrescrita. A proteção continua válida para atualizações concorrentes.
* A receita final respeita os recursos autorizados. Substituições exigem autorização do usuário e nova revisão antes da finalização.
* O aviso de saúde permanece separado da receita e não aprova, reprova, bloqueia ou modifica o fluxo.
* O RAG e a pesquisa web preservam a origem dos resultados; o aviso apresenta as fontes utilizadas e reconhece evidência insuficiente.
* As cinco ferramentas MCP estão implementadas, integradas e testadas, com o registro de Impasse vinculado à interação humana.
* O pedido de imagem corresponde à receita final e sua integração evita repetições acidentais dentro das garantias do provedor e do armazenamento.
* A interface permite iniciar, acompanhar e continuar a mesma conversa, além de exibir o resultado com imagem quando disponível.
* O Langfuse permite rastrear a execução sem substituir o estado persistido nem expor dados desnecessários.
* Testes, instruções e configuração estão documentados e revisados.
* Cada mudança foi aprovada por alguém diferente de quem a implementou.
