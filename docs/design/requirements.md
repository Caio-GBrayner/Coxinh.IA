# Requisitos da interface web do Coxinh.IA

Etapa 11 · 22/11/2026 · Português do Brasil

## 1. Escopo e fontes de verdade

A pessoa descreve uma coxinha improvável, acompanha a execução, pode resolver um Impasse e consulta receitas concluídas durante a sessão da aplicação. A experiência visual está em [`design.md`](design.md), os textos fixos em [`conteudo_interface.md`](conteudo_interface.md) e a execução em [`tasks.md`](tasks.md). O contrato de negócio é o código real de `src/api.py`, `src/recipe_session.py`, `src/graph/impasse.py` e `src/graph/finalize.py`. Havendo divergência, conferir o contrato no código e ajustar a documentação antes de implementar a tela.

O frontend é React, TypeScript e CSS em `frontend/`. O desenvolvimento local usa Vite e proxy `/api` para a API FastAPI. A API expõe operações de criar, consultar, listar e decidir o Impasse. A etapa 10.1 integra um provedor de imagem em paralelo; a interface deve suportar os estados de imagem previstos sem depender da conclusão dessa integração. Langfuse pertence à etapa 12.

## 2. Requisitos funcionais

| ID | Requisito | Aceite observável |
| --- | --- | --- |
| RF01 | Navegação Home, Suas receitas e História. | O cabeçalho leva às seções corretas por teclado e ponteiro; a ação Criar receita leva ao formulário. |
| RF02 | Formulário em texto livre. | Recebe ingredientes, utensílios e ideia de preparo; impede envio vazio com mensagem junto ao campo; permite enviar texto longo legível. |
| RF03 | Criação real. | Um envio chama `POST /api/recipes` uma vez e mostra espera até a resposta; envios duplicados ficam bloqueados enquanto há requisição. Não há receita fictícia para simular sucesso. |
| RF04 | Montagem visual. | A animação 2D genérica e o rótulo textual são independentes dos ingredientes; não há percentual nem etapa do grafo inventada; o retorno real encerra a espera. |
| RF05 | Retomada da execução. | O identificador `thread_id` da execução ativa é mantido ao navegar e recarregar a página enquanto a sessão do servidor existir. O frontend consulta `GET /api/recipes/{thread_id}` e trata 404 como sessão/execução indisponível, sem criar outra automaticamente. |
| RF06 | Impasse. | Mostra crítica, proposta e dados salvos quando presentes; permite informar novas orientações e ingredientes; **salvar** permanece pausado, **retomar** continua no mesmo thread e **cancelar** encerra. A interface usa `expected_state_version` e uma `idempotency_key` por decisão. |
| RF07 | Conflito de edição. | Em HTTP 409, consulta o estado atual e apresenta a versão e as alterações recebidas; conserva o que ainda estava digitado e requer nova ação consciente. Não repete a requisição automaticamente. |
| RF08 | Resultado completo. | Se `completed`, mostra título, subtítulo, massa, recheio, ingredientes, utensílios, métodos e passos disponíveis. Se o resultado vier incompleto, comunica isso sem inventar texto da receita. |
| RF09 | Aconselhamento separado. | Mostra `health.warning`, contraindicações, fontes com título e URL, incerteza e estados `pending`, `ok`, `insufficient` ou `unavailable`. Não apresenta selo de segurança ou endosso médico real. |
| RF10 | Imagem tolerante a falhas. | Exibe foto apenas para URL utilizável de imagem concluída. `simulated://`, imagem pendente, falha ou carregamento quebrado produzem alternativa visual com texto; a receita continua legível. |
| RF11 | Histórico da sessão. | `GET /api/recipes` alimenta cards de receitas concluídas, com ID, título, subtítulo e foto ou alternativa. Histórico vazio tem mensagem própria. Criar várias receitas não apaga as anteriores da mesma sessão. |
| RF12 | Carrossel infinito controlado. | Avançar após a última volta à primeira e recuar antes da primeira volta à última; há setas, teclado e deslize no celular. Uma receita mostra só um card. O clique abre a receita correspondente e o retorno preserva a posição. |
| RF13 | História editorial. | Mostra o texto aprovado e as imagens da turma na ordem definida; o bloco da dupla usa o texto aprovado sem simular a foto ainda pendente. |
| RF14 | Estados de erro. | Falhas de rede e servidor aparecem em português; erros não apagam a entrada da pessoa nem provocam repetição automática de uma ação possivelmente concluída. |

## 3. Contrato de dados e sessão

| Operação | Entrada | Resposta relevante |
| --- | --- | --- |
| `POST /api/recipes` | `{ "raw_input": texto }` | `RecipeView` com `thread_id`, `status`, `state_version`, `critique`, `recipe` e `final_response`. |
| `GET /api/recipes/{thread_id}` | ID da execução atual | Estado daquela execução, inclusive `awaiting_user`. |
| `POST /api/recipes/{thread_id}/decisions` | `action`, `expected_state_version`, `idempotency_key`; adições ou orientação quando a ação for `save`. | Estado atualizado da mesma execução; HTTP 409 quando a versão mudou ou a decisão não cabe no estado. |
| `GET /api/recipes` | Cookie da sessão do navegador | Lista de respostas concluídas com `id` correspondente ao `thread_id`. |

A API usa cookie HTTP da sessão. O frontend não deve substituir esse mecanismo por um histórico local autoritativo: pode guardar somente o ID da execução ativa e a posição visual do carrossel. Uma nova criação recebe outro thread e usa a mesma sessão do navegador. Se o processo da API reiniciar, a memória e as receitas se perdem no MVP; o frontend explica a indisponibilidade quando a consulta falha. Não prometer persistência após reinício nem identificação de usuários.

As funções `createRecipe`, `getRecipe`, `submitDecision` e `listRecipes` de `frontend/src/recipeApi.ts` e os tipos de `frontend/src/recipeTypes.ts` são o ponto de partida. Confirmar os valores de `image.status` retornados pelo backend ou pela etapa 10.1 antes de restringir sua apresentação a uma enumeração no frontend. Não colocar chaves de LLM, Tavily ou OpenRouter no JavaScript do navegador.

## 4. Requisitos visuais e de interação

| ID | Requisito | Aceite observável |
| --- | --- | --- |
| RV01 | Abertura editorial. | Card de criação à esquerda e coxinha sobre letreiro Coxinh.IA à direita no desktop; no celular, formulário legível antes da composição decorativa. |
| RV02 | Identidade da marca. | Preto `#000000`, branco `#FFFFFF`, verde `#86BC25`; assinatura correta, sem troca por cores de sugestões de skills. |
| RV03 | Quatro recortes. | Café, marca Deloitte, navio e símbolo Coxinh.IA flutuam em composição estática ou com deslocamento sutil; versões finais têm transparência real e não incluem fundos ou marcas d'água. |
| RV04 | Acabamento. | Espaçamentos consistentes, hierarquia tipográfica forte, campos e botões claros, superfícies limpas; inspiração editorial TÒPAS com cuidado e precisão contemporâneos. |
| RV05 | Acessibilidade. | Foco visível, ordem de teclado lógica, rótulos de controles, mensagens de erro associadas ao campo, texto de estado perceptível e alternativas para imagens informativas. Decorações não recebem foco. |
| RV06 | Movimento. | `prefers-reduced-motion` desativa movimento decorativo; criação, Impasse e resultado permanecem compreensíveis sem animação. |
| RV07 | Responsividade. | Revisão visual em larguras aproximadas de 1440, 1024, 768 e 390 pixels, com textos longos e sem rolagem horizontal indevida. |
| RV08 | Contraste. | Texto comum com contraste mínimo de 4,5:1 e texto grande de 3:1; verde como ação ou detalhe sem depender só da cor para informar estado. |

## 5. Cenários de validação

1. Sessão vazia: Home utilizável, galeria vazia e História completa.
2. Campo vazio e texto extenso: feedback no campo e envio único quando válido.
3. Receita concluída: resultado, aconselhamento, imagem ou alternativa e card no histórico.
4. Duas ou mais receitas: threads diferentes na mesma sessão e carrossel que retorna ao início e ao fim.
5. Impasse: salvar orientação sem retomar, atualizar página, continuar com o mesmo ID e cancelar quando escolhido.
6. Decisão com versão desatualizada: HTTP 409, atualização de estado e formulário digitado preservado.
7. Falha na imagem e referência `simulated://`: nenhum elemento quebrado apresentado como fotografia real.
8. Erro de rede ou reinício da API: orientação de recuperação sem criação duplicada.
9. Navegação por teclado, tela estreita, texto ampliado e movimento reduzido.

Testes automatizados usam API/modelos simulados quando necessário. A revisão visual é feita no navegador em desktop e celular; nenhum teste depende de chamada paga ou de serviço externo real.

## 6. Limites e pendências de conteúdo

A foto da dupla e a foto cenográfica do personagem fictício de saúde ainda dependem de escolha. Podem ter área reservada no rascunho, mas a interface completa continua legível sem elas. Os recortes de produção da abertura exigem preparação a partir das referências e verificação de uso; não publicar uma referência com marca d'água. O provedor real de imagens é responsabilidade da etapa 10.1. A observabilidade Langfuse e persistência durável estão fora do escopo da etapa 11.
