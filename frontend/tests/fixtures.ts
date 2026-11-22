import type { Page } from "@playwright/test";
import type {
    RecipeView,
    SavedRecipe,
    FinalResponse,
    DecisionRequest,
} from "../src/recipeTypes";

export const finalResponse: FinalResponse = {
    recipe: {
        title: "Coxinha de frango e café",
        subtitle: "Uma combinação que virou história.",
        dough: "Massa de batata",
        filling: "Frango com café",
        ingredients: ["batata", "frango", "café"],
        utensils: ["panela"],
        preparation_methods: ["cozimento"],
        steps: ["Prepare a massa.", "Recheie e modele."],
        image_prompt: "Coxinha dourada",
    },
    health: {
        warning: "Observe os ingredientes e as restrições de consumo.",
        contraindications: ["Contém cafeína."],
        uncertainty: "Sem avaliação individual.",
        health_status: "insufficient",
        sources: [
            { title: "Fonte de teste", url: "https://example.com/fonte" },
        ],
    },
    image: { status: "generated", url: "simulated://test" },
    resource_validation: "valid",
};
export function view(
    status: RecipeView["status"] = "awaiting_user",
    id = "thread-1",
): RecipeView {
    return {
        thread_id: id,
        status,
        state_version: 0,
        revision_count: 2,
        max_revisions: 2,
        critique: "Ajuste o preparo desta combinação.",
        recipe: { ...finalResponse.recipe, preparation: "Prepare a massa." },
        ingredient_additions: [],
        user_guidance: null,
        final_response:
            status === "completed" ? structuredClone(finalResponse) : null,
    };
}
export async function mockApi(
    page: Page,
    options: {
        initial?: RecipeView;
        history?: SavedRecipe[];
        createStatus?: RecipeView["status"];
        delay?: number;
        conflict?: boolean;
        missing?: boolean;
        networkCreate?: boolean;
        networkDecision?: boolean;
    } = {},
) {
    let current = options.initial || view(options.createStatus || "completed");
    let history = options.history || [];
    let creates = 0;
    let reads = 0;
    const decisions: DecisionRequest[] = [];
    await page.route("**/api/recipes**", async (route) => {
        const req = route.request();
        const path = new URL(req.url()).pathname;
        if (path.endsWith("/decisions")) {
            const body = req.postDataJSON() as DecisionRequest;
            decisions.push(body);
            if (options.networkDecision) {
                await route.abort();
                return;
            }
            if (options.conflict && decisions.length === 1) {
                current = {
                    ...current,
                    state_version: 7,
                    user_guidance: "Orientação aceita em outra aba.",
                };
                await route.fulfill({
                    status: 409,
                    json: { detail: "Conflict" },
                });
                return;
            }
            current = {
                ...current,
                state_version: current.state_version + 1,
                status:
                    body.action === "save"
                        ? "awaiting_user"
                        : body.action === "cancel"
                          ? "cancelled"
                          : "completed",
                ingredient_additions: [
                    ...current.ingredient_additions,
                    ...(body.ingredient_additions || []),
                ],
                user_guidance: body.user_guidance || current.user_guidance,
            };
            if (current.status === "completed") {
                current.final_response = structuredClone(finalResponse);
                history.push({
                    id: current.thread_id,
                    ...current.final_response,
                });
            }
            await route.fulfill({ json: current });
            return;
        }
        if (path === "/api/recipes" && req.method() === "POST") {
            creates++;
            if (options.delay)
                await new Promise((resolve) =>
                    setTimeout(resolve, options.delay),
                );
            if (options.networkCreate) {
                await route.abort();
                return;
            }
            current = view(
                options.createStatus || "completed",
                `thread-${creates}`,
            );
            if (current.final_response)
                history.push({
                    id: current.thread_id,
                    ...current.final_response,
                });
            await route.fulfill({ status: 201, json: current });
            return;
        }
        if (path === "/api/recipes") {
            await route.fulfill({ json: history });
            return;
        }
        reads++;
        if (options.missing) {
            await route.fulfill({
                status: 404,
                json: { detail: "Receita não encontrada." },
            });
            return;
        }
        await route.fulfill({ json: current });
    });
    return {
        decisions,
        get creates() {
            return creates;
        },
        get reads() {
            return reads;
        },
    };
}
