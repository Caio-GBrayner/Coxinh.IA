import { test, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { mockApi } from "./fixtures";
import { copy } from "../src/content";

for (const width of [1440, 1024, 768, 390]) {
    test(`marca, fontes e revelação reversível pela rolagem em ${width}px`, async ({
        page,
    }) => {
        await page.setViewportSize({ width, height: 900 });
        await mockApi(page);
        await page.goto("/");
        await page.evaluate(() => document.fonts.ready);
        await expect(page.locator(".brand img")).toHaveCount(2);
        for (const img of await page.locator(".brand img").all()) {
            await expect(img).toHaveAttribute(
                "src",
                "/assets/coxinh-logo-nome.png",
            );
            await expect(img).toHaveAttribute("alt", copy.brand);
        }
        const directory = `../docs/design/review/${width}`;
        await mkdir(directory, { recursive: true });
        await page
            .locator(".site-header")
            .screenshot({ path: `${directory}/marca-header.png` });
        await page
            .locator(".story-frame")
            .screenshot({ path: `${directory}/historia-tipografia.png` });
        await page
            .locator(".duo")
            .screenshot({ path: `${directory}/dupla-tipografia.png` });
        await page
            .locator("footer")
            .screenshot({ path: `${directory}/marca-rodape.png` });
        const stage = page.locator(".class-reveal");
        const frame = page.locator(".class-reveal-frame");
        await stage.locator("img").evaluateAll((images) =>
            Promise.all(
                images.map((image) => {
                    const img = image as HTMLImageElement;
                    img.loading = "eager";
                    return img.decode();
                }),
            ),
        );
        for (const progress of [0, 0.5, 1, 0.25]) {
            await stage.evaluate((element, position) => {
                const pinned = element.querySelector(
                    ".class-reveal-sticky",
                ) as HTMLElement;
                const top = parseFloat(getComputedStyle(pinned).top);
                const distance =
                    element.getBoundingClientRect().height -
                    pinned.offsetHeight;
                window.scrollTo(
                    0,
                    scrollY +
                        element.getBoundingClientRect().top -
                        top +
                        distance * position,
                );
            }, progress);
            await expect
                .poll(async () => {
                    const box = (await frame.boundingBox())!;
                    const line = (await page
                        .locator(".class-reveal-divider")
                        .boundingBox())!;
                    return Math.abs(
                        (line.x + line.width / 2 - box.x) / box.width -
                            progress,
                    );
                })
                .toBeLessThan(0.01);
            await page.screenshot({
                path: `${directory}/turma-${progress * 100}.png`,
            });
        }
        await expect(page.locator(".story-frame h2")).toHaveCSS(
            "font-family",
            /Archivo/,
        );
        await expect(page.locator(".duo-names")).toHaveCSS(
            "font-family",
            /Archivo/,
        );
        await expect(page.locator(".story-columns .lead")).toHaveCSS(
            "font-family",
            /Source Sans 3/,
        );
        expect(
            await page.evaluate(
                () => document.documentElement.scrollWidth <= innerWidth,
            ),
        ).toBe(true);
    });
}

test("objetos flutuam, podem ser pausados e respeitam movimento reduzido", async ({
    page,
}) => {
    await mockApi(page);
    await page.goto("/");
    const coffee = page.locator(".coffee");
    const start = (await coffee.boundingBox())!.y;
    await expect
        .poll(async () => Math.abs((await coffee.boundingBox())!.y - start))
        .toBeGreaterThan(0.5);
    await page.getByRole("button", { name: copy.pauseMotion }).click();
    await expect(
        page.getByRole("button", { name: copy.resumeMotion }),
    ).toHaveAttribute("aria-pressed", "true");
    await expect(coffee).toHaveCSS("animation-play-state", "paused");
    await page.getByRole("button", { name: copy.resumeMotion }).click();
    await expect(coffee).toHaveCSS("animation-play-state", "running");
    await page.emulateMedia({ reducedMotion: "reduce" });
    await expect(coffee).toHaveCSS("animation-name", "none");
    await expect(
        page.getByRole("button", { name: copy.pauseMotion }),
    ).toHaveCount(0);
    await page.locator(".class-reveal").scrollIntoViewIfNeeded();
    const illustration = (await page
        .locator(".class-illustration")
        .boundingBox())!;
    const photo = (await page.locator(".class-photograph").boundingBox())!;
    expect(photo.y).toBeGreaterThanOrEqual(
        illustration.y + illustration.height,
    );
    await expect(page.locator(".class-photograph")).toHaveCSS(
        "clip-path",
        "none",
    );
});
