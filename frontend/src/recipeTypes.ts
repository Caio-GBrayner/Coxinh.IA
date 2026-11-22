/** Os campos retornados pela API para a execução em andamento. */
export interface RecipeView {
  thread_id: string
  status: 'in_revision' | 'approved' | 'awaiting_user' | 'completed' | 'cancelled' | 'error'
  state_version: number
  revision_count: number
  max_revisions: number
  critique: string | null
  recipe: ProposedRecipe | null
  ingredient_additions: string[]
  user_guidance: string | null
  final_response: FinalResponse | null
}

/** Proposta revisada pelo SubChef e mostrada durante um Impasse. */
export interface ProposedRecipe {
  dough: string
  filling: string
  ingredients: string[]
  preparation: string
  utensils: string[]
  preparation_methods: string[]
}

/** Resultado final separado em receita, saúde e imagem. */
export interface FinalResponse {
  recipe: {
    title: string
    subtitle: string
    dough: string
    filling: string
    ingredients: string[]
    utensils: string[]
    preparation_methods: string[]
    steps: string[]
    image_prompt: string
  }
  health: {
    warning: string | null
    contraindications: string[]
    sources: Array<{ title: string; url: string }>
    uncertainty: string | null
    health_status: 'pending' | 'ok' | 'insufficient' | 'unavailable'
  }
  image: {
    status: string
    url: string | null
  }
  resource_validation: string
}

/** Card salvo no histórico da sessão, com o ID da execução. */
export type SavedRecipe = FinalResponse & { id: string }

/** A ação e a versão necessárias para salvar ou retomar um Impasse. */
export interface DecisionRequest {
  action: 'save' | 'resume' | 'cancel'
  expected_state_version: number
  idempotency_key: string
  ingredient_additions?: string[]
  user_guidance?: string | null
}
