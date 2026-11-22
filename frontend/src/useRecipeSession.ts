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
            setHistory([...recipes].reverse());
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
        // Establish the cookie first; parallel initial calls can create two sessions.
        void (async () => {
            await refreshHistory();
            const id = storage.get(activeKey);
            if (id) await restore(id);
            setReady(true);
        })();
    }, []);
    async function create(input: string) {
        if (locked.current || !ready) return;
        locked.current = true;
        setBusy(true);
        setMessage("");
        try {
            accept(await createRecipe(input));
            await refreshHistory();
        } catch {
            // The ID arrives only after execution; never automatically retry a POST.
            await refreshHistory();
            setMessage(copy.unknownCreation);
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
        if (!active || locked.current || needsRefresh) return false;
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
                    error instanceof RecipeApiError && error.status === 409
                        ? copy.conflict
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
        busy,
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
