import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir } from "node:fs/promises";
import { copy } from "../src/content";
import { finalResponse, mockApi } from "./fixtures";

for (const width of [1440, 1024, 768, 390]) {
    test(`seis áreas, textos longos, teclado e acessibilidade em ${width}px`, async ({
        page,
    }) => {
        await page.setViewportSize({ width, height: 900 });
        const errors: string[] = [];
        page.on("pageerror", (error) => errors.push(error.message));
        const directory = `../docs/design/review/${width}`;
        await mkdir(directory, { recursive: true });
        const history = [1, 2, 3].map((id) => ({
            id: String(id),
            ...structuredClone(finalResponse),
            recipe: {
                ...finalResponse.recipe,
                title: `Coxinha ${id} com uma combinação muito improvável para experimentar`,
            },
        }));
        history[1].health.warning = "Aviso extenso de teste. ".repeat(45);
        history[1].health.sources = [
            {
                title: "Uma fonte com URL longa",
                url: `https://example.com/${"caminho".repeat(40)}`,
            },
        ];
        await mockApi(page, {
            createStatus: "awaiting_user",
            delay: 900,
            history,
        });
        await page.goto("/");
        await expect(
            page.getByRole("button", { name: copy.create, exact: true }),
        ).toBeEnabled();
        await page.evaluate(() =>
            Promise.all(
                Array.from(document.images).map((img) => {
                    img.loading = "eager";
                    return img.decode().catch(() => undefined);
                }),
            ),
        );
        await page.keyboard.press("Tab");
        await expect(page.getByRole("link", { name: copy.skip })).toBeFocused();
        await page.keyboard.press("Tab");
        await page.screenshot({ path: `${directory}/home.png` });
        await page
            .locator("#story")
            .screenshot({ path: `${directory}/historia.png` });
        await page
            .locator("#recipes")
            .screenshot({ path: `${directory}/galeria.png` });
        expect(
            await page.evaluate(
                () => document.documentElement.scrollWidth <= innerWidth,
            ),
        ).toBe(true);
        const homeAudit = await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze();
        expect(homeAudit.violations).toEqual([]);
        await page
            .getByLabel(copy.input)
            .fill("Coxinha de café com frango. ".repeat(20));
        await page
            .getByRole("button", { name: copy.create, exact: true })
            .click();
        await expect(page.locator(".assembly")).toBeVisible();
        await page.locator(".assembly").screenshot({
            path: `${directory}/montagem.png`,
            animations: "disabled",
        });
        await expect(
            page.getByRole("heading", { name: copy.impasse }),
        ).toBeVisible();
        await page
            .locator(".impasse")
            .screenshot({ path: `${directory}/impasse.png` });
        const impasseAudit = await new AxeBuilder({ page })
            .include(".impasse")
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze();
        expect(impasseAudit.violations).toEqual([]);
        await page
            .getByRole("button", {
                name: "Abrir receita: " + history[1].recipe.title,
            })
            .click();
        await page
            .locator(".result")
            .screenshot({ path: `${directory}/resultado.png` });
        expect(
            await page.evaluate(
                () => document.documentElement.scrollWidth <= innerWidth,
            ),
        ).toBe(true);
        const resultAudit = await new AxeBuilder({ page })
            .include(".result")
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze();
        expect(resultAudit.violations).toEqual([]);
        await page.emulateMedia({ reducedMotion: "reduce" });
        await page.evaluate(() => {
            document.documentElement.style.fontSize = "32px";
        });
        await page.screenshot({
            path: `${directory}/texto-ampliado.png`,
            fullPage: true,
        });
        expect(
            await page.evaluate(
                () => document.documentElement.scrollWidth <= innerWidth,
            ),
        ).toBe(true);
        expect(errors).toEqual([]);
    });
}

test("recortes possuem canal alfa e objetos visíveis", async ({ page }) => {
    await mockApi(page);
    await page.goto("/");
    const report = await page.evaluate(async () => {
        const files = [
            "coxinh-symbol.png",
            "coffee-cutout.png",
            "deloitte-cutout.png",
            "ship-cutout.png",
            "coxinha-hero.png",
        ];
        return Promise.all(
            files.map(async (file) => {
                const img = new Image();
                img.src = "/assets/" + file;
                await img.decode();
                const canvas = document.createElement("canvas");
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext("2d")!;
                ctx.drawImage(img, 0, 0);
                const pixels = ctx.getImageData(
                    0,
                    0,
                    img.width,
                    img.height,
                ).data;
                let transparent = 0;
                let opaque = 0;
                for (let i = 3; i < pixels.length; i += 4) {
                    if (pixels[i] === 0) transparent++;
                    if (pixels[i] >= 250) opaque++;
                }
                return {
                    file,
                    width: img.width,
                    height: img.height,
                    transparent,
                    opaque,
                };
            }),
        );
    });
    for (const item of report) {
        expect(item.transparent, item.file).toBeGreaterThan(100);
        expect(item.opaque, item.file).toBeGreaterThan(100);
    }
    await test.info().attach("alpha-report", {
        body: JSON.stringify(report, null, 2),
        contentType: "application/json",
    });
});
