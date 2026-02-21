import { useEffect, useRef } from 'react';
import gsap from 'gsap';

const SOURCES = [
    "ERCOT Real-Time Load & Price",
    "TXDOT Austin Traffic Cameras",
    "UT Athletics Calendar API",
    "Moody Center Event Scraper",
    "Austin Open Data Portal",
    "Project Connect GIS Config",
    "Base Power Operator API",
];

export function Footer() {
    const marqueeRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const ctx = gsap.context(() => {
            gsap.to('.marquee-content', {
                xPercent: -50,
                ease: 'none',
                duration: 30,
                repeat: -1,
            });
        }, marqueeRef);

        return () => ctx.revert();
    }, []);

    return (
        <footer className="border-t border-white/10 bg-dark-panel pb-12 mt-20 relative overflow-hidden">
            {/* Marquee Section */}
            <div
                ref={marqueeRef}
                className="flex items-center h-12 border-b border-white/5 bg-black/40 overflow-hidden relative opacity-70"
            >
                <div className="absolute left-0 top-0 bottom-0 w-16 bg-gradient-to-r from-dark-panel to-transparent z-10" />
                <div className="marquee-content flex whitespace-nowrap gap-8 text-[10px] sm:text-xs font-mono text-grey-olive tracking-widest uppercase">
                    {/* Double content for seamless looping */}
                    <div className="flex gap-16 pr-16 items-center">
                        {SOURCES.map((source, i) => (
                            <span key={`src1-${i}`}>[ {source} ]</span>
                        ))}
                    </div>
                    <div className="flex gap-16 pr-16 items-center">
                        {SOURCES.map((source, i) => (
                            <span key={`src2-${i}`}>[ {source} ]</span>
                        ))}
                    </div>
                </div>
                <div className="absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-dark-panel to-transparent z-10" />
            </div>

            {/* Brutalist Sign-off */}
            <div className="max-w-[1440px] mx-auto px-6 mt-16 grid grid-cols-1 md:grid-cols-2 gap-8 items-end">
                <div>
                    <h3 className="font-space text-3xl font-bold tracking-tighter text-pale-slate">GRIDPULSE</h3>
                    <p className="font-mono text-xs text-grey-olive mt-4 uppercase max-w-sm">
                        A real-time simulation layer for ERCOT demand volatility and proactive battery fleet actuation.
                    </p>
                </div>

                <div className="md:text-right flex flex-col md:items-end justify-end">
                    <div className="flex items-center gap-3 border border-white/10 bg-black/50 px-4 py-2 tech-panel w-fit">
                        <div className="w-2 h-2 rounded-full bg-olive animate-pulse shadow-[0_0_8px_#4F5D2F]" />
                        <span className="font-mono text-[10px] sm:text-xs uppercase text-white tracking-widest">
                            Grid Operational
                        </span>
                    </div>
                    <span className="font-mono text-[10px] text-grey-olive mt-4 block">
                        SESSION_ID: BP-{Math.floor(Math.random() * 90000) + 10000}-TX
                    </span>
                </div>
            </div>
        </footer>
    );
}
