import { test, expect } from "@playwright/test";
import { copy } from "../src/content";
import { finalResponse, mockApi, view } from "./fixtures";

test("vazio, validação, envio único, montagem e resultado", async ({
    page,
}) => {
    const api = await mockApi(page, { delay: 700 });
    await page.goto("/");
    await expect(page.getByText(copy.noRecipes)).toBeVisible();
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await expect(page.getByText(copy.empty)).toBeVisible();
    await page.getByLabel(copy.input).fill("Frango com café");
    await page.locator(".idea-card").evaluate((form) => {
        form.dispatchEvent(
            new Event("submit", { bubbles: true, cancelable: true }),
        );
        form.dispatchEvent(
            new Event("submit", { bubbles: true, cancelable: true }),
        );
    });
    await expect(
        page.getByRole("heading", { name: copy.processing }),
    ).toBeVisible();
    await expect(
        page.getByRole("button", { name: copy.processing, exact: true }),
    ).toBeDisabled();
    await expect(
        page.getByRole("heading", { name: finalResponse.recipe.title }),
    ).toBeVisible();
    expect(api.creates).toBe(1);
    await expect(page.getByText(copy.imageSimulated).first()).toBeVisible();
    await expect(page.getByText(copy.imageCredit)).toHaveCount(0);
    await expect(page.locator(".recipe-card")).toHaveCount(1);
    await expect(page.getByRole("button", { name: copy.next })).toBeDisabled();
});

test("Impasse salva sem retomar, restaura o ID e continua", async ({
    page,
}) => {
    const api = await mockApi(page, { createStatus: "awaiting_user" });
    await page.goto("/");
    await page.getByLabel(copy.input).fill("Coxinha improvável");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await page.getByRole("button", { name: copy.save }).click();
    await expect(page.getByText(copy.saveEmpty)).toBeVisible();
    expect(api.decisions).toHaveLength(0);
    await page.getByLabel(copy.guidance).fill("Usar menos café");
    await page.getByLabel(copy.additions, { exact: true }).fill("queijo\n\n");
    await page.getByRole("button", { name: copy.resume }).click();
    await expect(page.getByText(copy.unsaved)).toBeVisible();
    await page.getByRole("button", { name: copy.save }).click();
    await expect(page.getByText(copy.saved)).toBeVisible();
    expect(api.decisions[0]).toMatchObject({
        action: "save",
        expected_state_version: 0,
        ingredient_additions: ["queijo"],
        user_guidance: "Usar menos café",
    });
    await page.reload();
    await expect(
        page.getByRole("heading", { name: copy.impasse }),
    ).toBeVisible();
    await expect(
        page.getByText("Usar menos café", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: copy.resume }).click();
    await expect(
        page.getByRole("heading", { name: finalResponse.recipe.title }),
    ).toBeVisible();
    expect(api.decisions[1]).toMatchObject({
        action: "resume",
        expected_state_version: 1,
    });
    expect(api.decisions[1].idempotency_key).not.toBe(
        api.decisions[0].idempotency_key,
    );
    expect(api.creates).toBe(1);
});

test("409 consulta estado e mantém o rascunho até nova decisão", async ({
    page,
}) => {
    const api = await mockApi(page, {
        createStatus: "awaiting_user",
        conflict: true,
    });
    await page.goto("/");
    await page.getByLabel(copy.input).fill("Frango");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await page.getByLabel(copy.guidance).fill("Meu ajuste");
    await page.getByRole("button", { name: copy.save }).click();
    await expect(page.getByText(copy.conflict)).toBeVisible();
    await expect(page.getByLabel(copy.guidance)).toHaveValue("Meu ajuste");
    await expect(
        page.getByText("Orientação aceita em outra aba."),
    ).toBeVisible();
    expect(api.decisions).toHaveLength(1);
    expect(api.reads).toBe(1);
    await page.getByRole("button", { name: copy.save }).click();
    await expect(page.getByText(copy.saved)).toBeVisible();
    expect(api.decisions[1].expected_state_version).toBe(7);
});

test("cancelar é explícito e não entra no histórico", async ({ page }) => {
    const api = await mockApi(page, { createStatus: "awaiting_user" });
    await page.goto("/");
    await page.getByLabel(copy.input).fill("Frango");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await page.getByRole("button", { name: copy.cancel }).click();
    await expect(
        page.getByRole("heading", { name: copy.cancelled }),
    ).toBeVisible();
    expect(api.decisions[0].action).toBe("cancel");
    await expect(page.locator(".recipe-card")).toHaveCount(0);
});

test("404 na restauração não inicia outro POST", async ({ page }) => {
    const api = await mockApi(page, { missing: true });
    await page.addInitScript(() =>
        sessionStorage.setItem("coxinh.activeThread", "old-thread"),
    );
    await page.goto("/");
    await expect(page.getByText(copy.unavailable)).toBeVisible();
    expect(api.creates).toBe(0);
});

test("falha de criação preserva entrada e consulta histórico sem repetir", async ({
    page,
}) => {
    const api = await mockApi(page, { networkCreate: true });
    await page.goto("/");
    await page.getByLabel(copy.input).fill("Minha ideia");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await expect(page.getByText(copy.unknownCreation)).toBeVisible();
    await expect(page.getByLabel(copy.input)).toHaveValue("Minha ideia");
    expect(api.creates).toBe(1);
});

test("falha de decisão consulta a execução e conserva orientação", async ({
    page,
}) => {
    const api = await mockApi(page, {
        createStatus: "awaiting_user",
        networkDecision: true,
    });
    await page.goto("/");
    await page.getByLabel(copy.input).fill("Frango");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await page.getByLabel(copy.guidance).fill("Preservar isto");
    await page.getByRole("button", { name: copy.save }).click();
    await expect(page.getByText(copy.failure)).toBeVisible();
    await expect(page.getByLabel(copy.guidance)).toHaveValue("Preservar isto");
    expect(api.decisions).toHaveLength(1);
    expect(api.reads).toBe(1);
});

test("carrossel circular, teclado, deslize e posição ao voltar", async ({
    page,
}) => {
    const history = [1, 2, 3, 4].map((id) => ({
        ...structuredClone(finalResponse),
        id: String(id),
        recipe: { ...finalResponse.recipe, title: `Coxinha ${id}` },
    }));
    await mockApi(page, { history });
    await page.goto("/");
    const cards = page.locator(".recipe-card");
    await expect(cards.first()).toHaveAccessibleName(
        "Abrir receita: Coxinha 4",
    );
    await page.getByRole("button", { name: copy.previous }).click();
    await expect(cards.first()).toHaveAccessibleName(
        "Abrir receita: Coxinha 1",
    );
    const carousel = page.locator(".carousel");
    await carousel.focus();
    await page.keyboard.press("ArrowRight");
    await expect(cards.first()).toHaveAccessibleName(
        "Abrir receita: Coxinha 4",
    );
    await carousel.dispatchEvent("touchstart", {
        touches: [{ identifier: 1, clientX: 280, clientY: 100 }],
    });
    await carousel.dispatchEvent("touchend", {
        changedTouches: [{ identifier: 1, clientX: 80, clientY: 102 }],
    });
    await expect(cards.first()).toHaveAccessibleName(
        "Abrir receita: Coxinha 3",
    );
    await cards.first().click();
    await expect(
        page.getByRole("heading", { name: "Coxinha 3", exact: true }),
    ).toBeVisible();
    await page.getByRole("link", { name: copy.back }).click();
    await expect(cards.first()).toHaveAccessibleName(
        "Abrir receita: Coxinha 3",
    );
    expect(await cards.count()).toBe(3);
});

for (const state of ["pending", "failed", "broken", "generated", "reused"]) {
    test(`imagem ${state} e URLs de fontes seguras`, async ({ page }) => {
        const initial = view("completed");
        initial.final_response!.image = {
            status: state === "broken" ? "generated" : state,
            url: "https://images.example.test/recipe.png",
        };
        initial.final_response!.health.sources.push({
            title: "<script>alert(1)</script>",
            url: "javascript:alert(1)",
        });
        await mockApi(page, { initial });
        await page.route("https://images.example.test/**", (route) =>
            state === "broken"
                ? route.abort()
                : route.fulfill({
                      path: "public/assets/coxinha-hero.png",
                      contentType: "image/png",
                  }),
        );
        await page.addInitScript(() =>
            sessionStorage.setItem("coxinh.activeThread", "thread-1"),
        );
        await page.goto("/");
        if (["generated", "reused"].includes(state))
            await expect(page.getByText(copy.imageCredit)).toBeVisible();
        else
            await expect(
                page.getByText(
                    state === "pending" ? copy.imagePending : copy.noImage,
                ),
            ).toBeVisible();
        await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0);
        await expect(
            page.getByText("<script>alert(1)</script>", { exact: false }),
        ).toBeVisible();
        await expect(page.locator(".health a")).toHaveAttribute(
            "rel",
            "noopener noreferrer",
        );
    });
}

test("API real pelo proxy: sessão vazia, Impasse, salvar, recarregar e duas receitas", async ({
    page,
}) => {
    await page.goto("/");
    await expect(page.getByText(copy.noRecipes)).toBeVisible();
    const response = await page.request.get("/api/recipes");
    expect(await response.json()).toEqual([]);
    await page.getByLabel(copy.input).fill("impasse de teste");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await expect(
        page.getByRole("heading", { name: copy.impasse }),
    ).toBeVisible();
    const id = await page.evaluate(() =>
        sessionStorage.getItem("coxinh.activeThread"),
    );
    await page.getByLabel(copy.guidance).fill("Ajustar o preparo");
    await page.getByRole("button", { name: copy.save }).click();
    await expect(page.getByText(copy.saved)).toBeVisible();
    await page.reload();
    await expect(
        page.getByText("Ajustar o preparo", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: copy.resume }).click();
    await expect(
        page.getByRole("heading", { name: "Coxinha de teste da cozinha" }),
    ).toBeVisible();
    expect(
        await page.evaluate(() =>
            sessionStorage.getItem("coxinh.activeThread"),
        ),
    ).toBe(id);
    await page.getByRole("link", { name: copy.another }).click();
    await page.getByLabel(copy.input).fill("Segunda coxinha");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await expect(page.locator(".recipe-card")).toHaveCount(2);
    const history = await (await page.request.get("/api/recipes")).json();
    expect(history).toHaveLength(2);
    expect(new Set(history.map((item: { id: string }) => item.id)).size).toBe(
        2,
    );
});
