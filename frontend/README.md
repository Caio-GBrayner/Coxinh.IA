# Frontend Coxinh.IA

React, TypeScript e Vite. Os contratos existentes estão em `src/recipeApi.ts` e `src/recipeTypes.ts`; os textos editoriais em `src/content.ts`.

A partir desta pasta, em PowerShell:

```powershell
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

A API deve estar disponível em `127.0.0.1:8080`; consulte o [README principal](../README.md) para configurar o backend.

```powershell
npm.cmd run build
npm.cmd run lint
npm.cmd test
npm.cmd run test:visual
```

A suíte usa Edge headless, portas isoladas 5174/8001 e a API de teste com os mesmos endpoints e workflow, substituindo somente agentes externos. As capturas ficam em `../docs/design/review/`. O HTML detalhado de testes fica em `playwright-report/`, ignorado pelo Git.

`COXINH_API_TARGET` permite alterar o destino do proxy nos testes; sem essa variável, o destino continua 8080. Não use `tests/browser_api.py` como API de produção.

Histórico é do servidor, em memória. Na aba são guardados apenas o ID da execução e a posição do carrossel. A interface não repete POSTs automaticamente. Os recortes e as fotos pendentes estão documentados em [ativos](public/assets/README.md).

O proxy `/api` remove o prefixo antes de encaminhar à API oficial. Em produção, configure o mesmo proxy ou informe a URL pública antes do build:

```powershell
$env:VITE_API_URL = "http://127.0.0.1:8080"
npm.cmd run build
```

`VITE_API_URL` não contém `/recipes`: é a base comum para receitas e `/images`. Configure `CORS_ORIGINS` no backend para a origem exata do frontend. A API roda com `uvicorn src.api.app:create_app --factory`. O carrossel é global e o cliente acompanha execuções por polling; não usa cookie de sessão.
