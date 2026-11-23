import { useEffect, useRef, useState } from "react";
import {
    createRecipe,
    getRecipe,
    listRecipes,
    RecipeApiError,
    submitDecision,
} from "./recipeApi";
import type { DecisionRequest, RecipeView, SavedRecipe } from "./recipeTypes";
import { copy } from "./content";

const activeKey = "coxinh.activeThread";
export const storage = {
    get(key: string) {
        try {
            return sessionStorage.getItem(key);
        } catch {
            return null;
        }
    },
    set(key: string, value: string) {
        try {
            sessionStorage.setItem(key, value);
        } catch {
            /* Storage is optional. */
        }
    },
};

export function useRecipeSession() {
    const [active, setActive] = useState<RecipeView | null>(null);
    const [history, setHistory] = useState<SavedRecipe[]>([]);
    const [busy, setBusy] = useState(false);
    const [ready, setReady] = useState(false);
    const [message, setMessage] = useState("");
    const [historyError, setHistoryError] = useState("");
    const [needsRefresh, setNeedsRefresh] = useState(false);
    const locked = useRef(false);
    const booted = useRef(false);
    function accept(view: RecipeView) {
        storage.set(activeKey, view.thread_id);
        setActive(view);
        setNeedsRefresh(false);
    }
    async function refreshHistory() {
        try {
            const recipes = await listRecipes();
            setHistory(recipes);
            setHistoryError("");
        } catch {
            setHistoryError(copy.historyFailure);
        }
    }
    async function restore(id: string) {
        try {
            accept(await getRecipe(id));
            return true;
        } catch (error) {
            setNeedsRefresh(true);
            setMessage(
                error instanceof RecipeApiError && error.status === 404
                    ? copy.unavailable
                    : copy.failure,
            );
            return false;
        }
    }
    useEffect(() => {
        if (booted.current) return;
        booted.current = true;
        // Restore the active ID; the gallery is shared by all browsers.
        void (async () => {
            await refreshHistory();
            const id = storage.get(activeKey);
            if (id) await restore(id);
            setReady(true);
        })();
    }, []);
    // Only GET is retried. Cleanup prevents stale results after navigation/unmount.
    useEffect(() => {
        if (active?.status !== "running" || needsRefresh) return;
        let stopped = false;
        let timer: ReturnType<typeof setTimeout>;
        const id = active.thread_id;
        async function poll() {
            try {
                const next = await getRecipe(id);
                if (stopped) return;
                if (next.status === "running") {
                    setActive(next);
                    timer = setTimeout(() => void poll(), 1000);
                } else {
                    try {
                        const recipes = await listRecipes();
                        if (!stopped) {
                            setHistory(recipes);
                            setHistoryError("");
                        }
                    } catch {
                        if (!stopped) setHistoryError(copy.historyFailure);
                    }
                    if (!stopped) setActive(next);
                }
            } catch {
                if (!stopped) {
                    setNeedsRefresh(true);
                    setMessage(copy.failure);
                }
            }
        }
        timer = setTimeout(() => void poll(), 1000);
        return () => {
            stopped = true;
            clearTimeout(timer);
        };
    }, [active?.thread_id, active?.status, needsRefresh]);
    async function create(input: string) {
        if (locked.current || !ready || active?.status === "running") return;
        locked.current = true;
        setBusy(true);
        setMessage("");
        try {
            accept(await createRecipe(input));
            await refreshHistory();
        } catch (error) {
            // The server may have accepted this request; never automatically retry a POST.
            await refreshHistory();
            setMessage(
                error instanceof RecipeApiError
                    ? error.message
                    : copy.unknownCreation,
            );
        } finally {
            locked.current = false;
            setBusy(false);
        }
    }
    async function decide(
        action: DecisionRequest["action"],
        additions: string[],
        guidance: string,
    ) {
        if (
            !active ||
            active.status !== "awaiting_user" ||
            active.state_version === undefined ||
            locked.current ||
            needsRefresh
        )
            return false;
        locked.current = true;
        setBusy(true);
        setMessage("");
        const decision: DecisionRequest = {
            action,
            expected_state_version: active.state_version,
            idempotency_key: crypto.randomUUID(),
            ...(action === "save" && additions.length
                ? { ingredient_additions: additions }
                : {}),
            ...(action === "save" && guidance
                ? { user_guidance: guidance }
                : {}),
        };
        try {
            accept(await submitDecision(active.thread_id, decision));
            if (action === "save") setMessage(copy.saved);
            await refreshHistory();
            return true;
        } catch (error) {
            const restored = await restore(active.thread_id);
            if (restored)
                setMessage(
                    error instanceof RecipeApiError &&
                        error.code === "resume_limit_reached"
                        ? copy.resumeLimit
                        : error instanceof RecipeApiError && error.status === 409
                          ? copy.conflict
                          : error instanceof RecipeApiError
                            ? error.message
                            : copy.failure,
                );
            return false;
        } finally {
            locked.current = false;
            setBusy(false);
        }
    }
    async function refresh() {
        if (locked.current) return;
        locked.current = true;
        setBusy(true);
        setMessage("");
        const id = storage.get(activeKey);
        if (id) await restore(id);
        await refreshHistory();
        locked.current = false;
        setBusy(false);
    }
    return {
        active,
        history,
        busy: busy || (active?.status === "running" && !needsRefresh),
        ready,
        message,
        historyError,
        needsRefresh,
        create,
        decide,
        refresh,
        refreshHistory,
    };
}
