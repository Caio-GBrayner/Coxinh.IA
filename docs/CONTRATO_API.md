# Contrato da API HTTP do Coxinh.IA

Porta de entrada do front. Implementação em `src/api/app.py`. O contrato completo e interativo fica em `/docs` (OpenAPI) com a API rodando.

```bash
uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8081
```

## Como o front usa

1. `POST /recipes` com o pedido. A resposta vem na hora com o `thread_id` e `status: "running"`.
2. Consultar `GET /recipes/{thread_id}` a cada 1 ou 2 segundos até o `status` sair de `running`.
3. Se `status` for `awaiting_user`, mostrar o Impasse e enviar a decisão para `POST /recipes/{thread_id}/impasse`.
4. Se `status` for `completed`, mostrar `final_response`. A imagem fica em `final_response.image.url`.
5. O carrossel usa `GET /recipes`.

## Status

| Status | Significado |
| --- | --- |
| `running` | Os agentes estão trabalhando. Não aceite decisões nesse estado. |
| `awaiting_user` | Impasse: o SubChef rejeitou a receita e aguarda uma decisão. |
| `completed` | Receita pronta, com `final_response`. |
| `cancelled` | O usuário encerrou no Impasse. |
| `error` | A execução falhou; `error` traz a mensagem. Comece um pedido novo. |
| `interrupted` | A execução parou no meio (por exemplo, a API caiu durante a geração). Comece um pedido novo. |

## Rotas

### `POST /recipes` → 202

Corpo: `{"raw_input": "texto livre com ingredientes e preparo"}` (1 a 4000 caracteres).

Resposta: `{"thread_id": "rcp-...", "status": "running"}`.

### `GET /recipes/{thread_id}` → 200

```json
{
  "thread_id": "rcp-...",
  "status": "awaiting_user",
  "state_version": 0,
  "recipe": {"dough": "...", "filling": "...", "ingredients": ["..."], "preparation": "...", "utensils": [], "preparation_methods": []},
  "critique": "Crítica do SubChef quando a receita foi rejeitada, senão null",
  "ingredient_additions": [],
  "user_guidance": null,
  "final_response": null,
  "error": null
}
```

Enquanto `status` for `running`, só vêm `thread_id`, `status` e `error`. Em `completed`, `final_response` traz `recipe` (título, subtítulo, massa, recheio, listas, passos), `health` (aviso, contraindicações, fontes, incerteza e status) e `image`.

`final_response.image.url` é um caminho da própria API (`/images/<arquivo>`) ou `null`. Referências simuladas nunca viram URL. Monte a URL completa com o endereço da API.

### `POST /recipes/{thread_id}/impasse`

Corpo igual ao `ImpasseDecision`:

| Campo | Tipo | Regra |
| --- | --- | --- |
| `action` | `save`, `resume`, `accept` ou `cancel` | |
| `expected_state_version` | inteiro ≥ 0 | O `state_version` lido em `GET /recipes/{thread_id}`. |
| `idempotency_key` | texto não vazio | Gerada pelo front para cada decisão (por exemplo, um UUID). |
| `ingredient_additions` | lista de textos | `save` exige este campo ou `user_guidance`; `accept` e `cancel` não aceitam. |
| `user_guidance` | texto ou `null` | Mesma regra. |

| Ação | Resposta | O que acontece |
| --- | --- | --- |
| `save` | 200, estado atual | Guarda ingredientes e orientação. Continua em `awaiting_user`, com `state_version` + 1. |
| `cancel` | 200, estado atual | Encerra com `cancelled`. |
| `resume` | 202, `running` | O Chef cria uma nova proposta com o que foi salvo. |
| `accept` | 202, `running` | Aceita a receita rejeitada e segue para Cozinheiro, Saúde, Imagem e finalização. |

Repetir a mesma decisão com a mesma chave devolve 200 com o estado atual, sem executar de novo, inclusive depois de a API reiniciar.

### `GET /recipes` → 200

Receitas concluídas, da mais recente para a mais antiga. O carrossel é global (todos veem a mesma lista).

```json
{"items": [{"id": "rcp-...", "title": "...", "subtitle": "...", "image_url": "/images/abc.png", "image_status": "generated"}]}
```

### `GET /images/{arquivo}` → 200

Serve a imagem gravada pelo provedor. Aceita só nomes simples (`[A-Za-z0-9_-]` mais `.png`, `.jpg`, `.jpeg`, `.webp` ou `.svg`). Qualquer outro nome, ou arquivo ausente, devolve 404.

### `GET /health` → 200

`{"status": "ok"}`.

## Erros

Formato: `{"detail": {"code": "...", "message": "..."}}`. Erros de validação do corpo (422) seguem o formato padrão do FastAPI.

| HTTP | `code` | Quando |
| --- | --- | --- |
| 404 | `workflow_not_found` | `thread_id` inexistente. |
| 404 | `image_not_found` | Imagem ausente ou nome inválido. |
| 409 | `workflow_running` | Decisão enviada enquanto a receita está em `running`. |
| 409 | `workflow_not_paused` | A receita não está em `awaiting_user`. |
| 409 | `state_version_conflict` | `expected_state_version` diferente da versão atual. Releia o estado. |
| 409 | `idempotency_key_reuse` | A mesma chave foi usada com outro conteúdo. |
| 422 | — | Corpo inválido (campo ausente, ação desconhecida, combinação proibida). |

## Configuração

| Variável | Padrão | Uso |
| --- | --- | --- |
| `PERSISTENCE` | `sqlite` | `sqlite` sobrevive a reinícios; `memory` perde tudo ao encerrar. |
| `DATABASE_PATH` | `data/coxinh.db` | Receitas concluídas e decisões do Impasse. |
| `CHECKPOINT_DATABASE_PATH` | `data/checkpoints.db` | Checkpoints do LangGraph. |
| `IMAGE_STORAGE_DIR` | `data/images` | Pasta servida em `/images`. |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Origens do front, separadas por vírgula. |

## Limites

- Um processo da API por vez. Vários processos sobre o mesmo banco não são suportados.
- Uma execução em `running` quando a API cai vira `interrupted`; ela não é retomada sozinha. Impasses em aberto (`awaiting_user`) sobrevivem a quedas.
- Sem autenticação: qualquer cliente que alcance a API pode criar receitas e decidir impasses.
