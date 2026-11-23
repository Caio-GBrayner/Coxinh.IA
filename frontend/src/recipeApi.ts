import type { DecisionRequest, RecipeView, SavedRecipe } from "./recipeTypes";

// Empty configuration uses the Vite/reverse proxy; explicit URL supports separate hosting.
export const apiBase = (import.meta.env.VITE_API_URL || "/api").replace(
    /\/+$/,
    "",
);

export function recipeImageUrl(
    value: string | null | undefined,
): string | null {
    if (
        !value ||
        !/^\/images\/[A-Za-z0-9_-]{1,128}\.(png|jpg|jpeg|webp|svg)$/.test(value)
    )
        return null;
    try {
        const url = new URL(`${apiBase}${value}`, window.location.origin);
        return ["http:", "https:"].includes(url.protocol) ? url.href : null;
    } catch {
        return null;
    }
}

/** Erro HTTP que preserva o código para tratar conflitos de versão na tela. */
export class RecipeApiError extends Error {
    readonly status: number;
    readonly code?: string;

    constructor(status: number, message: string, code?: string) {
        super(message);
        this.name = "RecipeApiError";
        this.status = status;
        this.code = code;
    }
}

/** Consulta a API oficial e transforma erros em mensagens legíveis. */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${apiBase}${path}`, {
        credentials: "same-origin",
        ...options,
    });

    if (!response.ok) {
        const body: unknown = await response.json().catch(() => null);
        const detail =
            body && typeof body === "object" && "detail" in body
                ? body.detail
                : null;
        const message =
            typeof detail === "string"
                ? detail
                : detail && typeof detail === "object" && "message" in detail
                  ? String(detail.message)
                  : Array.isArray(detail)
                    ? "Dados inválidos. Confira os campos enviados."
                    : "Não foi possível completar esta operação.";
        const code =
            detail && typeof detail === "object" && "code" in detail
                ? String(detail.code)
                : undefined;
        throw new RecipeApiError(response.status, message, code);
    }

    return (await response.json()) as T;
}

/** Envia a ideia e recebe o estado da nova receita. */
export function createRecipe(rawInput: string): Promise<RecipeView> {
    return request<RecipeView>("/recipes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_input: rawInput }),
    });
}

/** Recupera uma execução existente, inclusive quando aguarda decisão. */
export function getRecipe(threadId: string): Promise<RecipeView> {
    return request<RecipeView>(`/recipes/${encodeURIComponent(threadId)}`);
}

/** Lista resumos globais, mais recentes primeiro. */
export async function listRecipes(): Promise<SavedRecipe[]> {
    return (await request<{ items: SavedRecipe[] }>("/recipes")).items;
}

/** Aplica uma decisão humana no Impasse da execução indicada. */
export function submitDecision(
    threadId: string,
    decision: DecisionRequest,
): Promise<RecipeView> {
    return request<RecipeView>(
        `/recipes/${encodeURIComponent(threadId)}/impasse`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(decision),
        },
    );
}
