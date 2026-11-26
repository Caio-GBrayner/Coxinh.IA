import { useEffect, useRef } from "react";
import * as THREE from "three";

/** A single animated brand mark keeps the loading state true to its reference. */
export function AssemblyScene() {
    const host = useRef<HTMLDivElement>(null);
    const pointer = useRef({ x: 0, y: 0 });

    useEffect(() => {
        const element = host.current;
        if (!element) return;
        let renderer: THREE.WebGLRenderer;
        try {
            renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        } catch {
            element.dataset.rendererFailed = "true";
            return;
        }
        const scene = new THREE.Scene();
        const camera = new THREE.OrthographicCamera(-2, 2, 2, -2, 0.1, 10);
        camera.position.z = 5;
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.setSize(element.clientWidth, element.clientHeight);
        element.appendChild(renderer.domElement);

        const geometry = new THREE.PlaneGeometry(1.34, 1.28);
        const material = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide });
        const mark = new THREE.Mesh(geometry, material);
        scene.add(mark);
        let alive = true;
        const texture = new THREE.TextureLoader().load("/assets/coxinh-symbol.png", (loaded) => {
            if (!alive) {
                loaded.dispose();
                return;
            }
            loaded.colorSpace = THREE.SRGBColorSpace;
            material.map = loaded;
            material.needsUpdate = true;
        }, undefined, () => { if (alive) element.dataset.rendererFailed = "true"; });
        let visible = true;
        let reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        let elapsed = 0;
        let previous = performance.now();
        let pointerX = 0;
        let pointerY = 0;

        const resize = () => {
            const width = element.clientWidth;
            const height = element.clientHeight;
            if (!width || !height) return;
            const aspect = width / height;
            const viewHeight = 4;
            camera.top = viewHeight / 2;
            camera.bottom = -viewHeight / 2;
            camera.left = -viewHeight * aspect / 2;
            camera.right = viewHeight * aspect / 2;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        };
        const resizeObserver = new ResizeObserver(resize);
        resizeObserver.observe(element);
        resize();
        const intersectionObserver = new IntersectionObserver(([entry]) => {
            visible = entry.isIntersecting;
            renderer.setAnimationLoop(visible ? animate : null);
            previous = performance.now();
        });
        intersectionObserver.observe(element);
        const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
        const updatePreference = (event: MediaQueryListEvent) => { reduced = event.matches; };
        preference.addEventListener("change", updatePreference);

        function animate(now: number) {
            if (!alive) return;
            const delta = Math.min((now - previous) / 1000, 0.05);
            previous = now;
            const active = !reduced;
            if (active) elapsed += delta;
            const entry = reduced ? 1 : THREE.MathUtils.clamp(elapsed / 0.9, 0, 1);
            const ease = 1 - Math.pow(1 - entry, 3);
            const drift = active ? Math.sin(elapsed * 1.25) : 0;
            pointerX += (pointer.current.x - pointerX) * (1 - Math.exp(-delta * 4));
            pointerY += (pointer.current.y - pointerY) * (1 - Math.exp(-delta * 4));
            mark.position.y = -0.23 - 0.08 * (1 - ease) + drift * 0.045 * ease;
            mark.rotation.z = active ? pointerX * 0.035 + Math.sin(elapsed * 0.7) * 0.012 : 0;
            mark.rotation.x = active ? -pointerY * 0.035 : 0;
            const breathing = active ? 1 + Math.sin(elapsed * 1.1) * 0.006 : 1;
            mark.scale.setScalar((0.94 + ease * 0.06) * breathing);
            material.opacity = ease;
            renderer.render(scene, camera);
        }
        renderer.setAnimationLoop(animate);

        return () => {
            alive = false;
            resizeObserver.disconnect();
            intersectionObserver.disconnect();
            preference.removeEventListener("change", updatePreference);
            renderer.setAnimationLoop(null);
            texture.dispose();
            geometry.dispose();
            material.dispose();
            renderer.dispose();
            renderer.domElement.remove();
        };
    }, []);

    return (
        <div
            ref={host}
            className="assembly-scene"
            aria-hidden="true"
            onPointerMove={(event) => {
                const rect = event.currentTarget.getBoundingClientRect();
                pointer.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                pointer.current.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
            }}
            onPointerLeave={() => { pointer.current.x = 0; pointer.current.y = 0; }}
        >
            <img className="assembly-fallback" src="/assets/coxinh-symbol.png" alt="" />
        </div>
    );
}
