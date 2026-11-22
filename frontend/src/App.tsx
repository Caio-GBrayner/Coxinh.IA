import { useEffect, useRef, useState } from "react";
import type { SavedRecipe } from "./recipeTypes";
import { copy } from "./content";
import { useRecipeSession } from "./useRecipeSession";
import { Impasse } from "./Impasse";
import { Gallery } from "./Gallery";
import { RecipeResult } from "./RecipeResult";
import "./App.css";

function App() {
    const session = useRecipeSession();
    const [idea, setIdea] = useState("");
    const [inputError, setInputError] = useState("");
    const [detail, setDetail] = useState<SavedRecipe | null>(null);
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
        setDetail(null);
        await session.create(idea.trim());
        workflow.current?.focus();
    }
    return (
        <>
            <a className="skip-link" href="#main">
                {copy.skip}
            </a>
            <header className="site-header">
                <a className="brand" href="#home">
                    <img src="/assets/coxinh-symbol.png" alt="" />
                    {copy.brand}
                </a>
                <nav aria-label={copy.navigation}>
                    <a href="#home">{copy.home}</a>
                    <a href="#recipes">{copy.gallery}</a>
                    <a href="#story">{copy.story}</a>
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
                <section id="home" className="hero section">
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
                </section>
                {(session.busy ||
                    session.active ||
                    session.message ||
                    detail) && (
                    <section
                        id="workflow"
                        className="workflow section"
                        ref={workflow}
                        tabIndex={-1}
                        aria-label={copy.active}
                    >
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
                                <p className="eyebrow">{copy.brand}</p>
                                <h2>{copy.processing}</h2>
                                <div
                                    className="assembly-art"
                                    aria-hidden="true"
                                >
                                    <span className="dough-layer" />
                                    <span className="filling-layer" />
                                    <img
                                        src="/assets/coxinh-symbol.png"
                                        alt=""
                                    />
                                </div>
                                <p>{copy.atmosphere}</p>
                            </div>
                        )}
                        {session.active && (
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
                        {!session.busy && !detail && status === "error" && (
                            <p role="status">{copy.executionError}</p>
                        )}
                        {!session.busy &&
                            !detail &&
                            ["in_revision", "approved"].includes(status) && (
                                <p role="status">
                                    {copy.running}{" "}
                                    <button
                                        onClick={() => void session.refresh()}
                                    >
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
                    <div className="class-photos">
                        <figure>
                            <img
                                src="/assets/turma-ilustrada.png"
                                alt={copy.illustration}
                                loading="lazy"
                            />
                            <figcaption>{copy.illustration}</figcaption>
                        </figure>
                        <figure>
                            <img
                                src="/assets/turma-bootcamp.png"
                                alt={copy.group}
                                loading="lazy"
                            />
                            <figcaption>{copy.group}</figcaption>
                        </figure>
                    </div>
                    <div className="duo">
                        <p className="duo-names">{copy.duoPending}</p>
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
                    open={(recipe) => {
                        setDetail(recipe);
                        requestAnimationFrame(() => workflow.current?.focus());
                    }}
                />
            </main>
            <footer>
                <a className="brand" href="#home">
                    {copy.brand}
                </a>
                <p>{copy.footer}</p>
            </footer>
        </>
    );
}
export default App;
