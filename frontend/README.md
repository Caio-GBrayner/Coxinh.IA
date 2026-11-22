# Frontend Coxinh.IA

React, TypeScript e Vite. Os contratos existentes estão em `src/recipeApi.ts` e `src/recipeTypes.ts`; os textos editoriais em `src/content.ts`.

A partir desta pasta, em PowerShell:

```powershell
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

A API deve estar disponível em `127.0.0.1:8000`; consulte o [README principal](../README.md) para configurar o backend.

```powershell
npm.cmd run build
npm.cmd run lint
npm.cmd test
npm.cmd run test:visual
```

A suíte usa Edge headless, portas isoladas 5174/8001 e a API de teste com os mesmos endpoints e workflow, substituindo somente agentes externos. As capturas ficam em `../docs/design/review/`. O HTML detalhado de testes fica em `playwright-report/`, ignorado pelo Git.

`COXINH_API_TARGET` permite alterar o destino do proxy nos testes; sem essa variável, o destino continua 8000. Não use `tests/browser_api.py` como API de produção.

Histórico é do servidor, em memória. Na aba são guardados apenas o ID da execução e a posição do carrossel. A interface não repete POSTs automaticamente. Os recortes e as fotos pendentes estão documentados em [ativos](public/assets/README.md).
