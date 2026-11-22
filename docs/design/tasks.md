# Tarefas da etapa 11: interface web

22/11/2026 · Responsável pela implementação: João · Revisão: Caio

Este checklist orienta o Codex no VS Code. Ler primeiro [`requirements.md`](requirements.md), [`design.md`](design.md), [`conteudo_interface.md`](conteudo_interface.md) e a seção da etapa 11 em `docs/plano_execucao_coxinh_ia.md`. Conferir os arquivos no branch local antes de editar: há uma API e um cliente TypeScript preparados, mas o frontend ainda pode conter a tela padrão do Vite. Não reescrever contratos que já passam nos testes apenas para reorganizá-los.

## 0. Preparar e conferir a base

- [x] Verificar branch, status do Git e diferenças locais. Preservar alterações existentes. Não incluir `retomada-mcp.patch` no PR.
- [x] Confirmar `frontend/` com React, TypeScript, Vite e `frontend/vite.config.ts` com proxy `/api` para `127.0.0.1:8000`.
- [x] Conferir `src/api.py`, `frontend/src/recipeApi.ts`, `frontend/src/recipeTypes.ts`, `tests/test_api.py` e o contrato real do Impasse antes de criar componentes.
- [x] Rodar `python -m pytest -q` e `npm run build` dentro de `frontend/`; registrar a linha de base e resolver apenas falhas relacionadas à etapa.
- [x] Abrir `/api/recipes` por Vite e confirmar que a resposta vazia `[]` corresponde à sessão atual. Esse teste de conexão já foi feito por João, mas pode ser repetido após alterações da configuração.

## 1. Fundamentos da interface

- [x] Substituir a página padrão do Vite em `frontend/src/App.tsx`, `frontend/src/App.css`, `frontend/src/index.css` e `frontend/index.html` por estrutura semântica em português do Brasil.
- [x] Centralizar textos fixos da UI em um módulo próprio de `frontend/src/`, conforme `conteudo_interface.md`, sem manter cópias conflitantes no código.
- [x] Definir tokens CSS para as três cores da marca, tipografia, escalas de espaço, largura de conteúdo, bordas e foco. Conferir contraste e evitar que o ponto verde seja o único indicador de estado.
- [x] Organizar componentes por responsabilidade sem criar abstrações artificiais: navegação, formulário, montagem, Impasse, resultado, saúde, galeria e História podem evoluir em arquivos próprios se isso facilitar a leitura.
- [x] Garantir que renderização de dados da API use texto React, sem interpretar HTML fornecido por receita, fonte ou mensagem de erro.

## 2. Home, marca e ativos

- [x] Construir cabeçalho com símbolo, nome Coxinh.IA, links Home, Suas receitas, História e ação Criar receita.
- [x] Construir primeiro enquadramento com card de formulário à esquerda, título aprovado e entrada de texto livre visível ao abrir a página; no celular, manter formulário antes das decorações.
- [x] Posicionar letreiro gigante atrás de uma coxinha aberta na área direita, sem usar foto de uma receita gerada para representar todas as criações.
- [ ] Preparar versões de produção com canal alfa real de café, logo Deloitte, navio e símbolo Coxinh.IA. Usar as referências de `docs/design/`, conferir direitos de uso e descartar versões com marca d'água. Organizar os arquivos finais em `frontend/` com nomes inequívocos.
- [x] Tratar imagens decorativas com `alt=""`, sem foco e sem interceptar cliques ou o preenchimento do formulário.
- [x] Aplicar entrada e flutuação discretas somente se ajudarem a profundidade da abertura; desativar com movimento reduzido.

## 3. Criação e montagem

- [x] Ligar o formulário a `createRecipe(rawInput)`; validar campo vazio e manter a ideia escrita quando houver falha.
- [x] Bloquear envios repetidos enquanto a mesma requisição estiver em andamento e mostrar estado textual de processamento acessível.
- [x] Montar uma sequência 2D genérica de massa, recheio e fechamento, reutilizada em toda criação. O texto de ambientação não descreve etapas reais de backend sem evidência.
- [x] Encerrar a espera pelo retorno real: `completed` abre resultado, `awaiting_user` abre Impasse; demais estados recebem mensagem apropriada.
- [x] Conservar o `thread_id` da execução ativa ao navegar e recarregar a página, consultando `getRecipe(threadId)` ao restaurar. Consultar o backend antes de decidir que uma ação falhou; não repetir automaticamente um POST.

## 4. Impasse e continuidade

- [x] Apresentar crítica, proposta, `ingredient_additions`, `user_guidance` e versão atual quando presentes.
- [x] Permitir inserir ingredientes e orientação; validar a ação `save` para que envie ao menos um ingrediente ou orientação. Não enviar campo vazio como alteração.
- [x] Usar `submitDecision` com `thread_id`, `expected_state_version` e uma `idempotency_key` própria da decisão. Salvar permanece em `awaiting_user`; retomar e cancelar são ações explícitas.
- [x] Ao receber HTTP 409, consultar novamente o estado, mostrar alteração/conflito, preservar o texto digitado e deixar a pessoa escolher a próxima ação. Não sobrescrever atualização aceita.
- [x] Ao atualizar a página no meio do Impasse, restaurar a mesma execução se a sessão da API ainda existir. Tratar 404 sem iniciar criação automaticamente.

## 5. Resultado e saúde

- [x] Exibir título, subtítulo, massa, recheio, ingredientes, utensílios, métodos e passos vindos de `final_response.recipe`, com quebras e textos longos legíveis.
- [x] Renderizar fotografia somente para URL de imagem final utilizável. Para `simulated://`, pendência, indisponibilidade e erro de carregamento, mostrar imagem provisória e texto claro; jamais rotular simulação como imagem real gerada por IA.
- [x] Montar bloco separado de Aconselhamento de consumo com aviso, contraindicações, incerteza, status e links de fontes efetivamente fornecidos pela API. URLs externas com abertura segura, sem texto de origem interpretado como instrução.
- [x] Reservar espaço para a foto cenográfica de um personagem fictício de médico; só integrar ativo aprovado, sem nome, credencial ou marca de instituição. O conteúdo deve ser completo sem a foto.
- [x] Manter ações de voltar às receitas e criar outra receita sem apagar a execução concluída ou seu registro no histórico.

## 6. História e carrossel de receitas

- [x] Construir seção editorial **Da Deloitte à Coxinh.IA** com texto aprovado, moldura, detalhe verde e ilustração da turma seguida pela foto real. Incluir bloco da dupla com texto aprovado; não simular uma foto ainda ausente.
- [x] Consultar `listRecipes()` após carregar a aplicação e após concluir uma receita. Exibir histórico vazio com a mensagem definida e ordenar a apresentação da mais recente para a mais antiga.
- [x] Criar cards com imagem ou alternativa, título e subtítulo. O clique abre o resultado daquela receita sem alterar ou duplicar seu ID.
- [x] Implementar carrossel circular com setas, teclado e gesto de deslize em tela sensível ao toque. Uma única receita não cria cópias. Preservar índice ao entrar e sair do detalhe e manter só uma versão acessível de cada receita.
- [x] Usar interação para avançar, sem reprodução automática; respeitar movimento reduzido.

## 7. Revisão técnica e visual

- [x] Criar testes de comportamento para envio único, resposta concluída, Impasse, salvar sem retomar, retomar, conflito 409, restauração, histórico vazio e múltiplo, ciclo do carrossel e alternativas de imagem. Simular chamadas externas e não testar CSS por cópia de implementação.
- [x] Rodar build e lint do frontend, testes de backend pertinentes e uma navegação local completa com a API. Registrar resultados reais no PR.
- [x] Revisar as seis áreas da interface em aproximadamente 1440, 1024, 768 e 390 pixels. Testar título longo, aviso extenso, fonte com URL longa, erro, imagem quebrada e histórico vazio.
- [x] Revisar foco e ordem por teclado, nomes acessíveis, ampliação do texto, preferência por movimento reduzido e contraste de texto.
- [x] Conferir direção visual com UI UX Pro Max, acabamento com Impeccable, função do movimento com orientações de Emil Kowalski e identidade própria com Taste Skill. Usar observações como revisão, sem substituir este contrato por cores, textos ou componentes genéricos.
- [x] Atualizar README apenas com comandos de execução comprovados e limitações reais. Não declarar Langfuse implementado na etapa 11.
- [ ] Abrir PR da etapa 11 para revisão de Caio, com capturas desktop e celular, cenários executados e lista honesta de ativos pendentes. Não fazer merge antes da revisão prevista no plano.

## Dependências e limite de conclusão

As tarefas 0 e 1 precedem as telas. A criação depende da API já preparada; Impasse depende da execução ativa; resultado e galeria dependem dos dados reais. A etapa 10.1 pode terminar durante a implementação: integrar o resultado da imagem por contrato, sem acoplar o frontend a um modelo específico. A foto da dupla e a foto cenográfica do personagem de saúde podem permanecer pendentes se a experiência funcionar sem elas e a pendência constar no PR. Os quatro recortes limpos e a revisão visual das telas fazem parte do aceite desta etapa.

## Evidências da implementação

Ver [relatório da etapa 11](review/etapa-11.md), capturas, comandos e pendências. O aceite permanece parcial: recortes com alfa preparados, mas acabamento/fidelidade ainda precisam de revisão. Uso das referências autorizado por João em 22/11/2026. Fotos da dupla e do personagem de saúde pendentes; etapa 10.1 não implementada aqui.

