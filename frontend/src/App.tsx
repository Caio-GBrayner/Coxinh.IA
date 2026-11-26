import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { getRecipe } from "./recipeApi";
import type { FinalResponse, SavedRecipe } from "./recipeTypes";
import { copy } from "./content";
import { useRecipeSession } from "./useRecipeSession";
import { Impasse } from "./Impasse";
import { Gallery } from "./Gallery";
import { RecipeResult } from "./RecipeResult";
import { ClassPhotoReveal } from "./ClassPhotoReveal";

import "./App.css";

const AssemblyScene = lazy(() =>
    import("./AssemblyScene").then(({ AssemblyScene: Component }) => ({
        default: Component,
    })),
);

function App() {
    const session = useRecipeSession();
    const [idea, setIdea] = useState("");
    const [inputError, setInputError] = useState("");
    const [detail, setDetail] = useState<FinalResponse | null>(null);
    const [detailError, setDetailError] = useState("");
    const detailRequest = useRef(0);
    const [motionPaused, setMotionPaused] = useState(false);
    const workflow = useRef<HTMLElement>(null);
    const previousStatus = useRef("");
    const status = session.active?.status || "";
    useEffect(() => {
        if (status && status !== previousStatus.current) {
            workflow.current?.focus();
            previousStatus.current = status;
        }
    }, [status]);
    useEffect(() => {
        if (session.busy) workflow.current?.focus();
    }, [session.busy]);
    async function openRecipe(recipe: SavedRecipe) {
        const request = ++detailRequest.current;
        setDetailError("");
        setDetail(null);
        try {
            const view = await getRecipe(recipe.id);
            if (request !== detailRequest.current) return;
            if (view.status !== "completed" || !view.final_response)
                throw new Error(copy.incomplete);
            setDetail(view.final_response);
            requestAnimationFrame(() => workflow.current?.focus());
        } catch {
            if (request === detailRequest.current)
                setDetailError(copy.unavailable);
        }
    }
    function focusIdea() {
        document.getElementById("idea")?.focus();
    }
    async function create(event: React.SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!idea.trim()) {
            setInputError(copy.empty);
            focusIdea();
            return;
        }
        setInputError("");
        detailRequest.current++;
        setDetail(null);
        setDetailError("");
        await session.create(idea.trim());
        workflow.current?.focus();
    }
    return (
        <>
            <a className="skip-link" href="#main">
                {copy.skip}
            </a>
            <header className="site-header">
                <div className="brand-lockup">
                    <a className="brand" href="#home">
                        <img
                            src="/assets/coxinh-logo-nome.png"
                            alt={copy.brand}
                        />
                    </a>
                    <span className="brand-by">by</span>
                    <span className="brand-deloitte-frame">
                        <img
                            className="brand-deloitte"
                            src="/assets/deloitte-cutout.png"
                            alt="Deloitte"
                        />
                    </span>
                </div>
                <nav aria-label={copy.navigation}>
                    <a href="#home">{copy.home}</a>
                    <a href="#story">{copy.story}</a>
                    <a href="#recipes">{copy.gallery}</a>
                </nav>
                <a
                    className="button primary header-create"
                    href="#idea"
                    onClick={focusIdea}
                >
                    {copy.create}
                </a>
            </header>
            <main id="main">
                <section
                    id="home"
                    className="hero section"
                    data-motion-paused={motionPaused}
                >
                    <form
                        className="idea-card"
                        onSubmit={create}
                        aria-busy={session.busy}
                    >
                        <p className="eyebrow">{copy.kitchen}</p>
                        <h1>{copy.title}</h1>
                        <label htmlFor="idea">{copy.input}</label>
                        <p id="idea-help" className="hint">
                            {copy.help}
                        </p>
                        <textarea
                            id="idea"
                            rows={4}
                            maxLength={4000}
                            value={idea}
                            onChange={(event) => setIdea(event.target.value)}
                            aria-invalid={!!inputError}
                            aria-describedby={`idea-help${inputError ? " idea-error" : ""}`}
                        />
                        {inputError && (
                            <p id="idea-error" role="alert">
                                {inputError}
                            </p>
                        )}
                        <button
                            className="primary"
                            disabled={session.busy || !session.ready}
                        >
                            {session.busy
                                ? copy.processing
                                : !session.ready
                                  ? copy.restoring
                                  : copy.create}
                        </button>
                        {session.active && (
                            <a
                                className="active-link"
                                href="#workflow"
                                onClick={() => setDetail(null)}
                            >
                                {copy.active}
                            </a>
                        )}
                    </form>
                    <div className="hero-art" aria-hidden="true">
                        <span className="hero-wordmark">{copy.brand}</span>
                        <img
                            className="hero-coxinha"
                            src="/assets/coxinha-hero.png"
                            alt=""
                        />
                        <img
                            className="float coffee"
                            src="/assets/coffee-cutout.png"
                            alt=""
                        />
                        <img
                            className="float deloitte"
                            src="/assets/deloitte-cutout.png"
                            alt=""
                        />
                        <img
                            className="float ship"
                            src="/assets/ship-cutout.png"
                            alt=""
                        />
                        <img
                            className="float symbol"
                            src="/assets/coxinh-symbol.png"
                            alt=""
                        />
                    </div>
                    <button
                        className="motion-toggle"
                        type="button"
                        aria-pressed={motionPaused}
                        onClick={() => setMotionPaused(!motionPaused)}
                    >
                        {motionPaused ? copy.resumeMotion : copy.pauseMotion}
                    </button>
                </section>
                {(session.busy ||
                    session.active ||
                    session.message ||
                    detailError ||
                    detail) && (
                    <section
                        id="workflow"
                        className={`workflow section${session.busy ? " workflow-loading" : ""}`}
                        ref={workflow}
                        tabIndex={-1}
                        aria-label={copy.active}
                    >
                        {detailError && <p role="alert">{detailError}</p>}
                        {session.message && (
                            <div className="notice" role="status">
                                <p>{session.message}</p>
                                <button
                                    disabled={session.busy}
                                    onClick={() => void session.refresh()}
                                >
                                    {copy.refresh}
                                </button>
                            </div>
                        )}
                        {session.busy && (
                            <div className="assembly" role="status">
                                <Suspense fallback={null}>
                                    <AssemblyScene />
                                </Suspense>
                                <p className="eyebrow assembly-brand">{copy.brand}</p>
                                <h2>{copy.processing}</h2>
                                <p>{copy.atmosphere}</p>
                            </div>
                        )}
                        {session.active?.status === "awaiting_user" && (
                            <div
                                hidden={
                                    !!detail ||
                                    session.active.status !== "awaiting_user"
                                }
                            >
                                <Impasse
                                    key={session.active.thread_id}
                                    active={session.active}
                                    busy={session.busy}
                                    blocked={session.needsRefresh}
                                    decide={session.decide}
                                />
                            </div>
                        )}
                        {!session.busy &&
                            (detail || status === "completed") && (
                                <>
                                    <RecipeResult
                                        response={
                                            detail ||
                                            session.active?.final_response ||
                                            null
                                        }
                                    />
                                    <div className="result-actions">
                                        <a
                                            className="button"
                                            href="#recipes"
                                            onClick={() => setDetail(null)}
                                        >
                                            {copy.back}
                                        </a>
                                        <a
                                            className="button primary"
                                            href="#idea"
                                            onClick={() => {
                                                setDetail(null);
                                                focusIdea();
                                            }}
                                        >
                                            {copy.another}
                                        </a>
                                    </div>
                                </>
                            )}
                        {!session.busy && !detail && status === "cancelled" && (
                            <h2>{copy.cancelled}</h2>
                        )}
                        {!session.busy && !detail && status === "blocked" && (
                            <div role="alert">
                                <h2>{copy.blocked}</h2>
                                <p>{session.active?.guardrail?.message}</p>
                            </div>
                        )}
                        {!session.busy &&
                            !detail &&
                            ["error", "interrupted"].includes(status) && (
                                <p role="status">
                                    {status === "interrupted"
                                        ? copy.interrupted
                                        : session.active?.error ||
                                          copy.executionError}
                                </p>
                            )}
                        {!session.busy && !detail && status === "running" && (
                            <p role="status">
                                {copy.running}{" "}
                                <button onClick={() => void session.refresh()}>
                                    {copy.refresh}
                                </button>
                            </p>
                        )}
                    </section>
                )}
                <section id="story" className="story section">
                    <div className="story-frame">
                        <p className="eyebrow">{copy.origin}</p>
                        <h2>{copy.storyTitle}</h2>
                        <div className="story-columns">
                            <p className="lead">{copy.storyLead}</p>
                            <p>{copy.storyBody}</p>
                        </div>
                        <img
                            className="story-coxinha"
                            src="/assets/coxinha-hero.png"
                            alt=""
                        />
                    </div>
                    <ClassPhotoReveal />
                    <div className="duo">
                        <div className="duo-portrait">
                            <p className="duo-names">{copy.duoPending}</p>
                            <img
                                className="duo-photo"
                                src="/assets/dupla.png"
                                alt="João e Caio juntos"
                                loading="lazy"
                            />
                            <p className="duo-photo-caption">
                                {copy.duoPhotoCaption}
                            </p>
                        </div>
                        <div>
                            <h2>{copy.duoTitle}</h2>
                            <p>{copy.duoBody}</p>
                        </div>
                    </div>
                </section>
                <Gallery
                    recipes={session.history}
                    error={session.historyError}
                    refresh={session.refreshHistory}
                    open={(recipe) => void openRecipe(recipe)}
                />
            </main>
            <footer>
                <a className="brand" href="#home">
                    <img src="/assets/coxinh-logo-nome.png" alt={copy.brand} />
                </a>
                <p>{copy.footer}</p>
            </footer>
            <nav className="floating-nav" aria-label="Navegação flutuante">
                <a href="#home">{copy.home}</a>
                <a href="#story">{copy.story}</a>
                <a href="#recipes">{copy.gallery}</a>
                <a className="primary" href="#idea" onClick={focusIdea}>
                    {copy.create}
                </a>
            </nav>
        </>
    );
}
export default App;
