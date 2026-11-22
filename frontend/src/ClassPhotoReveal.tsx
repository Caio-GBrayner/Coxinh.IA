import { useEffect, useRef } from "react";
import { copy } from "./content";

/** Uma única moldura: a rolagem revela a foto sobre a ilustração, sem autoplay. */
export function ClassPhotoReveal() {
    const stage = useRef<HTMLDivElement>(null);
    const sticky = useRef<HTMLElement>(null);

    useEffect(() => {
        const element = stage.current!;
        const frame = sticky.current!;
        const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
        let animationFrame = 0;
        function update() {
            animationFrame = 0;
            if (reducedMotion.matches) {
                element.style.removeProperty("--reveal");
                return;
            }
            const bounds = element.getBoundingClientRect();
            const top = parseFloat(getComputedStyle(frame).top) || 0;
            const distance = Math.max(1, bounds.height - frame.offsetHeight);
            const progress = Math.min(
                1,
                Math.max(0, (top - bounds.top) / distance),
            );
            element.style.setProperty("--reveal", `${progress * 100}%`);
        }
        function schedule() {
            if (!animationFrame) animationFrame = requestAnimationFrame(update);
        }
        const observer = new ResizeObserver(schedule);
        observer.observe(element);
        observer.observe(frame);
        window.addEventListener("scroll", schedule, { passive: true });
        window.addEventListener("resize", schedule);
        reducedMotion.addEventListener("change", schedule);
        update();
        return () => {
            cancelAnimationFrame(animationFrame);
            observer.disconnect();
            window.removeEventListener("scroll", schedule);
            window.removeEventListener("resize", schedule);
            reducedMotion.removeEventListener("change", schedule);
        };
    }, []);

    return (
        <div className="class-reveal" ref={stage}>
            <figure className="class-reveal-sticky" ref={sticky}>
                <div className="class-reveal-frame">
                    <img
                        className="class-illustration"
                        src="/assets/turma-ilustrada.png"
                        alt={copy.illustration}
                        loading="lazy"
                    />
                    <img
                        className="class-photograph"
                        src="/assets/turma-bootcamp.png"
                        alt={copy.group}
                        loading="lazy"
                    />
                    <span className="class-reveal-divider" aria-hidden="true" />
                </div>
                <figcaption>
                    <span>{copy.illustration}</span>
                    <span>{copy.group}</span>
                </figcaption>
            </figure>
        </div>
    );
}
