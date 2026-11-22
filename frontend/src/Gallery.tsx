import { useRef, useState } from "react";
import type { SavedRecipe } from "./recipeTypes";
import { RecipeImage } from "./RecipeResult";
import { copy } from "./content";
import { storage } from "./useRecipeSession";
export function Gallery({
    recipes,
    open,
    error,
    refresh,
}: {
    recipes: SavedRecipe[];
    open: (recipe: SavedRecipe) => void;
    error: string;
    refresh: () => Promise<void>;
}) {
    const [selected, setSelected] = useState(() =>
        storage.get("coxinh.galleryId"),
    );
    const touch = useRef<{ x: number; y: number } | null>(null);
    const index = Math.max(
        0,
        recipes.findIndex((recipe) => recipe.id === selected),
    );
    function move(direction: number) {
        if (recipes.length < 2) return;
        const recipe =
            recipes[(index + direction + recipes.length) % recipes.length];
        setSelected(recipe.id);
        storage.set("coxinh.galleryId", recipe.id);
    }
    const visible = [...recipes.slice(index), ...recipes.slice(0, index)].slice(
        0,
        3,
    );
    return (
        <section
            id="recipes"
            className="gallery section"
            aria-labelledby="gallery-title"
        >
            <header className="section-heading">
                <div>
                    <p className="eyebrow">{copy.session}</p>
                    <h2 id="gallery-title">{copy.gallery}</h2>
                </div>
                <div className="carousel-controls">
                    <button
                        aria-label={copy.previous}
                        disabled={recipes.length < 2}
                        onClick={() => move(-1)}
                    >
                        ←
                    </button>
                    <button
                        aria-label={copy.next}
                        disabled={recipes.length < 2}
                        onClick={() => move(1)}
                    >
                        →
                    </button>
                </div>
            </header>
            {error ? (
                <p role="alert">
                    {error}{" "}
                    <button onClick={() => void refresh()}>
                        {copy.refresh}
                    </button>
                </p>
            ) : !recipes.length ? (
                <div className="empty-gallery">
                    <p>{copy.noRecipes}</p>
                    <a href="#idea">{copy.create}</a>
                </div>
            ) : (
                <>
                    <p className="hint" aria-live="polite">
                        {copy.position} {index + 1} {copy.of} {recipes.length}
                    </p>
                    <div
                        className="carousel"
                        role="region"
                        aria-roledescription="carrossel"
                        aria-label={copy.gallery}
                        tabIndex={0}
                        onKeyDown={(event) => {
                            if (
                                event.key === "ArrowRight" ||
                                event.key === "ArrowLeft"
                            ) {
                                event.preventDefault();
                                move(event.key === "ArrowRight" ? 1 : -1);
                            }
                        }}
                        onTouchStart={(event) => {
                            touch.current = {
                                x: event.touches[0].clientX,
                                y: event.touches[0].clientY,
                            };
                        }}
                        onTouchEnd={(event) => {
                            if (!touch.current) return;
                            const dx =
                                event.changedTouches[0].clientX -
                                touch.current.x;
                            const dy =
                                event.changedTouches[0].clientY -
                                touch.current.y;
                            if (
                                Math.abs(dx) > 50 &&
                                Math.abs(dx) > Math.abs(dy)
                            )
                                move(dx < 0 ? 1 : -1);
                            touch.current = null;
                        }}
                    >
                        {visible.map((recipe) => (
                            <button
                                className="recipe-card"
                                key={recipe.id}
                                onClick={() => {
                                    setSelected(recipe.id);
                                    storage.set("coxinh.galleryId", recipe.id);
                                    open(recipe);
                                }}
                                aria-label={`${copy.open}: ${recipe.recipe.title}`}
                            >
                                <RecipeImage
                                    image={recipe.image}
                                    title={recipe.recipe.title}
                                />
                                <span className="card-title">
                                    {recipe.recipe.title}
                                </span>
                                <span className="card-subtitle">
                                    {recipe.recipe.subtitle}
                                </span>
                            </button>
                        ))}
                    </div>
                </>
            )}
        </section>
    );
}
