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

test("aceitar proposta ignora rascunho não salvo e segue ao resultado", async ({
    page,
}) => {
    const api = await mockApi(page, { createStatus: "awaiting_user" });
    await page.goto("/");
    await page.getByLabel(copy.input).fill("Coxinha improvável");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await page.getByLabel(copy.guidance).fill("Rascunho não salvo");
    await page.getByLabel(copy.additions, { exact: true }).fill("queijo");
    await page.getByRole("button", { name: copy.accept }).click();

    await expect(
        page.getByRole("heading", { name: finalResponse.recipe.title }),
    ).toBeVisible();
    expect(api.decisions).toHaveLength(1);
    expect(api.decisions[0].action).toBe("accept");
    expect(api.decisions[0]).not.toHaveProperty("ingredient_additions");
    expect(api.decisions[0]).not.toHaveProperty("user_guidance");
    await expect(page.getByText(copy.health)).toBeVisible();
    await expect(page.locator(".recipe-card")).toHaveCount(1);
});

test("aceitar fica desabilitado quando a proposta não existe", async ({
    page,
}) => {
    const initial = view("awaiting_user");
    initial.recipe = null;
    await mockApi(page, { initial });
    await page.addInitScript(() =>
        sessionStorage.setItem("coxinh.activeThread", "thread-1"),
    );
    await page.goto("/");
    await expect(
        page.getByRole("button", { name: copy.accept }),
    ).toBeDisabled();
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
    expect(api.reads).toBeGreaterThanOrEqual(3);
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
    expect(api.reads).toBeGreaterThanOrEqual(3);
});

test("carrossel circular pelas setas e posição ao voltar", async ({
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
    await page.getByRole("button", { name: copy.next }).click();
    await expect(cards.first()).toHaveAccessibleName(
        "Abrir receita: Coxinha 4",
    );
    await page.getByRole("button", { name: copy.next }).click();
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

test("rolagem da página não passa o carrossel; as setas avançam", async ({
    page,
}) => {
    const history = [1, 2, 3, 4].map((id) => ({
        ...structuredClone(finalResponse),
        id: String(id),
        recipe: { ...finalResponse.recipe, title: `Coxinha ${id}` },
    }));
    await mockApi(page, { history });
    await page.goto("/");

    const galleryPosition = page.locator(".gallery .hint");
    await expect(galleryPosition).toContainText("1");
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await expect(galleryPosition).toContainText("1");
    await page.locator("#recipes").scrollIntoViewIfNeeded();
    await page.getByRole("button", { name: copy.next }).click();
    await expect(galleryPosition).toContainText("2");
});

test("foto da dupla fica abaixo dos nomes no desktop e no celular", async ({
    page,
}) => {
    await mockApi(page);
    await page.goto("/");
    const names = page.locator(".duo-names");
    const photo = page.locator(".duo-photo");

    await expect(photo).toHaveAttribute("src", "/assets/dupla.png");
    for (const width of [1440, 390]) {
        await page.setViewportSize({ width, height: 900 });
        await photo.scrollIntoViewIfNeeded();
        const namesBox = await names.boundingBox();
        const photoBox = await photo.boundingBox();
        expect(namesBox).not.toBeNull();
        expect(photoBox).not.toBeNull();
        expect(photoBox!.y).toBeGreaterThanOrEqual(
            namesBox!.y + namesBox!.height,
        );
        await expect
            .poll(() => photo.evaluate((image: HTMLImageElement) => image.naturalWidth))
            .toBeGreaterThan(0);
    }
});

for (const state of ["pending", "failed", "broken", "generated", "reused"]) {
    test(`imagem ${state} e URLs de fontes seguras`, async ({ page }) => {
        const initial = view("completed");
        initial.final_response!.image = {
            status: state === "broken" ? "generated" : state,
            url: "/images/recipe.png",
        };
        initial.final_response!.health.sources.push({
            title: "<script>alert(1)</script>",
            url: "javascript:alert(1)",
        });
        await mockApi(page, { initial });
        await page.route("**/api/images/recipe.png", (route) =>
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

test("referência raster local aparece no resultado e no card do histórico", async ({
    page,
}) => {
    const initial = view("completed");
    initial.final_response!.image = {
        status: "generated",
        url: "/images/recipe-1.png",
    };
    const history = [
        { id: "thread-1", ...structuredClone(initial.final_response!) },
    ];
    await mockApi(page, { initial, history });
    await page.route("**/api/images/recipe-1.png", (route) =>
        route.fulfill({
            path: "public/assets/coxinha-hero.png",
            contentType: "image/png",
        }),
    );
    await page.addInitScript(() =>
        sessionStorage.setItem("coxinh.activeThread", "thread-1"),
    );
    await page.goto("/");

    await expect(page.locator(".result .recipe-photo img")).toHaveAttribute(
        "src",
        "http://127.0.0.1:5174/api/images/recipe-1.png",
    );
    await expect(
        page.locator(".recipe-card .recipe-photo img"),
    ).toHaveAttribute("src", "http://127.0.0.1:5174/api/images/recipe-1.png");
    await expect(page.getByText(copy.imageCredit).first()).toBeVisible();
});

test("imagem grande fica limitada ao quadro no resultado e no carrossel", async ({
    page,
}) => {
    const initial = view("completed");
    initial.final_response!.image = {
        status: "generated",
        url: "/images/oversized.png",
    };
    const history = [
        { id: "thread-1", ...structuredClone(initial.final_response!) },
    ];
    await mockApi(page, { initial, history });
    await page.route("**/api/images/oversized.png", (route) =>
        route.fulfill({
            body: '<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="200" viewBox="0 0 2400 200"><rect width="2400" height="200" fill="#86bc25"/></svg>',
            contentType: "image/svg+xml",
        }),
    );
    await page.addInitScript(() =>
        sessionStorage.setItem("coxinh.activeThread", "thread-1"),
    );
    await page.goto("/");

    const frames = page.locator(".recipe-photo-frame");
    await expect(frames).toHaveCount(2);
    for (const width of [1440, 1024, 768, 390]) {
        await page.setViewportSize({ width, height: 1000 });
        const bounds = await frames.evaluateAll((elements) =>
            elements.map((element) => {
                const frame = element.getBoundingClientRect();
                const image = element.querySelector("img")!.getBoundingClientRect();
                return {
                    ratio: frame.width / frame.height,
                    frame: {
                        left: frame.left,
                        right: frame.right,
                        top: frame.top,
                        bottom: frame.bottom,
                    },
                    image: {
                        left: image.left,
                        right: image.right,
                        top: image.top,
                        bottom: image.bottom,
                    },
                    objectFit: getComputedStyle(
                        element.querySelector("img")!,
                    ).objectFit,
                };
            }),
        );

        for (const { ratio, frame, image, objectFit } of bounds) {
            expect(ratio).toBeCloseTo(1.2, 1);
            expect(objectFit).toBe("cover");
            expect(image.left).toBeGreaterThanOrEqual(frame.left - 1);
            expect(image.right).toBeLessThanOrEqual(frame.right + 1);
            expect(image.top).toBeGreaterThanOrEqual(frame.top - 1);
            expect(image.bottom).toBeLessThanOrEqual(frame.bottom + 1);
        }

        const cardFigure = await page
            .locator(".recipe-card .recipe-photo")
            .boundingBox();
        const cardTitle = await page
            .locator(".recipe-card .card-title")
            .boundingBox();
        expect(cardFigure).not.toBeNull();
        expect(cardTitle).not.toBeNull();
        expect(cardTitle!.y).toBeGreaterThanOrEqual(
            cardFigure!.y + cardFigure!.height,
        );
    }
});

test("fallbacks mantêm o enquadramento e o texto dentro dos quadros", async ({
    page,
}) => {
    const initial = view("completed");
    initial.final_response!.image = {
        status: "unavailable",
        url: "simulated://test",
    };
    const history = [
        { id: "thread-1", ...structuredClone(initial.final_response!) },
    ];
    await mockApi(page, { initial, history });
    await page.addInitScript(() =>
        sessionStorage.setItem("coxinh.activeThread", "thread-1"),
    );
    await page.goto("/");

    const placeholders = page.locator(
        ".result .image-placeholder, .recipe-card .image-placeholder",
    );
    await expect(placeholders).toHaveCount(2);
    for (const width of [1440, 1024, 768, 390]) {
        await page.setViewportSize({ width, height: 1000 });
        const dimensions = await placeholders.evaluateAll((elements) =>
            elements.map((element) => {
                const box = element.getBoundingClientRect();
                return {
                    ratio: box.width / box.height,
                    contentFits: element.scrollHeight <= element.clientHeight + 1,
                };
            }),
        );
        for (const { ratio } of dimensions)
            expect(ratio).toBeCloseTo(1.2, 1);
        expect(dimensions.every(({ contentFits }) => contentFits)).toBe(true);
    }
});

test("referência local inválida e imagem local indisponível mostram fallback", async ({
    page,
}) => {
    const initial = view("completed");
    initial.final_response!.image = {
        status: "generated",
        url: "/images/../outside.png",
    };
    await mockApi(page, { initial });
    await page.addInitScript(() =>
        sessionStorage.setItem("coxinh.activeThread", "thread-1"),
    );
    await page.goto("/");
    await expect(page.getByText(copy.noImage)).toBeVisible();
});

test("imagem local indisponível no servidor mantém o fallback", async ({
    page,
}) => {
    const initial = view("completed");
    initial.final_response!.image = {
        status: "generated",
        url: "/images/missing.png",
    };
    await mockApi(page, { initial });
    await page.route("**/api/images/missing.png", (route) =>
        route.fulfill({ status: 404, body: "" }),
    );
    await page.addInitScript(() =>
        sessionStorage.setItem("coxinh.activeThread", "thread-1"),
    );
    await page.goto("/");
    await expect(page.getByText(copy.noImage)).toBeVisible();
});

test("API real pelo proxy: sessão vazia, Impasse, salvar, recarregar e duas receitas", async ({
    page,
    browser,
}) => {
    await page.goto("/");
    await expect(page.getByText(copy.noRecipes)).toBeVisible();
    const response = await page.request.get("/api/recipes");
    expect(await response.json()).toEqual({ items: [] });
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
    const { items: history } = await (
        await page.request.get("/api/recipes")
    ).json();
    expect(history).toHaveLength(2);
    expect(new Set(history.map((item: { id: string }) => item.id)).size).toBe(
        2,
    );
    const other = await browser.newContext();
    try {
        const second = await other.newPage();
        await second.goto("/");
        await expect(second.locator(".recipe-card")).toHaveCount(2);
        await second.locator(".recipe-card").first().click();
        await expect(
            second.getByRole("heading", {
                name: "Coxinha de teste da cozinha",
            }),
        ).toBeVisible();
    } finally {
        await other.close();
    }
});

for (const status of ["error", "interrupted"] as const) {
    test(`polling termina em ${status} sem repetir criação`, async ({
        page,
    }) => {
        const api = await mockApi(page, { createStatus: status });
        await page.goto("/");
        await page.getByLabel(copy.input).fill("Pedido com falha");
        await page
            .getByRole("button", { name: copy.create, exact: true })
            .click();
        await expect(
            page.getByText(
                status === "error" ? copy.executionError : copy.interrupted,
            ),
        ).toBeVisible();
        await expect(
            page.getByRole("button", { name: copy.create, exact: true }),
        ).toBeEnabled();
        expect(api.creates).toBe(1);
        expect(api.reads).toBe(2);
    });
}

test("recarregar durante running restaura polling sem outro POST", async ({
    page,
}) => {
    const api = await mockApi(page, { runningReads: 2 });
    await page.goto("/");
    await page.getByLabel(copy.input).fill("Frango");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await expect
        .poll(() =>
            page.evaluate(() => sessionStorage.getItem("coxinh.activeThread")),
        )
        .toBe("thread-1");
    await page.reload();
    await expect(
        page.getByRole("heading", { name: finalResponse.recipe.title }),
    ).toBeVisible();
    expect(api.creates).toBe(1);
});

test("falha no polling oferece consulta manual sem repetir POST", async ({
    page,
}) => {
    const api = await mockApi(page, { runningReads: 0 });
    let failed = false;
    await page.route("**/api/recipes/thread-1", async (route) => {
        if (!failed) {
            failed = true;
            await route.abort();
        } else await route.fallback();
    });
    await page.goto("/");
    await page.getByLabel(copy.input).fill("Frango");
    await page.getByRole("button", { name: copy.create, exact: true }).click();
    await expect(page.getByText(copy.failure)).toBeVisible();
    await page.getByRole("button", { name: copy.refresh }).first().click();
    await expect(
        page.getByRole("heading", { name: finalResponse.recipe.title }),
    ).toBeVisible();
    expect(api.creates).toBe(1);
});

for (const [status, detail, message] of [
    [
        422,
        [{ loc: ["body", "raw_input"], msg: "invalid", type: "value_error" }],
        "Dados inválidos. Confira os campos enviados.",
    ],
    [
        503,
        {
            code: "service_unavailable",
            message: "Serviço temporariamente indisponível.",
        },
        "Serviço temporariamente indisponível.",
    ],
] as const) {
    test(`erro FastAPI ${status} fica legível`, async ({ page }) => {
        await mockApi(page);
        let posts = 0;
        await page.route("**/api/recipes", async (route) => {
            if (route.request().method() !== "POST") {
                await route.fallback();
                return;
            }
            posts++;
            await route.fulfill({ status, json: { detail } });
        });
        await page.goto("/");
        await page.getByLabel(copy.input).fill("Frango");
        await page
            .getByRole("button", { name: copy.create, exact: true })
            .click();
        await expect(page.getByText(message)).toBeVisible();
        expect(posts).toBe(1);
    });
}
