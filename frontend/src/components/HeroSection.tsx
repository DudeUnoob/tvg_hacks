import { useEffect, useRef } from 'react';
import gsap from 'gsap';

export function HeroSection() {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Split text animation
            gsap.from('.hero-text span', {
                y: 50,
                opacity: 0,
                duration: 1.2,
                stagger: 0.2,
                ease: 'power3.out',
                delay: 0.5
            });

            // Pulse ring animations
            gsap.utils.toArray('.pulse-ring').forEach((ring: any, i) => {
                gsap.to(ring, {
                    scale: 3 + i * 0.5,
                    opacity: 0,
                    duration: 3 + i,
                    repeat: -1,
                    ease: 'power1.out',
                    delay: i * 0.5
                });
            });
        }, containerRef);

        return () => ctx.revert();
    }, []);

    return (
        <section
            ref={containerRef}
            className="relative w-full h-[100dvh] bg-dark overflow-hidden flex flex-col justify-center border-b border-white/10"
        >
            {/* Background Image with Vignette */}
            <div
                className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat opacity-40 mix-blend-luminosity"
                style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1519501025264-65ba15a82390?q=80&w=3540&auto=format&fit=crop")' }}
            />
            <div className="absolute inset-0 z-0 bg-gradient-to-b from-dark/80 via-transparent to-dark" />
            <div className="absolute inset-0 z-0 bg-dark/20 backdrop-brightness-50" />

            {/* Pulse Animations (Simulated Events on Map) */}
            <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
                <div className="relative w-full h-full max-w-6xl mx-auto">
                    {/* Node 1 */}
                    <div className="absolute top-[40%] left-[30%] -translate-x-1/2 -translate-y-1/2">
                        <div className="w-3 h-3 bg-taupe rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 shadow-[0_0_15px_#423629]" />
                        <div className="pulse-ring w-6 h-6 border border-taupe rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                        <div className="pulse-ring w-6 h-6 border border-taupe rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                    </div>

                    {/* Node 2 */}
                    <div className="absolute top-[60%] left-[65%] -translate-x-1/2 -translate-y-1/2">
                        <div className="w-4 h-4 bg-olive rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 shadow-[0_0_20px_#4F5D2F]" />
                        <div className="pulse-ring w-8 h-8 border border-olive rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 delay-100" />
                        <div className="pulse-ring w-8 h-8 border border-olive rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 delay-300" />
                        <div className="pulse-ring w-8 h-8 border border-olive rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 delay-500" />
                    </div>
                </div>
            </div>

            {/* Hero Content */}
            <div className="relative z-20 px-8 max-w-7xl mx-auto w-full">
                <h1 className="hero-text text-8xl md:text-9xl font-space font-bold tracking-tighter leading-[0.85] flex flex-col uppercase">
                    <span className="text-white drop-shadow-2xl">Anticipate the</span>
                    <span className="text-lavender drop-shadow-[0_0_30px_rgba(207,214,234,0.4)]">Invisible Surge.</span>
                </h1>

                <div className="mt-12 flex items-start gap-8 border-l border-white/20 pl-6 tech-interactive p-4 max-w-xl bg-dark/40 backdrop-blur-sm rounded-sm">
                    <div className="text-grey-olive font-mono text-xs uppercase space-y-2">
                        <p>System Initiative initialized.</p>
                        <p>Scanning urban topology for unforecasted demand spikes.</p>
                        <p className="text-taupe animate-pulse">Connecting to Base Power Telemetry...</p>
                    </div>
                </div>
            </div>

            {/* Scroll indicator */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-2 opacity-60">
                <span className="font-mono text-xs text-pale-slate uppercase tracking-widest">Initialize Telemetry</span>
                <div className="w-[1px] h-12 bg-gradient-to-b from-pale-slate to-transparent" />
            </div>
        </section>
    );
}
