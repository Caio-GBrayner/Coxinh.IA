import type { DecisionRequest, RecipeView, SavedRecipe } from './recipeTypes'

/** Erro HTTP que preserva o código para tratar conflitos de versão na tela. */
export class RecipeApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'RecipeApiError'
    this.status = status
  }
}

/** Consulta a API da sessão atual e transforma erros em mensagens legíveis. */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    credentials: 'same-origin',
    ...options,
  })

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null)
    const detail =
      body && typeof body === 'object' && 'detail' in body
        ? body.detail
        : null
    const message =
      typeof detail === 'string'
        ? detail
        : 'Não foi possível completar esta operação.'
    throw new RecipeApiError(response.status, message)
  }

  return (await response.json()) as T
}

/** Envia a ideia e recebe o estado da nova receita. */
export function createRecipe(rawInput: string): Promise<RecipeView> {
  return request<RecipeView>('/recipes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw_input: rawInput }),
  })
}

/** Recupera uma execução existente, inclusive quando aguarda decisão. */
export function getRecipe(threadId: string): Promise<RecipeView> {
  return request<RecipeView>(`/recipes/${encodeURIComponent(threadId)}`)
}

/** Lista as receitas concluídas que pertencem à sessão deste navegador. */
export function listRecipes(): Promise<SavedRecipe[]> {
  return request<SavedRecipe[]>('/recipes')
}

/** Aplica uma decisão humana no Impasse da execução indicada. */
export function submitDecision(
  threadId: string,
  decision: DecisionRequest,
): Promise<RecipeView> {
  return request<RecipeView>(
    `/recipes/${encodeURIComponent(threadId)}/decisions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(decision),
    },
  )
}
