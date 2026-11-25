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
| `blocked` | O guardrail recusou o pedido antes do Chef. `guardrail` traz o motivo. Comece um pedido novo. |
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
  "evidence": ["Itens adicionados no Impasse que a receita ainda não usa: queijo."],
  "resume_allowed": true,
  "ingredient_additions": [],
  "user_guidance": null,
  "final_response": null,
  "guardrail": null,
  "error": null
}
```

Enquanto `status` for `running`, só vêm `thread_id`, `status` e `error`. Em `completed`, `final_response` traz `recipe` (título, subtítulo, massa, recheio, listas, passos), `health` (aviso, contraindicações, fontes, incerteza e status) e `image`.

Em `blocked`, `guardrail` é `{"code", "message", "reason"}`: `message` é o texto completo para o usuário, já com o motivo. Códigos: `prompt_injection`, `guard_uncertain`, `guard_unavailable` e `input_too_long`.

`final_response.image.url` é um caminho da própria API (`/images/<arquivo>`) ou `null`. Referências simuladas nunca viram URL. Monte a URL completa com o endereço da API.

### `POST /recipes/{thread_id}/impasse`

Corpo igual ao `ImpasseDecision`:

| Campo | Tipo | Regra |
| --- | --- | --- |
| `action` | `save`, `resume`, `accept` ou `cancel` | |
| `expected_state_version` | inteiro ≥ 0 | O `state_version` lido em `GET /recipes/{thread_id}`. |
| `idempotency_key` | texto não vazio | Gerada pelo front para cada decisão (por exemplo, um UUID). |
| `ingredient_additions` | texto ou lista de textos | Aceita texto livre: vírgula, `;`, quebra de linha, "e" e marcadores de lista separam itens (`"queijo, carne e fogão"` vira três itens). `save` exige este campo ou `user_guidance`; `accept` e `cancel` não aceitam. |
| `user_guidance` | texto ou `null` | Mesma regra. |

| Ação | Resposta | O que acontece |
| --- | --- | --- |
| `save` | 200, estado atual | Guarda ingredientes e orientação. Continua em `awaiting_user`, com `state_version` + 1. |
| `cancel` | 200, estado atual | Encerra com `cancelled`. |
| `resume` | 202, `running` | O Chef cria uma nova proposta com o que foi salvo. |
| `accept` | 202, `running` | Aceita a receita rejeitada e segue para Cozinheiro, Saúde, Imagem e finalização. |

Repetir a mesma decisão com a mesma chave devolve 200 com o estado atual, sem executar de novo, inclusive depois de a API reiniciar.

**O Impasse não trava.** Se `resume` ou `accept` falhar no meio (erro do LLM ou de outro serviço), `GET /recipes/{thread_id}` volta a mostrar `awaiting_user`, com a explicação no começo de `critique` e o detalhe técnico em `error`. A próxima decisão, com uma chave nova e o `state_version` atual, é aplicada normalmente.

**Itens adicionados são comparados com tolerância:** sem diferença de acento ou maiúsculas, aceitando nome parcial (`queijo` casa com `queijo ralado`) e em qualquer lista da receita (`fogão` pode estar em utensílios). Quando falta algum, `critique` e `evidence` dizem qual.

**Limite de retomadas:** cada conversa tem até 4 ciclos de revisão. Depois disso `resume_allowed` fica `false` e `resume` responde 409 `resume_limit_reached`; `save`, `accept` e `cancel` continuam disponíveis.

**Guardrail.** Todo texto enviado numa decisão (`ingredient_additions` e `user_guidance`) é verificado antes de ser registrado. Um texto recusado responde 422 (ou 503, se a verificação estiver fora do ar), continua em `awaiting_user` e não gasta `state_version` nem `idempotency_key`. Num `resume` com texto, que roda em segundo plano, a recusa aparece em `error`.

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
| 409 | `resume_limit_reached` | Acabaram as retomadas desta conversa. Aceite ou encerre. |
| 422 | `prompt_injection`, `guard_uncertain`, `input_too_long` | O guardrail recusou o texto da decisão. |
| 503 | `guard_unavailable` | A verificação do guardrail falhou. Tente de novo. |
| 422 | — | Corpo inválido (campo ausente, ação desconhecida, combinação proibida). |

## Configuração

| Variável | Padrão | Uso |
| --- | --- | --- |
| `PERSISTENCE` | `sqlite` | `sqlite` sobrevive a reinícios; `memory` perde tudo ao encerrar. |
| `DATABASE_PATH` | `data/coxinh.db` | Receitas concluídas e decisões do Impasse. |
| `CHECKPOINT_DATABASE_PATH` | `data/checkpoints.db` | Checkpoints do LangGraph. |
| `IMAGE_STORAGE_DIR` | `data/images` | Pasta servida em `/images`. |
| `GUARD_ENABLED` | `true` | Só `false`, `0`, `no` ou `off` desligam o guardrail. |
| `GUARD_JUDGE_PROVIDER`, `GUARD_JUDGE_MODEL` | os do Chef | Provedor e modelo do juiz. |
| `GUARD_MAX_INPUT_CHARS` | `4000` | Tamanho máximo do texto verificado. |
| `GUARD_JUDGE_TIMEOUT_SECONDS` | `15` | Prazo de cada tentativa do juiz. |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Origens do front, separadas por vírgula. |

## Limites

- Um processo da API por vez. Vários processos sobre o mesmo banco não são suportados.
- Uma execução em `running` quando a API cai vira `interrupted`; ela não é retomada sozinha. Impasses em aberto (`awaiting_user`) sobrevivem a quedas.
- Sem autenticação: qualquer cliente que alcance a API pode criar receitas e decidir impasses.
