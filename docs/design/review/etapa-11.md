# Etapa 11 — integração da API oficial — 23/11/2026

Este relatório registra a validação executada nesta integração, substituindo os resultados antigos que não descreviam o contrato do PR #20. O design, CSS, marcas e ativos foram preservados; capturas foram regeneradas pela suíte visual.

## Git e preservação

- Merge existente concluído em `5a14fd7` (pais `90894a7` e `7e09f9a`). Nenhum outro commit foi criado.
- `README.md` combinou execução web, persistência, API e limites dos dois lados. `tests/test_api.py` preservou a suíte oficial e adaptou a cobertura anterior de dois navegadores, salvamento sem executar agentes e conflito de versão.
- `src/api.py` foi removido; `tests/browser_api.py` importa `src.api.app.create_app` e injeta `RecipeSession` em memória, com agentes externos simulados.
- `git stash apply 'stash@{0}'` reaplicou o backup. Seus conflitos foram conciliados, sem restaurar API duplicada, cookies de isolamento, autorização de imagens por sessão ou implementação paralela de `accept`.
- `stash@{0}` (`a0b5e08e7aacb5247288c4fbc3a9d3a2dcd67c79`) continua disponível com a mensagem `backup antes da API do PR20`. Alterações de implementação permanecem sem commit e sem stage. Nenhum push nem atualização do PR #18.
- Preservados separadamente: `docs/SKILL.zip`, `docs/skill-fluxograma/`, `retomada-mcp.patch` e `test-results/`. SHA-256 confirmou os 17 arquivos idênticos ao inventário anterior ao merge.

## Comportamento integrado

Criação retorna 202 e o cliente conserva o ID imediatamente. Somente GET é consultado periodicamente, a cada segundo, até `awaiting_user`, `completed`, `cancelled`, `error` ou `interrupted`. Falha no polling oferece consulta manual sem repetir POST. Recarregar restaura o ID e retoma a consulta.

O Impasse usa `/recipes/{thread_id}/impasse`, versão esperada e UUID por decisão. Salvar mantém a pausa; retomar e aceitar acompanham 202 por polling. **Aceitar receita como está** usa a proposta salva, sem enviar o rascunho e sem reimplementar o comportamento já fornecido pelo backend. Conflitos 409 releem o estado e conservam ajustes digitados.

O carrossel global, aprovado por João, usa `{ "items": [...] }` na ordem recebida (mais recente primeiro). O card contém apenas resumo; abrir consulta os detalhes pelo ID. URLs de imagens aceitam somente `/images/<nome seguro>` e são compostas com a mesma base da API. Simulação, extensão/caminho inválido ou recurso ausente mantêm fallback. Links de fontes continuam restritos a HTTP/HTTPS.

## Arquivos e blocos alterados

| Arquivo | Bloco/função e motivo |
| --- | --- |
| `README.md` | Estado atual, execução web/API e limites: comandos oficiais e persistência, combinando os dois lados do merge. |
| `src/api.py` | Remoção da implementação antiga; a API única fica em `src/api/app.py`. |
| `tests/browser_api.py` | Import e criação de `app`: injeta sessão em memória na fábrica oficial. |
| `tests/test_api.py` | Testes de carrossel entre navegadores, save/conflito, pipeline de accept e symlink externo. |
| `tests/test_checkpoint.py` | `test_accept_uses_current_proposal_without_rerunning_review`: preservado do stash, verifica pipeline e ausência de nova revisão. |
| `frontend/src/recipeApi.ts` | `request`, `listRecipes`, `submitDecision`, `recipeImageUrl`: detail estruturado/422, envelope items, rota impasse e base configurável. |
| `frontend/src/recipeTypes.ts` | `RecipeView`, `SavedRecipe`, `DecisionRequest`: running/interrupted, campos ausentes durante execução, resumo global e accept. |
| `frontend/src/useRecipeSession.ts` | Polling, `create`, `decide`, `restore`, `refreshHistory`: ID persistido na aba, lock, recuperação e atualização da galeria ao terminar. |
| `frontend/src/App.tsx` | `openRecipe`, resultado e estados: busca detalhes, ignora respostas antigas de cards, mostra falha/interrupção e limita entrada a 4000 caracteres. |
| `frontend/src/Gallery.tsx` | `Gallery`: cards usam título/subtítulo/imagem do resumo; mantém posição, setas, teclado e gesto. |
| `frontend/src/Impasse.tsx` | `Impasse`: botão de aceite do stash, disponível somente com proposta; campos opcionais seguros. |
| `frontend/src/RecipeResult.tsx` | `RecipeImage`: URL baseada na API, validação de caminho e fallback; fontes mantêm validação independente. |
| `frontend/src/content.ts` | `copy`: carrossel global, indisponibilidade e interrupção, sem prometer isolamento por sessão. |
| `frontend/vite.config.ts` | `server.proxy`: destino padrão 8080, remove /api; testes usam 8001. |
| `frontend/README.md` | Execução, proxy e `VITE_API_URL` para API em outro host, com CORS no backend. |
| `frontend/tests/fixtures.ts` | `mockApi`: respostas 202, polling, impasse, resumos globais e detalhes separados. |
| `frontend/tests/flows.spec.ts` | Contrato assíncrono, aceite sem rascunhos, versões, erros, imagens, recuperação e API real com dois navegadores. |
| `docs/design/requirements.md` | RF03–RF14, contrato e cenários: fonte oficial, estados, persistência e carrossel global. |
| `docs/design/design.md` | Histórico, integração e apresentação de imagens: comportamento novo com direção visual preservada. |
| `docs/design/tasks.md` | Checklist de integração: API única, stash, polling e validação. |
| `docs/design/review/etapa-11.md` | Este relatório registra somente comandos e resultados executados nesta rodada. |
| `docs/design/review/{1440,1024,768,390}/*.png` | Evidências regeneradas pelos testes visuais; inventário exato abaixo. |

Nomes de contratos foram mantidos quando ainda úteis. `SavedRecipe` agora representa o resumo oficial, e os detalhes usam `FinalResponse`; essa separação decorre do contrato, não de reorganização opcional. Polling a cada segundo, UUID por decisão e `VITE_API_URL` são escolhas de implementação compatíveis com ele.

## Validação executada

- `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -p no:cacheprovider`: **25 passed**, antes do commit de merge.
- Primeira suíte Python completa: falhou na coleta por ausência de `langgraph.checkpoint.sqlite`.
- `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`: primeira tentativa bloqueada pela rede do sandbox; repetida com permissão, **concluiu com sucesso** no ambiente virtual.
- `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`: **252 passed, 1 skipped** em 21,15 s. Symlink ignorado por indisponibilidade da criação nesta conta Windows.
- `npm.cmd run build` e `npm.cmd run lint`: **aprovados**; lint sem diagnósticos.
- Primeiro `npm.cmd test`: os 29 cenários reportaram sucesso, mas o desligamento dos servidores travou. A árvore desse Playwright foi identificada e encerrada; essa tentativa não conta como execução com saída zero.
- `npm.cmd test` com permissão para gerenciar processos Windows: **35 passed**, saída 0, em 1,6 min. Repetição final após corrigir a publicação tardia na galeria e fortalecer o teste: **35 passed**, saída 0, em 1,7 min.

Durante a integração real, LangGraph emitiu aviso de desserialização de `src.schemas.CookOutput` fora da lista permitida. Os testes concluíram sem falhas; não foi alterada a política de desserialização nesta tarefa. O Node também emitiu avisos de `NO_COLOR`/`FORCE_COLOR`.

Inspeção visual direta das capturas: resultado em 390 px, Home final em 390 px e Impasse final em 1440 px. A navegação usa o rótulo curto “Receitas” para preservar o espaço dos controles móveis; o título auxiliar identifica o carrossel global.

## Limites

Os testes usam agentes externos simulados, inclusive quando a API/workflow são reais. Nenhuma geração paga ou integração real com OpenRouter/Tavily/LLM foi validada. Persistem os limites oficiais: um processo da API, ausência de autenticação e impossibilidade de recuperar pela interface um ID de criação cuja resposta se perdeu. Não há repetição automática de POST.

As pendências editoriais anteriores (como foto da dupla e aceite dos recortes) não foram resolvidas por esta integração. Não houve alteração do CSS nem redesenho de ativos.

## Comandos Git executados

`git status`, `git stash list`, `git show` e `git diff` conferiram estado, conflitos e alterações. `git add -- README.md tests/test_api.py src/api.py tests/browser_api.py` marcou somente as resoluções necessárias, mantendo o que o merge já havia preparado. `git commit -m "Merge origin/main into feat/interface-web"` criou o único commit. `git stash apply 'stash@{0}'` preservou a entrada. Após conciliar seus conflitos, `git add --` usou caminhos explícitos, e `git restore --staged --` retirou as alterações locais do índice. Não foram executados `git add .`, `git clean`, `git reset --hard`, push ou operações de PR.

## Inventário das capturas alteradas

- `docs/design/review/1024/galeria.png`
- `docs/design/review/1024/historia.png`
- `docs/design/review/1024/home.png`
- `docs/design/review/1024/impasse.png`
- `docs/design/review/1024/marca-header.png`
- `docs/design/review/1024/resultado.png`
- `docs/design/review/1024/texto-ampliado.png`
- `docs/design/review/1024/turma-0.png`
- `docs/design/review/1024/turma-100.png`
- `docs/design/review/1024/turma-25.png`
- `docs/design/review/1024/turma-50.png`
- `docs/design/review/1440/galeria.png`
- `docs/design/review/1440/historia.png`
- `docs/design/review/1440/home.png`
- `docs/design/review/1440/impasse.png`
- `docs/design/review/1440/marca-header.png`
- `docs/design/review/1440/marca-rodape.png`
- `docs/design/review/1440/resultado.png`
- `docs/design/review/1440/texto-ampliado.png`
- `docs/design/review/1440/turma-0.png`
- `docs/design/review/1440/turma-100.png`
- `docs/design/review/1440/turma-25.png`
- `docs/design/review/1440/turma-50.png`
- `docs/design/review/390/galeria.png`
- `docs/design/review/390/historia.png`
- `docs/design/review/390/home.png`
- `docs/design/review/390/impasse.png`
- `docs/design/review/390/marca-header.png`
- `docs/design/review/390/marca-rodape.png`
- `docs/design/review/390/resultado.png`
- `docs/design/review/390/texto-ampliado.png`
- `docs/design/review/390/turma-0.png`
- `docs/design/review/390/turma-100.png`
- `docs/design/review/390/turma-25.png`
- `docs/design/review/390/turma-50.png`
- `docs/design/review/768/galeria.png`
- `docs/design/review/768/historia.png`
- `docs/design/review/768/home.png`
- `docs/design/review/768/impasse.png`
- `docs/design/review/768/marca-header.png`
- `docs/design/review/768/resultado.png`
- `docs/design/review/768/texto-ampliado.png`
- `docs/design/review/768/turma-0.png`
- `docs/design/review/768/turma-100.png`
- `docs/design/review/768/turma-25.png`
- `docs/design/review/768/turma-50.png`
