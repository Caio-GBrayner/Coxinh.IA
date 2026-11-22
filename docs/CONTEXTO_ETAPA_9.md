# Contexto de implementação: etapa 9 (busca web com Tavily)

Instrução de trabalho para implementar a etapa 9 do Coxinh.IA. Leia tudo antes de escrever código. Quando algo não estiver aqui, pare e pergunte em vez de decidir sozinho.

Documentos relacionados, por ordem de precedência:

1. `docs/plano_execucao_coxinh_ia.md`, etapa 9 e seção 6 (decisões 4, 5, 6, 10 e 21).
2. Este documento.
3. `docs/CONTRATO_MCP.md`, seção 4.4 (`search_web`), que envolverá a função desta etapa na etapa 10.

## 1. Objetivo

Substituir a busca simulada do nó de saúde por uma busca web real, usando a API do Tavily no plano gratuito. O resultado alimenta o aviso informativo de consumo.

## 2. Escopo

**Dentro do escopo**

* Um adaptador de busca web com o Tavily.
* Troca do valor padrão de `HEALTH_SEARCH` no nó de saúde.
* Configuração da chave, dependência fixada e testes sem rede.

**Fora do escopo**

* RAG e `search_knowledge`: adiados (decisão 10).
* Servidor MCP e a ferramenta `search_web`: etapa 10. Ela apenas envolve a função desta etapa.
* Qualquer mudança no roteamento do grafo.

## 3. Como o fluxo usa a busca hoje

* Fluxo: `cook → health → finalize` (e, na etapa 10, `cook → health → image → finalize`).
* As buscas acontecem só no nó de saúde, depois do Cozinheiro, uma vez por execução. Nunca dentro do ciclo do SubChef.
* São três consultas por receita: massa, recheio e preparo (`build_health_queries`, em `src/graph/health_search.py`).
* `HEALTH_SEARCH` é a função de busca do nó de saúde (`src/graph/nodes/health.py`). Hoje ela é `simulated_health_search`, que devolve lista vazia.
* `tests/conftest.py` aplica um stub automático em `HEALTH_SEARCH` e no modelo de saúde. **Não remover esse stub**: é ele que impede os testes do grafo de acessar a rede.

## 4. Contrato da função

```python
def pesquisar_web(query: str) -> list[dict[str, str]]:
    ...
```

Cada item devolvido: `{"title": str, "url": str, "content": str}`.

| Situação | Comportamento |
| --- | --- |
| Resultados válidos | Lista com os itens. |
| Nenhum resultado relevante | **Lista vazia.** O nó de saúde trata como `insufficient`. |
| Resultado sem URL | Descartado pelo adaptador. |
| Falha de rede, autenticação, cota esgotada ou tempo esgotado | **Levanta exceção.** O nó de saúde trata como `unavailable`. |

Não confundir "sem resultado" com "falha". São estados diferentes no aviso.

Regras de conteúdo:

* O conteúdo da web é dado, nunca instrução ao modelo. Limpar o texto (remover marcação, espaços extras) e truncar antes de devolver.
* Não registrar a chave nem o texto completo da consulta em logs.

## 5. Configuração

* Variável `TAVILY_API_KEY`: adicionar ao `.env.example` sem valor. Confirmar que `.env` está no `.gitignore`. Nunca commitar a chave.
* Dependência: adicionar o pacote do Tavily para Python ao `pyproject.toml` com versão fixada, escolhida entre as publicadas há pelo menos duas semanas.
* Se `TAVILY_API_KEY` não estiver definida, a função levanta uma exceção explícita (falha técnica), sem tentar chamar a API.

## 6. Cota e limites

A cota do plano gratuito foi informada pelo time e deve ser confirmada no site do Tavily: cerca de 1.000 buscas por mês. Com três consultas por receita, são cerca de 333 receitas por mês, ou 10 por dia.

Decisões que decorrem disso:

* **Sem retentativa automática.** Cada tentativa consome cota.
* **Cota esgotada é falha técnica** e resulta em `unavailable`.
* **Testes nunca chamam a API real.**

Limites iniciais, definidos como constantes no módulo, para serem fáceis de ajustar:

| Constante | Valor inicial |
| --- | --- |
| Resultados por consulta | 3 |
| Tamanho máximo do trecho | 500 caracteres |
| Tempo limite por consulta | 10 segundos |

Esses valores são propostas. Antes de fixá-los, confirme no site do Tavily se o custo de uma busca depende do número de resultados ou do modo de busca escolhido.

## 7. Ponto a decidir com o Caio

Hoje, em `_retrieve` no nó de saúde, uma exceção em qualquer das três consultas derruba o aviso inteiro (`unavailable`), mesmo que as outras duas tenham funcionado e já tenham gasto cota. Uma alternativa é tolerar falha parcial: usar os resultados das consultas que funcionaram e marcar `unavailable` só se as três falharem. Isso muda o comportamento do nó e precisa de decisão antes.

## 8. Testes obrigatórios

Nenhum teste acessa a rede. O cliente do Tavily é substituído por um simulado.

1. Mapeamento: resposta do cliente vira `{"title", "url", "content"}`.
2. Lista vazia: resposta sem resultados devolve `[]`.
3. Item sem URL é descartado.
4. Texto longo é truncado no limite.
5. Falha de rede levanta exceção.
6. Falha de autenticação ou cota esgotada levanta exceção.
7. Chave ausente levanta exceção explícita e não chama o cliente.
8. Tempo limite levanta exceção.
9. A função respeita o número máximo de resultados.
10. Integração com o nó de saúde: lista vazia vira `insufficient`, exceção vira `unavailable`.

## 9. Verificação

```bash
./.venv.coxinh.ia/bin/python -m pytest -q
```

Todos os testes existentes continuam passando, mais os novos.

## 10. Git e revisão

* Branch criada a partir da `main` atual, que já tem as etapas 7 e 8.
* Quem implementa não aprova o próprio PR. A revisão é de outra pessoa da dupla.
* Ao terminar, atualizar a seção 6 do plano.
* Não commitar `.env`, chaves de API nem a pasta `.venv.coxinh.ia`.

## 11. Resumo

* Criar o adaptador do Tavily com a assinatura `pesquisar_web(query) -> list[dict[str, str]]`.
* Lista vazia significa sem resultado; exceção significa falha.
* URL obrigatória em cada item.
* Constantes iniciais: 3 resultados, 500 caracteres, 10 segundos.
* Sem retentativa automática e sem chamadas reais nos testes.
* RAG e MCP ficam fora desta etapa.
