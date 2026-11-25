/** Os campos retornados pela API para a execução em andamento. */
export interface RecipeView {
    error?: string | null;
    thread_id: string;
    status:
        | "running"
        | "interrupted"
        | "awaiting_user"
        | "completed"
        | "cancelled"
        | "blocked"
        | "error";
    state_version?: number;
    critique?: string | null;
    /** Falso quando a conversa esgotou as retomadas: restam aceitar ou encerrar. */
    resume_allowed?: boolean;
    recipe?: ProposedRecipe | null;
    ingredient_additions?: string[];
    user_guidance?: string | null;
    final_response?: FinalResponse | null;
    /** Preenchido quando o guardrail recusou o pedido. */
    guardrail?: { code: string; message: string; reason: string | null } | null;
}

/** Proposta revisada pelo SubChef e mostrada durante um Impasse. */
export interface ProposedRecipe {
    dough: string;
    filling: string;
    ingredients: string[];
    preparation: string;
    utensils: string[];
    preparation_methods: string[];
}

/** Resultado final separado em receita, saúde e imagem. */
export interface FinalResponse {
    recipe: {
        title: string;
        subtitle: string;
        dough: string;
        filling: string;
        ingredients: string[];
        utensils: string[];
        preparation_methods: string[];
        steps: string[];
        image_prompt: string;
    };
    health: {
        warning: string | null;
        contraindications: string[];
        sources: Array<{ title: string; url: string }>;
        uncertainty: string | null;
        health_status: "pending" | "ok" | "insufficient" | "unavailable";
    };
    image: {
        status: string;
        url: string | null;
    };
    resource_validation: string;
}

/** Card salvo no histórico da sessão, com o ID da execução. */
export interface SavedRecipe {
    id: string;
    title: string | null;
    subtitle: string | null;
    image_url: string | null;
    image_status: string | null;
}

/** A ação e a versão necessárias para salvar ou retomar um Impasse. */
export interface DecisionRequest {
    action: "save" | "resume" | "accept" | "cancel";
    expected_state_version: number;
    idempotency_key: string;
    ingredient_additions?: string[];
    user_guidance?: string | null;
}
