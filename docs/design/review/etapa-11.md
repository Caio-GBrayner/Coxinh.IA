# Revisão da etapa 11 — 22/11/2026

A interface funcional foi implementada na branch `feat/interface-web`, preservando `src/api.py`, o contrato TypeScript e as alterações locais já existentes. O aceite final da etapa permanece parcial por causa do acabamento dos ativos. A etapa 10.1 não foi implementada aqui.

## Comportamentos entregues

- Home em português com formulário livre, validação, bloqueio síncrono de envios duplicados e entrada preservada em falhas.
- Montagem 2D em CSS, comandada pela resposta real. A animação não representa etapas técnicas nem percentuais do backend.
- Impasse com crítica, proposta, versão, ingredientes e orientação registrados. Salvar mantém a pausa; continuar e encerrar são ações explícitas. Cada decisão tem chave de idempotência própria e versão esperada.
- HTTP 409 e falha de decisão consultam o estado antes de outra ação, sem repetição automática e sem apagar o rascunho.
- Restauração do ID ativo pela API ao recarregar. Cookie continua sendo a identidade da sessão; a primeira listagem precede outras consultas para evitar criar dois cookies concorrentes.
- Resultado com todos os campos disponíveis; saúde separada, fontes com protocolos seguros e texto React sem interpretar HTML.
- Imagens `generated`, `reused` ou `completed` só são exibidas com URL HTTP(S) utilizável. `simulated://`, pendência, erro e falha de carregamento têm alternativas explícitas. A compatibilidade final com o provedor real deverá ser conferida na etapa 10.1.
- História editorial com os textos aprovados, ilustração seguida da foto da turma e bloco da dupla sem foto inventada.
- Histórico consultado no carregamento e depois das operações. Ordem mais recente primeiro, carrossel circular por setas, teclado e deslize, sem autoplay nem duplicação de IDs. A posição é conservada ao abrir e voltar.

## Validação

Resultado final: **196 testes Python aprovados; 19 testes de navegador aprovados; build e lint aprovados, sem avisos do lint**. `npm.cmd ci` foi concluído com sucesso depois de liberar um módulo nativo bloqueado por servidores Vite abertos. Os testes de integração emitiram avisos do LangGraph sobre futura restrição de desserialização de `Recipe` e `SubChefEvaluation`, sem falhas; o backend foi preservado.

Linha de base: 196 testes Python e build Vite passaram antes da implementação. `npm.ps1` foi bloqueado pela política do PowerShell; todos os comandos documentados usam `npm.cmd`.

Comandos finais:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
Set-Location -LiteralPath .\frontend
npm.cmd ci
npm.cmd run build
npm.cmd run lint
npm.cmd test
```

A suíte inclui 14 cenários de comportamento e integração, quatro cenários de revisão visual (1440, 1024, 768 e 390 pixels) e uma verificação de alfa nos recortes. A integração percorre os endpoints FastAPI e o workflow reais, com os agentes externos substituídos somente no servidor de testes. Foram testados sessão vazia, criar duas receitas, Impasse, salvar, recarregar e continuar no mesmo ID, além de conflito, cancelamento, 404, falhas de rede e imagens.

A revisão com Edge headless cobre Home, História, montagem, Impasse, resultado e galeria. Inclui títulos longos, aviso extenso, URL longa, texto a 200%, foco inicial por teclado e preferência por movimento reduzido. A análise axe usa WCAG A/AA nas áreas renderizadas; não substitui uma avaliação manual completa com leitor de tela. A sobreposição da coxinha decorativa no texto da História em 390px foi encontrada visualmente e corrigida.

O teste de montagem usa desenhos CSS fixos, não fotos específicas de ingredientes. A versão com movimento reduzido mostra apenas a figura estática e o texto de processamento.

## Capturas

As imagens usam dados de teste, não receitas produzidas por modelos externos.

| Largura | Home | História | Montagem | Impasse | Resultado | Galeria |
| --- | --- | --- | --- | --- | --- | --- |
| 1440 | [abrir](1440/home.png) | [abrir](1440/historia.png) | [abrir](1440/montagem.png) | [abrir](1440/impasse.png) | [abrir](1440/resultado.png) | [abrir](1440/galeria.png) |
| 1024 | [abrir](1024/home.png) | [abrir](1024/historia.png) | [abrir](1024/montagem.png) | [abrir](1024/impasse.png) | [abrir](1024/resultado.png) | [abrir](1024/galeria.png) |
| 768 | [abrir](768/home.png) | [abrir](768/historia.png) | [abrir](768/montagem.png) | [abrir](768/impasse.png) | [abrir](768/resultado.png) | [abrir](768/galeria.png) |
| 390 | [abrir](390/home.png) | [abrir](390/historia.png) | [abrir](390/montagem.png) | [abrir](390/impasse.png) | [abrir](390/resultado.png) | [abrir](390/galeria.png) |

Cada pasta também contém `texto-ampliado.png`.

## Aplicação das quatro referências

As referências foram lidas como métodos de revisão; não foram instaladas como ferramentas nem substituíram o briefing.

- [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill): hierarquia de títulos condensados, texto legível, alvos de toque, foco visível, quebra de textos longos e quatro larguras de revisão.
- [Impeccable](https://github.com/pbakaus/impeccable): crítica por seção e revisão de espaçamento, contraste, estados de erro e excesso de decoração. O achado de sobreposição no celular foi corrigido.
- [Emil Kowalski](https://github.com/emilkowalski/skills/blob/main/skills/animate/SKILL.md): CSS para sequência predeterminada, transformação/opacidade, resposta curta dos controles e movimento reduzido. A abertura fica estática; o carrossel avança por ação, sem animação que atrase teclado ou altere foco.
- [Taste Skill](https://github.com/Leonxlnx/taste-skill): composição própria com um foco por área, ativos do projeto e inspeção no navegador. A paleta preta, branca e verde, o carrossel e os textos do contrato prevalecem sobre sugestões genéricas.

## Arquivos e decisões de implementação

| Arquivo | Bloco/função e motivo |
| --- | --- |
| `frontend/src/App.tsx` | `App`: substitui o starter, compõe navegação, Home, montagem, História e fluxo ativo. Mantém formulário antes da decoração no celular. |
| `frontend/src/content.ts` | `copy`: fonte única dos textos fixos; inclui mensagens de recuperação necessárias ao contrato. |
| `frontend/src/useRecipeSession.ts` | `useRecipeSession`, `restore`, `create`, `decide`, `refreshHistory`: coordenação de requisições, lock, ID ativo e recuperação. O histórico continua autoritativo na API. |
| `frontend/src/Impasse.tsx` | `Impasse`, `act`: valida ajustes, separa salvar/continuar/encerrar e preserva rascunhos após falhas. |
| `frontend/src/RecipeResult.tsx` | `RecipeResult`, `Proposal`, `RecipeImage`, `safeUrl`: receita, saúde, proposta, validação de URL e fallback de imagem. |
| `frontend/src/Gallery.tsx` | `Gallery`, `move`: janela circular de até três cards, sem clonar receitas, com teclado e gesto. |
| `frontend/src/index.css` | Tokens, tipografia, foco, campos e preferência por movimento reduzido. |
| `frontend/src/App.css` | Composição por área, montagem CSS e breakpoints. |
| `frontend/index.html` | Idioma pt-BR, título, descrição e símbolo da marca como favicon. |
| `frontend/vite.config.ts` | Mantém proxy padrão em 8000; variável `COXINH_API_TARGET` permite isolar testes em 8001. |
| `frontend/package.json`, `package-lock.json` | Playwright, axe e Prettier como dependências de desenvolvimento; scripts de teste. Nenhuma nova dependência de produção. |
| `frontend/playwright.config.ts` | Edge headless e servidores exclusivos em 5174/8001, sem reutilizar a API do usuário. |
| `frontend/tests/fixtures.ts` | Respostas e rotas simuladas para conflitos/falhas reproduzíveis. |
| `frontend/tests/flows.spec.ts` | Cenários de comportamento e navegação completa com API real e agentes simulados. |
| `frontend/tests/visual.spec.ts` | Capturas, revisão de overflow, teclado, axe, ampliação e transparência. |
| `tests/browser_api.py` | Servidor exclusivamente de teste; substitui agentes externos, preserva API e workflow de produção. |
| `frontend/public/assets/` | Quatro recortes, hero decorativo e cópias das duas imagens da turma; `README.md` registra origem, prompts e pendências. |
| `frontend/.gitignore` | Exclui relatórios temporários e traces de testes. |
| `README.md`, `frontend/README.md` | Execução e testes em PowerShell, limitações e dependências reais. |
| `docs/design/tasks.md` | Checklist atualizado conforme evidências; itens incompletos permanecem abertos. |
| `docs/design/review/` | Este relatório e capturas do navegador. |

`src/api.py`, `tests/test_api.py`, `pyproject.toml`, `frontend/src/recipeApi.ts` e `frontend/src/recipeTypes.ts` já existiam localmente e foram preservados. Os documentos `requirements.md` e as alterações locais em `design.md` também foram preservados. A separação em componentes é uma escolha de manutenção; os contratos e os comportamentos são requisitos. `retomada-mcp.patch` fica local e não entra no commit.

## Pendências para aceite

1. Finalizar e aprovar bordas dos quatro recortes e conferir fidelidade das marcas. Há alfa real e autorização de uso confirmada por João, mas o recorte generativo não certifica reprodução exata do original. O hero decorativo também pede aprovação visual final.
2. Selecionar a foto da dupla e a foto cenográfica do personagem fictício de saúde. Nenhuma delas foi inventada; o conteúdo está completo sem as fotos.
3. Integrar e validar a etapa 10.1 com imagem real da receita. O frontend já trata o contrato e as falhas, mas a geração real não foi testada nem implementada nesta etapa.
4. Revisão de Caio e aceite antes do merge. O PR deve permanecer rascunho enquanto os recortes não forem aprovados.

Publicação pendente: o commit local foi criado, mas a revisão automática de aprovação bloqueou o `git push` por exigir autorização explícita para publicar no repositório público `Caio-GBrayner/Coxinh.IA`. Nenhuma branch foi enviada e nenhum PR foi aberto. `retomada-mcp.patch` permanece fora do commit.

Limite adicional do contrato preservado: se o POST de criação for aceito e a resposta com ID se perder, a interface só pode consultar o histórico concluído; não recupera um Impasse cujo ID nunca recebeu. Não há reenvio automático. A recuperação integral desse caso exige uma evolução futura da API, não uma alteração silenciosa nesta etapa. Langfuse permanece fora do escopo.
