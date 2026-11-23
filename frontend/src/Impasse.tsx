import { useState } from "react";
import type { DecisionRequest, RecipeView } from "./recipeTypes";
import { copy } from "./content";
import { Proposal } from "./RecipeResult";
export function Impasse({
    active,
    busy,
    blocked,
    decide,
}: {
    active: RecipeView;
    busy: boolean;
    blocked: boolean;
    decide: (
        action: DecisionRequest["action"],
        additions: string[],
        guidance: string,
    ) => Promise<boolean>;
}) {
    const [guidance, setGuidance] = useState("");
    const [ingredients, setIngredients] = useState("");
    const [error, setError] = useState("");
    const dirty = !!(guidance.trim() || ingredients.trim());
    async function act(action: DecisionRequest["action"]) {
        const additions = ingredients
            .split("\n")
            .map((value) => value.trim())
            .filter(Boolean);
        if (action === "save" && !dirty) {
            setError(copy.saveEmpty);
            return;
        }
        if (action === "resume" && dirty) {
            setError(copy.unsaved);
            return;
        }
        setError("");
        if (await decide(action, additions, guidance.trim())) {
            setGuidance("");
            setIngredients("");
        }
    }
    return (
        <div className="impasse">
            <header>
                <p className="eyebrow">
                    {copy.impasseLabel} · {copy.version} {active.state_version}
                </p>
                <h2>{copy.impasse}</h2>
            </header>
            <div className="impasse-grid">
                <div>
                    {active.critique && (
                        <section>
                            <h3>{copy.critique}</h3>
                            <p>{active.critique}</p>
                        </section>
                    )}
                    {active.recipe && <Proposal recipe={active.recipe} />}
                    {active.user_guidance && (
                        <section>
                            <h3>{copy.savedGuidance}</h3>
                            <p>{active.user_guidance}</p>
                        </section>
                    )}
                    {!!active.ingredient_additions?.length && (
                        <section>
                            <h3>{copy.savedAdditions}</h3>
                            <ul>
                                {active.ingredient_additions?.map((x, i) => (
                                    <li key={i}>{x}</li>
                                ))}
                            </ul>
                        </section>
                    )}
                </div>
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        void act("save");
                    }}
                >
                    <label htmlFor="guidance">{copy.guidance}</label>
                    <textarea
                        id="guidance"
                        value={guidance}
                        onChange={(event) => setGuidance(event.target.value)}
                        aria-describedby={error ? "decision-error" : undefined}
                    />
                    <label htmlFor="additions">{copy.additions}</label>
                    <textarea
                        id="additions"
                        value={ingredients}
                        onChange={(event) => setIngredients(event.target.value)}
                        aria-describedby="additions-help"
                    />
                    <p id="additions-help" className="hint">
                        {copy.additionsHelp}
                    </p>
                    {error && (
                        <p id="decision-error" role="alert">
                            {error}
                        </p>
                    )}
                    <div className="decision-actions">
                        <button className="primary" disabled={busy || blocked}>
                            {copy.save}
                        </button>
                        <button
                            type="button"
                            disabled={busy || blocked}
                            onClick={() => void act("resume")}
                        >
                            {copy.resume}
                        </button>
                        <button
                            type="button"
                            disabled={busy || blocked || !active.recipe}
                            onClick={() => void act("accept")}
                        >
                            {copy.accept}
                        </button>
                        <button
                            className="text-button"
                            type="button"
                            disabled={busy || blocked}
                            onClick={() => void act("cancel")}
                        >
                            {copy.cancel}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
