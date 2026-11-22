import { useState } from "react";
import type { FinalResponse, ProposedRecipe } from "./recipeTypes";
import { copy } from "./content";

function safeUrl(value: string | null | undefined) {
    if (!value) return null;
    try {
        const url = new URL(value);
        return ["https:", "http:"].includes(url.protocol) ? url.href : null;
    } catch {
        return null;
    }
}
export function RecipeImage({
    image,
    title,
}: {
    image?: FinalResponse["image"];
    title: string;
}) {
    const [failedUrl, setFailedUrl] = useState<string | null>(null);
    const url = safeUrl(image?.url);
    const usable = ["generated", "reused", "completed"].includes(
        image?.status || "",
    );
    if (url && usable && failedUrl !== url)
        return (
            <figure className="recipe-photo">
                <img src={url} alt={title} onError={() => setFailedUrl(url)} />
                <figcaption>{copy.imageCredit}</figcaption>
            </figure>
        );
    const text = image?.url?.startsWith("simulated://")
        ? copy.imageSimulated
        : image?.status === "pending"
          ? copy.imagePending
          : copy.noImage;
    return (
        <div className="image-placeholder">
            <img src="/assets/coxinh-symbol.png" alt="" />
            <p>{copy.imagePlaceholder}</p>
            <small>{text}</small>
        </div>
    );
}
function Items({
    title,
    items,
    ordered = false,
}: {
    title: string;
    items?: string[];
    ordered?: boolean;
}) {
    if (!items?.length) return null;
    const List = ordered ? "ol" : "ul";
    return (
        <section className="recipe-list">
            <h3>{title}</h3>
            <List>
                {items.map((item, index) => (
                    <li key={index}>{item}</li>
                ))}
            </List>
        </section>
    );
}
export function Proposal({ recipe }: { recipe: ProposedRecipe }) {
    return (
        <div className="proposal">
            <h3>{copy.proposal}</h3>
            <p>
                <strong>{copy.dough}: </strong>
                {recipe.dough}
            </p>
            <p>
                <strong>{copy.filling}: </strong>
                {recipe.filling}
            </p>
            <Items title={copy.ingredients} items={recipe.ingredients} />
            <p>{recipe.preparation}</p>
            <Items title={copy.utensils} items={recipe.utensils} />
            <Items title={copy.methods} items={recipe.preparation_methods} />
        </div>
    );
}
export function RecipeResult({ response }: { response: FinalResponse | null }) {
    if (!response?.recipe) return <p role="status">{copy.incomplete}</p>;
    const { recipe, health, image } = response;
    return (
        <article className="result">
            <header className="result-title">
                <p className="eyebrow">{copy.ready}</p>
                <h2>{recipe.title || copy.incomplete}</h2>
                <p className="lead">{recipe.subtitle}</p>
            </header>
            <div className="result-grid">
                <RecipeImage
                    key={image?.url}
                    image={image}
                    title={recipe.title}
                />
                <div className="recipe-details">
                    <div className="recipe-pair">
                        <section>
                            <h3>{copy.dough}</h3>
                            <p>{recipe.dough}</p>
                        </section>
                        <section>
                            <h3>{copy.filling}</h3>
                            <p>{recipe.filling}</p>
                        </section>
                    </div>
                    <Items
                        title={copy.ingredients}
                        items={recipe.ingredients}
                    />
                    <Items title={copy.utensils} items={recipe.utensils} />
                    <Items
                        title={copy.methods}
                        items={recipe.preparation_methods}
                    />
                    <Items
                        title={copy.preparation}
                        items={recipe.steps}
                        ordered
                    />
                    {!recipe.steps?.length && <p>{copy.incomplete}</p>}
                </div>
            </div>
            <aside className="health">
                <div>
                    <p className="eyebrow">
                        {
                            copy.healthStatus[
                                health?.health_status || "unavailable"
                            ]
                        }
                    </p>
                    <h2>{copy.health}</h2>
                </div>
                <div>
                    <p className="lead">{health?.warning || copy.noHealth}</p>
                    <Items
                        title={copy.contraindications}
                        items={health?.contraindications}
                    />
                    {health?.uncertainty && (
                        <section>
                            <h3>{copy.uncertainty}</h3>
                            <p>{health.uncertainty}</p>
                        </section>
                    )}
                    {!!health?.sources?.length && (
                        <section>
                            <h3>{copy.sources}</h3>
                            <ul>
                                {health.sources.map((source, i) => (
                                    <li key={i}>
                                        {safeUrl(source.url) ? (
                                            <a
                                                href={safeUrl(source.url)!}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                {source.title || source.url}
                                                <span className="source-url">
                                                    {source.url}
                                                </span>
                                            </a>
                                        ) : (
                                            <span>
                                                {source.title} — {source.url}
                                            </span>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}
                </div>
            </aside>
        </article>
    );
}
