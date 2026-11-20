# 🥟 Sistema Multiagente de Coxinhas Surreais
## Proposta de arquitetura — LangGraph, LangChain, MCP, RAG, Langfuse e Streamlit

> **Status:** proposta inicial para discussão e implementação incremental.  
> Os nomes de funções e estruturas são sugestões; a API exata de algumas integrações depende das versões escolhidas para as bibliotecas.

## 1. Objetivo

Construir uma aplicação web que recebe ingredientes ou ideias caóticas e gera uma receita criativa de coxinha. Um fluxo de agentes cria e revisa a proposta; depois, o sistema produz o preparo, um aviso de saúde informativo e, se configurado, uma imagem.

O projeto servirá também para praticar:

- LangChain e modelos de linguagem;
- LangGraph, nós, condições e ciclos;
- sistemas multiagente;
- Model Context Protocol (MCP);
- RAG (Retrieval-Augmented Generation);
- checkpoint e retomada de execução;
- idempotência e controle de conflitos de versão;
- observabilidade com Langfuse;
- interface com Streamlit.

## 2. Princípios de projeto

1. **Cada nó deve ter uma responsabilidade clara.** Um nó pode chamar um modelo ou uma ferramenta, mas isso não significa que precisa ser um agente autônomo separado.
2. **O Agente de Saúde não aprova nem altera a receita.** Ele acrescenta um aviso informativo ao resultado.
3. **O aviso de saúde não é diagnóstico nem previsão individual.** Se não houver informação confiável, o agente deve indicar essa incerteza.
4. **O estado do LangGraph é a fonte de continuidade da execução.** A conversa não deve depender apenas da memória do modelo.
5. **A aplicação deve poder pausar e retomar.** Uma interação com o usuário não deve exigir reiniciar o fluxo nem perder o estado salvo.
6. **Ferramentas externas precisam de proteção contra repetição acidental.** Em especial, a geração de imagem deve usar uma chave de idempotência.
7. **RAG e MCP são conceitos diferentes.** RAG recupera informação relevante de uma base; MCP padroniza a comunicação com ferramentas e servidores externos. Eles podem ser usados juntos.

## 3. Fluxo proposto

```text
Início / entrada do usuário
          ↓
        Chef
          ↓
       SubChef
       ↙     ↘
revisar       aprovado
  Chef            ↓
              Cozinheiro
                  ↓
           Agente de Saúde
             ↙         ↘
         aviso       aviso com
         direto      contexto RAG
             ↘         ↙
          geração de imagem
                  ↓
             resposta final

Se as revisões se esgotarem:
SubChef → Impasse → aguarda uma ação do usuário
                         ↓
           usuário adiciona ingrediente ou encerra
                         ↓
               Chef retoma a proposta
```

A etapa de imagem pode ocorrer antes ou depois do aviso de saúde. Neste projeto, a sugestão é gerar a imagem **depois de a receita e o aviso estarem prontos**, sem fazer o Agente de Saúde bloquear o fluxo.

### Definição de rodada

Uma interpretação simples e explícita:

- `recipe_version = 0`: estado inicial, antes de o Chef criar uma proposta; a primeira proposta passa a ser a versão `1`;
- `revision_count`: quantidade de avaliações válidas do SubChef no ciclo atual;
- `max_revisions = 2`: limite de duas propostas avaliadas no ciclo atual, incluindo a proposta inicial;
- cada decisão válida do SubChef incrementa `revision_count` e `total_attempts`;
- quando a proposta é rejeitada na última tentativa permitida, o fluxo pausa no Impasse e aguarda o usuário; uma aprovação na última tentativa segue para o Cozinheiro.

Assim, `recipe_version` representa a versão da proposta, e `revision_count` conta as avaliações feitas no ciclo atual. A adição de um ingrediente pelo usuário pode iniciar um novo ciclo de revisão: zerar `revision_count`, preservar `total_attempts` e manter `recipe_version` crescente, sem apagar o histórico anterior. O nome `max_revisions` permanece por compatibilidade com o estado atual, embora o limite conte avaliações, não apenas revisões.

## 4. Nós do LangGraph

### 4.1 Chef

**Responsabilidade:** criar ou atualizar uma proposta de coxinha com base nos ingredientes, no pedido original e na crítica do SubChef.

**Entrada relevante:**

- pedido original;
- ingredientes solicitados;
- ingredientes adicionados pelo usuário;
- receita anterior, se existir;
- crítica do SubChef;
- mensagens relevantes da conversa.

**Saída:**

- massa;
- recheio;
- lista de ingredientes;
- modo de preparo preliminar;
- resumo da alteração em relação à versão anterior.

**Particularidades:**

- Deve manter os ingredientes e as preferências fornecidos pelo usuário.
- Deve tratar a crítica como orientação para revisão, não como texto a ser copiado.
- Não deve inventar fatos científicos para justificar combinações absurdas.
- Deve produzir saída estruturada, idealmente validada por um schema.
- Não é necessário enviar todo o histórico textual ao modelo em todas as chamadas: o estado deve guardar os dados importantes e um resumo de contexto.

### 4.2 SubChef

**Responsabilidade:** revisar a proposta e devolver uma decisão estruturada ao fluxo.

**Critérios iniciais sugeridos:**

- a receita contém massa, recheio e modo de preparo;
- a proposta é compreensível e tem coerência culinária mínima;
- o recheio satisfaz o requisito do projeto relacionado a matéria orgânica/aminoácidos, se esse requisito for mantido;
- possíveis ingredientes não alimentares ou perigosos são identificados com base em uma fonte ou ferramenta disponível.

**Saída:**

- `approved`: proposta aceita para a etapa seguinte;
- `rejected`: proposta volta ao Chef enquanto houver revisões;
- `critique`: motivo específico e acionável;
- `evidence`: informações ou resultados de ferramentas usados na avaliação, quando disponíveis.

**Particularidades:**

- O SubChef não deve afirmar que um ingrediente é seguro apenas porque parece plausível.
- A validação bioquímica precisa de uma regra verificável ou fonte de dados; não deve depender apenas de uma resposta livre do modelo.
- A política de revisão é separada do aviso de saúde. O Agente de Saúde não substitui nem altera a decisão do SubChef.

### 4.3 Cozinheiro

**Responsabilidade:** transformar a proposta aprovada em uma receita final apresentada de forma criativa.

**Saída:**

- passo a passo detalhado;
- tempo e temperatura, quando fizer sentido e houver base adequada;
- dicas de apresentação;
- descrição visual que poderá ser usada na geração de imagem.

**Particularidades:**

- Deve respeitar os ingredientes definidos pelo Chef.
- Não deve alterar silenciosamente a receita aprovada.
- Se precisar sugerir uma substituição, deve identificá-la como sugestão, não como uma alteração já aplicada.
- Não precisa gerar a imagem diretamente; pode solicitar a ferramenta MCP em uma etapa separada.

### 4.4 Agente de Saúde

**Responsabilidade:** produzir um aviso final informativo e, quando possível, baseado em fontes recuperadas pelo RAG.

**O agente não deve:**

- aprovar ou reprovar a receita;
- modificar ingredientes, massa, recheio ou preparo;
- impedir a geração da imagem ou a apresentação da receita;
- diagnosticar o usuário ou prever efeitos individuais como certeza.

**Conteúdo possível do aviso:**

- contraindicações gerais conhecidas;
- alergênicos identificados;
- riscos relacionados a ingredientes ou preparo, se houver evidência;
- possíveis efeitos descritos nas fontes;
- indicação explícita de incerteza quando a base não tiver informação suficiente;
- referência ou identificação das fontes consultadas.

**Tom:** informativo e bem-humorado, mas sem apresentar uma instituição real como autora de um aviso fictício. Por exemplo: “Aviso culinário não oficial”.

### 4.5 Impasse

**Responsabilidade:** explicar que a proposta não passou pela revisão dentro do limite definido e oferecer opções ao usuário.

**Ações que pode oferecer:**

- adicionar ou substituir ingredientes;
- fornecer uma orientação adicional;
- iniciar outra tentativa;
- encerrar a criação da receita.

O Impasse não deve apagar a conversa nem criar uma nova execução sem vínculo com a anterior. A opção escolhida deve atualizar o estado salvo e retomar o mesmo fluxo.

### 4.6 Preparação da resposta final

Pode ser um nó explícito ou uma etapa simples que reúna:

- receita final;
- aviso do Agente de Saúde;
- imagem, se disponível;
- status do fluxo;
- fontes do aviso, quando aplicável.

## 5. Funções iniciais

Uma primeira organização de funções em Python poderia ser:

```python
def receive_user_request(state):
    """Normaliza a entrada e inicializa os campos do fluxo."""

def chef_node(state):
    """Cria ou revisa a receita com base no pedido e na crítica."""

def subchef_node(state):
    """Avalia a proposta e registra aprovação ou crítica."""

def route_after_subchef(state):
    """Escolhe Chef, Cozinheiro ou Impasse."""

def cook_node(state):
    """Gera o passo a passo final da receita."""

def retrieve_health_context(state):
    """Recupera trechos relevantes da base de conhecimento RAG."""

def health_agent_node(state):
    """Escreve o aviso informativo sem alterar a receita."""

def generate_image_node(state):
    """Solicita a imagem por uma ferramenta MCP, respeitando a idempotência."""

def impasse_node(state):
    """Prepara a mensagem e pausa para obter a decisão do usuário."""

def apply_user_update(state, user_action):
    """Registra uma adição ou orientação sem chamar um modelo de linguagem."""

def finalize_node(state):
    """Monta o resultado final apresentado no Streamlit."""
```

Funções auxiliares úteis:

```python
def validate_recipe_schema(recipe):
    """Valida a estrutura da receita antes de prosseguir."""

def make_recipe_hash(recipe):
    """Cria um hash determinístico para a versão canônica da receita."""

def build_image_idempotency_key(recipe_hash, image_prompt_version):
    """Gera a chave usada para evitar chamadas duplicadas de imagem."""

def summarize_conversation(messages):
    """Cria um resumo de contexto, se necessário, sem substituir o estado estruturado."""
```

## 6. Estado do LangGraph (`RecipeState`)

O estado deve guardar dados suficientes para retomar o fluxo sem depender da memória implícita do modelo.

Exemplo conceitual:

```python
from typing import Annotated, Any, Literal, Required, TypedDict
from langgraph.graph.message import add_messages
from src.schemas import Recipe, SubChefEvaluation

class RecipeState(TypedDict, total=False):
    thread_id: Required[str]
    raw_input: Required[str]
    messages: Required[Annotated[list, add_messages]]
    user_preferences: Required[dict[str, Any]]
    authorized_ingredients: Required[list[str] | None]
    authorized_utensils: Required[list[str] | None]
    authorized_preparation_methods: Required[list[str] | None]
    ingredient_additions: Required[list[str]]
    user_guidance: Required[str | None]
    user_action: Required[Literal["save", "resume", "cancel"] | None]
    recipe: Recipe
    subchef_evaluation: SubChefEvaluation
    recipe_version: Required[int]
    revision_count: Required[int]
    total_attempts: Required[int]
    max_revisions: Required[int]
    status: Required[
        Literal[
            "in_revision",
            "approved",
            "awaiting_user",
            "completed",
            "cancelled",
            "error",
        ]
    ]
    state_version: Required[int]
    state_schema_version: Required[int]
```

### Observações sobre o estado

- `messages` guarda as mensagens necessárias para a conversa; `add_messages` é uma forma comum de acumular mensagens no LangGraph.
- Os campos estruturados (`recipe`, `subchef_evaluation`, `revision_count`) devem ser a referência principal do fluxo. Não se deve depender apenas de procurar informações no histórico de mensagens.
- `thread_id` identifica a conversa e permite recuperar seu checkpoint.
- `recipe_version` identifica a proposta atual; começa em `0` e é incrementada pelo Chef ao criar uma proposta.
- `revision_count` conta as avaliações válidas do SubChef no ciclo atual; `total_attempts` conta as avaliações válidas do SubChef na conversa.
- `state_version` acompanha atualizações do fluxo. No MVP, o serviço em memória serializa operações por conversa; uma implantação durável deve atualizá-la atomicamente no armazenamento compartilhado. A versão esperada acompanha o pedido, não o estado.
- Não guardar o arquivo binário da imagem no estado. Guardar a URL ou uma referência ao armazenamento.
- `state_schema_version` ajuda a identificar mudanças futuras no formato do estado.
- O checkpoint pode conter texto do usuário. Definam quais dados serão persistidos e enviados ao Langfuse.

## 7. Preservar contexto ao adicionar um ingrediente

O MVP combina **LangGraph checkpointer em memória** com um identificador estável de conversa, como `thread_id`. O mesmo `InMemoryWorkflow` deve permanecer ativo durante o ciclo de vida da aplicação.

Fluxo proposto:

1. O usuário envia o pedido no Streamlit.
2. A aplicação inicia o grafo com um `thread_id`.
3. O LangGraph salva checkpoints durante a execução.
4. Se a proposta for rejeitada após o limite de revisões, o grafo pausa com o status `awaiting_user`.
5. O Streamlit mostra uma caixa para o usuário adicionar um ingrediente ou uma orientação.
6. A aplicação atualiza os campos do checkpoint — por exemplo, `ingredient_additions`, `messages` e `user_action` — sem chamar o LLM nesse passo.
7. O mesmo `thread_id` é usado para retomar o grafo.
8. O Chef recebe a receita anterior, a crítica, o histórico relevante e o novo ingrediente. Assim, o contexto não depende de o modelo “lembrar” uma chamada anterior.

**Importante:** adicionar o ingrediente ao estado não exige uma chamada ao LLM. A chamada ao Chef só acontece quando o fluxo retoma e precisa produzir a nova versão da receita. O checkpoint preserva os dados; ele não elimina a necessidade de chamar o modelo para gerar uma revisão.

Também é possível tratar a adição de ingrediente como o início de um novo ciclo de revisão: manter `recipe_version` e o histórico antigos, zerar `revision_count` para o novo ciclo e registrar o motivo da retomada.

### Checkpoints

- O MVP usa `MemorySaver`; o checkpoint se perde quando o processo da aplicação termina.
- O serviço em memória serializa atualizações por conversa, verifica `expected_state_version` e trata chaves de idempotência enquanto a instância está ativa.
- Essa implementação não coordena múltiplos processos e não recupera atualizações após falhas ou reinícios.
- A migração para banco compartilhado, transações atômicas e recuperação entre reinícios está detalhada em `docs/CONTEXTO_MIGRACAO_PERSISTENCIA.md`.

A forma de pausar e retomar pode usar os mecanismos de interrupção e continuação suportados pela versão escolhida do LangGraph. A configuração concreta deve ser conferida na documentação dessa versão.

## 8. Estrutura dos prompts

Os prompts devem ser separados por função e pedir saídas estruturadas. As instruções abaixo são esboços, não prompts finais.

### 8.1 Prompt do Chef

**Instruções de sistema:**

```text
Você é o Chef de um projeto culinário criativo e humorístico.
Sua tarefa é criar ou revisar uma receita de coxinha.

Respeite os ingredientes e as preferências informados pelo usuário.
Considere a crítica do SubChef ao revisar uma proposta.
Não invente fatos científicos. Se um ingrediente for absurdo ou não comestível,
trate isso como parte criativa da proposta sem afirmar que é seguro consumir.
Retorne somente a estrutura solicitada.
```

**Dados de entrada a fornecer:**

```text
Pedido original: {raw_input}
Ingredientes adicionados pelo usuário: {ingredient_additions}
Preferências: {user_preferences}
Versão anterior: {coxinha}
Crítica do SubChef: {critique}
Resumo relevante da conversa: {conversation_summary}
Número da nova versão: {recipe_version}
```

**Formato de saída sugerido:**

```json
{
  "dough": "...",
  "filling": "...",
  "ingredients": ["..."],
  "preparation": "...",
  "utensils": ["..."],
  "preparation_methods": ["..."],
  "revision_summary": null
}
```

### 8.2 Prompt do SubChef

**Instruções de sistema:**

```text
Você é o SubChef revisor de uma receita fictícia de coxinha.
Avalie somente os critérios definidos para o projeto.
Se reprovar, apresente uma crítica específica que ajude o Chef a revisar.
Não confunda criatividade com evidência científica.
Use as evidências de ferramentas ou fontes quando disponíveis.
Se uma informação necessária não estiver disponível, declare a incerteza.
```

**Dados de entrada a fornecer:**

```text
Receita proposta: {coxinha}
Regras de revisão: {review_rules}
Resultado da validação de ingredientes: {ingredient_validation}
Versão da receita: {recipe_version}
```

**Formato de saída sugerido:**

```json
{
  "decision": "approved",
  "critique": "",
  "evidence": [],
  "uncertainty": null
}
```

`decision` deve ser `approved` ou `rejected`. A decisão deve ser roteada pelo código do grafo, não por interpretação de texto livre.

### 8.3 Prompt do Cozinheiro

**Instruções de sistema:**

```text
Você é o Cozinheiro responsável por apresentar uma receita criativa.
Preserve a receita aprovada e produza passos claros e organizados.
Não altere silenciosamente os ingredientes aprovados.
Identifique incertezas sobre tempo ou temperatura, em vez de inventar precisão.
```

**Dados de entrada:**

```text
Receita aprovada: {coxinha}
Tom desejado: {user_preferences.tone}
Restrições de apresentação: {presentation_constraints}
```

**Formato de saída sugerido:**

```json
{
  "recipe_steps": "...",
  "image_prompt": "...",
  "presentation_notes": "..."
}
```

### 8.4 Prompt do Agente de Saúde

**Instruções de sistema:**

```text
Você redige um aviso informativo e complementar sobre a receita.
Você não aprova, reprova, bloqueia nem modifica a receita.
Baseie afirmações factuais apenas nos trechos de referência fornecidos.
Não faça diagnóstico nem preveja efeitos individuais como certeza.
Se os dados forem insuficientes ou o ingrediente for desconhecido,
diga explicitamente que não há informação suficiente.
Use tom claro, breve e, se solicitado, bem-humorado.
Não atribua um aviso fictício a uma instituição real.
```

**Dados de entrada:**

```text
Ingredientes e preparo: {coxinha}
Trechos recuperados pelo RAG: {retrieved_health_context}
Instrução de estilo: {user_preferences.tone}
```

**Formato de saída sugerido:**

```json
{
  "health_warning": "...",
  "contraindications": ["..."],
  "possible_effects": ["..."],
  "sources_used": [],
  "uncertainty": "..."
}
```

### 8.5 Prompt para geração de imagem

A geração da imagem deve receber somente uma descrição visual adequada à ferramenta:

```text
Crie uma imagem ilustrativa e fictícia de uma coxinha baseada nesta descrição:
{image_prompt}

Não apresente a imagem como fotografia de um alimento real ou seguro para consumo.
```

O contrato e as restrições finais dependem do provedor de imagem escolhido.

## 9. RAG para o Agente de Saúde

### Uso no projeto

Criar uma base pequena de documentos com informações gerais e confiáveis sobre:

- alergênicos comuns;
- segurança e armazenamento de alimentos;
- ingredientes tóxicos ou não comestíveis;
- riscos de preparo descritos nas fontes;
- limitações do conhecimento disponível sobre ingredientes incomuns.

### Pipeline básico

```text
Documentos
   ↓
carregamento e limpeza
   ↓
divisão em trechos (chunking)
   ↓
embeddings
   ↓
vector store
   ↓
busca de trechos relevantes
   ↓
Agente de Saúde produz aviso com base nos trechos
```

Cada trecho deve preservar metadados úteis, como título, URL ou nome do documento, seção e data. O agente deve receber as fontes recuperadas e limitar suas afirmações ao conteúdo encontrado.

### Escopo inicial sugerido

Começar com um conjunto pequeno de documentos selecionados manualmente. Isso facilita entender:

- o que foi indexado;
- por que certo trecho foi recuperado;
- quando a busca falhou;
- se o aviso corresponde às fontes.

RAG não garante que o conteúdo esteja correto: a qualidade depende dos documentos, da recuperação e do uso que o modelo faz dos trechos. O resultado deve poder dizer que a base não encontrou informação suficiente.

## 10. Servidor MCP

### Papel do MCP

O servidor MCP expõe ferramentas por uma interface padronizada. O grafo decide quando chamá-las e processa os resultados. MCP não é, por si só, um agente e não substitui o RAG.

### Ferramentas MCP candidatas

#### Prioridade inicial: geração de imagem

```text
generate_image
Entrada:
  - image_prompt
  - idempotency_key
Saída:
  - image_url ou image_reference
  - status
  - provider_request_id, se disponível
```

A ferramenta deve aceitar uma chave de idempotência se o provedor suportar esse recurso. Se não suportar, o aplicativo ainda deve registrar a chamada e evitar solicitá-la novamente quando já existir um resultado para a mesma chave.

#### Ferramentas opcionais para uma etapa posterior

- `validate_ingredient`: consulta uma fonte estruturada para encontrar informação sobre ingredientes;
- `search_food_safety_sources`: busca documentos autorizados para alimentar o RAG;
- `get_image_status`: consulta o estado de uma geração assíncrona.

Não é necessário criar uma ferramenta MCP para cada função interna. A validação de schema, o roteamento e a manipulação do estado podem continuar dentro da aplicação.

### Separação recomendada

- **MCP de imagem:** ferramenta externa para gerar ou consultar imagens.
- **RAG:** componente interno de recuperação de documentos na primeira versão.
- **MCP para busca RAG:** considerar apenas se houver benefício em expor a busca a outros clientes ou serviços.

## 11. Idempotência e conflitos de versão

### Idempotência da imagem

Uma receita igual deve evitar gerar várias imagens acidentalmente, por exemplo, quando uma execução é repetida depois de uma falha.

Procedimento sugerido:

1. Normalizar os campos relevantes da receita e do prompt de imagem.
2. Criar uma representação determinística.
3. Calcular um hash, por exemplo SHA-256.
4. Usar o hash — combinado com a versão do prompt — como `idempotency_key`.
5. Consultar o estado ou armazenamento para verificar se já há resultado para essa chave.
6. Reutilizar o resultado anterior quando apropriado.

A chave deve representar a entrada da operação. Não incluir valores aleatórios na entrada que façam o mesmo pedido produzir uma chave diferente a cada tentativa.

### Conflito de versão

Um conflito pode ocorrer se o usuário enviar duas atualizações baseadas na mesma versão persistida do estado, ou se houver duas execuções concorrentes da mesma conversa.

Campos sugeridos:

- `state_version`: versão atual das atualizações do fluxo; atomicidade compartilhada é requisito para uma implantação durável;
- `expected_state_version`: versão que o pedido de atualização esperava encontrar; é metadado do pedido, não do estado persistido;
- `recipe_version`: versão da proposta de receita;
- `state_schema_version`: versão do formato técnico do estado.

Antes de aplicar uma atualização, comparar `expected_state_version` com `state_version`. Se houver divergência, não sobrescrever silenciosamente os dados: recarregar o estado recente e pedir confirmação ou combinar as alterações de forma explícita. A comparação e a gravação devem ser atômicas.

A implementação concreta de concorrência depende do armazenamento escolhido. Esses campos ajudam a tornar a regra explícita, mas não substituem controle transacional quando múltiplas gravações concorrentes forem possíveis.

## 12. Langfuse: observabilidade e avaliação

Langfuse pode registrar traces de uma execução do grafo e observações associadas às chamadas do modelo e ferramentas.

Informações úteis:

- identificação da execução e do `thread_id` em formato adequado;
- nós executados e duração;
- versão da receita e quantidade de revisões;
- status final do fluxo;
- chamadas a modelos, tokens e custos, conforme integração e provedor;
- documentos recuperados pelo RAG;
- chamadas MCP e erros;
- resultado de reutilização ou geração da imagem.

Langfuse é uma camada de observabilidade, não o armazenamento oficial do checkpoint. O estado necessário para retomar a aplicação deve continuar persistido pelo checkpointer.

**Privacidade:** decidir se os prompts, textos do usuário e documentos recuperados podem ser enviados ao serviço de observabilidade. Usar variáveis de ambiente para credenciais e evitar registrar dados sensíveis sem necessidade.

## 13. Tecnologias previstas

| Área | Tecnologia prevista | Uso |
|---|---|---|
| Linguagem | Python | Aplicação e lógica do fluxo |
| Interface | Streamlit | Entrada do usuário, acompanhamento e resultado |
| Modelos e componentes | LangChain | Integração com modelos e componentes de recuperação |
| Orquestração | LangGraph | Estado, nós, ciclos, roteamento e retomada |
| Checkpoint | SQLite no desenvolvimento; PostgreSQL a avaliar | Persistência do estado entre pausas e reinícios |
| Ferramentas | MCP | Integração padronizada com geração de imagem ou outras ferramentas |
| Recuperação | RAG + embeddings + vector store | Busca de contexto para o aviso de saúde |
| Observabilidade | Langfuse | Traces, latência, chamadas e avaliação |
| Validação de dados | TypedDict ou Pydantic | Estruturar e validar entradas e saídas |
| Testes | pytest | Testar nós, roteamento, persistência e idempotência |

Os provedores de modelo, embeddings, vector store, banco de dados e geração de imagens ainda precisam ser escolhidos. Fixar versões das dependências e validar a compatibilidade das APIs antes de iniciar as integrações.

## 14. Interface Streamlit

Componentes iniciais:

- campo para ingredientes ou ideia caótica;
- botão para iniciar a criação;
- área para acompanhar o status: Chef, revisão, preparo, aviso ou aguardando usuário;
- formulário para adicionar ingredientes quando o fluxo estiver pausado;
- apresentação da receita, do aviso de saúde e da imagem;
- opção de continuar ou encerrar;
- identificação estável da conversa, associada a um `thread_id` reutilizado durante as retomadas.

A interface deve reutilizar o mesmo `thread_id` ao atualizar ou retomar uma conversa. Não criar um novo identificador a cada clique de continuação.

## 15. Estratégia de implementação

### Etapa 1 — Fluxo básico

- implementar os nós Chef, SubChef, Cozinheiro e Impasse;
- definir `ReceitaState`;
- implementar o ciclo e o limite de revisões;
- testar a rota de aprovação e a de rejeição.

### Etapa 2 — Persistência e interação

- adicionar checkpointer;
- persistir um `thread_id` por conversa;
- pausar no Impasse;
- permitir adicionar ingrediente ao estado sem chamar o LLM;
- retomar a execução com o mesmo contexto.

### Etapa 3 — Aviso de saúde

- adicionar o Agente de Saúde como etapa informativa;
- garantir que sua saída não altere a receita;
- incluir incerteza quando faltarem evidências.

### Etapa 4 — RAG

- selecionar documentos;
- criar o pipeline de indexação e busca;
- mostrar as fontes usadas;
- testar exemplos conhecidos e casos sem informação suficiente.

### Etapa 5 — MCP e imagem

- integrar uma ferramenta MCP de geração de imagem;
- criar uma chave de idempotência;
- registrar e reutilizar resultados anteriores quando possível.

### Etapa 6 — Langfuse e robustez

- instrumentar traces;
- acompanhar duração, erros, revisões e chamadas externas;
- testar retomada após interrupção;
- testar atualizações duplicadas e conflitos de versão;
- definir política de privacidade e retenção dos traces.

## 16. Critérios iniciais de conclusão

Uma primeira versão pode ser considerada funcional quando:

- aceita uma entrada e cria uma proposta estruturada;
- o SubChef consegue aprovar ou pedir revisão;
- o limite de revisões é respeitado;
- o fluxo pausa para receber um novo ingrediente;
- a aplicação retoma a mesma conversa a partir de um checkpoint;
- o novo ingrediente é registrado antes de a próxima chamada ao Chef;
- o aviso de saúde é acrescentado sem alterar ou bloquear a receita;
- o Agente de Saúde indica incerteza quando o RAG não encontra evidência;
- uma tentativa repetida não gera chamadas duplicadas de imagem sem necessidade;
- os traces permitem entender o caminho seguido por uma execução.