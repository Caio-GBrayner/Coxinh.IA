import { defineConfig } from "@playwright/test";

export default defineConfig({
    testDir: "./tests",
    fullyParallel: false,
    workers: 1,
    reporter: [["list"], ["html", { open: "never" }]],
    use: {
        baseURL: "http://127.0.0.1:5174",
        channel: process.env.PLAYWRIGHT_CHANNEL || "msedge",
        headless: true,
        screenshot: "only-on-failure",
        trace: "retain-on-failure",
    },
    webServer: [
        {
            command: "npm run dev -- --host 127.0.0.1 --port 5174 --strictPort",
            url: "http://127.0.0.1:5174",
            env: { COXINH_API_TARGET: "http://127.0.0.1:8001" },
            reuseExistingServer: false,
        },
        {
            command:
                "..\\.venv\\Scripts\\python.exe -m uvicorn tests.browser_api:app --app-dir .. --host 127.0.0.1 --port 8001",
            url: "http://127.0.0.1:8001/openapi.json",
            reuseExistingServer: false,
        },
    ],
});
