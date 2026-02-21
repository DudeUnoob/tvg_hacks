import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { Terminal, Zap } from 'lucide-react';

const REASONING_LINES = [
    "SYSTEM INITIATIVE: LAYER 4 ACTUATION",
    "> DKR dispersal at 22:00 + 102°F weather detected.",
    "> Cross-referencing historical unforecasted demand spikes...",
    "> Projected localized grid strain: +294.5 MW",
    "> Transformer T-809.b at 94% capacity.",
    "> Recommending Base Power pre-charge in zip codes 78705, 78722.",
    "> Estimating $18,450 arbitrage value across 1,200 deployed units."
];

const JSON_PAYLOAD = `{
  "dispatch_id": "BP-78705-SEQ-092",
  "target_zones": ["78705", "78722"],
  "trigger_event": "DKR_FOOTBALL_DISPERSAL",
  "weather_multiplier": 1.45,
  "action": "PRE_CHARGE_MAX",
  "fleet_allocation": 1200,
  "execution_window": "20:00:00 - 21:59:59",
  "expected_discharge": "22:00:00",
  "authorization": "PENDING_OPERATOR"
}`;

export function DispatchTerminal() {
    const containerRef = useRef<HTMLDivElement>(null);
    const [typedJson, setTypedJson] = useState("");
    const [typingComplete, setTypingComplete] = useState(false);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Fade in reasoning lines one by one
            gsap.from('.reasoning-line', {
                opacity: 0,
                x: -20,
                duration: 0.8,
                stagger: 0.8, // 0.8 seconds between each line
                ease: 'power2.out',
            });
        }, containerRef);

        return () => ctx.revert();
    }, []);

    useEffect(() => {
        // Wait for reasoning lines to finish (7 lines * 0.8s = 5.6s), then start typing payload
        const startDelay = setTimeout(() => {
            let currentIndex = 0;
            const interval = setInterval(() => {
                if (currentIndex <= JSON_PAYLOAD.length) {
                    setTypedJson(JSON_PAYLOAD.slice(0, currentIndex));
                    currentIndex += 2; // Speed up typing by taking 2 chars at a time
                } else {
                    clearInterval(interval);
                    setTypingComplete(true);
                }
            }, 15);
            return () => clearInterval(interval);
        }, 5600);

        return () => clearTimeout(startDelay);
    }, []);

    return (
        <section ref={containerRef} className="max-w-[1440px] mx-auto px-6 mb-24">
            <div className="tech-panel border-white/20 p-8">

                <div className="flex items-center gap-3 mb-8 border-b border-white/10 pb-4">
                    <Terminal className="text-olive w-6 h-6" />
                    <h2 className="text-2xl font-space uppercase tracking-widest text-white">
                        Layer 4: Actuation Engine
                    </h2>
                    <span className="ml-auto font-mono text-xs text-grey-olive tracking-widest border border-white/10 px-3 py-1 rounded-sm">
                        TERMINAL // SECURE
                    </span>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">

                    {/* LEFT: Plain English Reasoning */}
                    <div className="font-mono text-sm leading-relaxed space-y-4">
                        {REASONING_LINES.map((line, i) => (
                            <p
                                key={i}
                                className={`reasoning-line ${i === 0 ? 'text-olive font-bold' : 'text-pale-slate'}`}
                            >
                                {line}
                            </p>
                        ))}

                        {/* Blinking cursor after lines finish */}
                        <p className="reasoning-line text-taupe animate-pulse mt-8">_</p>
                    </div>

                    {/* RIGHT: JSON Payload and Execute Button */}
                    <div className="flex flex-col h-full">
                        <div className="flex-1 bg-black/50 border border-white/5 p-4 rounded-sm font-mono text-xs text-grey-olive relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-2 text-[10px] text-taupe border-b border-l border-white/5 bg-dark-panel">
                                payload.json
                            </div>
                            <pre className="whitespace-pre-wrap mt-4 text-lavender">
                                {typedJson}
                                {typingComplete ? '' : <span className="animate-pulse bg-lavender w-2 h-4 inline-block align-middle ml-1" />}
                            </pre>
                        </div>

                        {/* Execute Button */}
                        <button
                            className={`mt-6 w-full py-4 rounded-sm font-space font-bold text-lg tracking-widest transition-all duration-300 flex items-center justify-center gap-3 ${typingComplete
                                    ? 'bg-olive text-white shadow-[0_0_20px_rgba(79,93,47,0.4)] hover:shadow-[0_0_30px_rgba(79,93,47,0.8)] hover:bg-[#5a6a36] cursor-pointer'
                                    : 'bg-dark-panel border border-white/5 text-grey-olive cursor-not-allowed opacity-50'
                                }`}
                            disabled={!typingComplete}
                        >
                            <Zap className={`w-5 h-5 ${typingComplete ? 'text-white' : 'text-grey-olive'}`} />
                            [ EXECUTE DISPATCH ]
                        </button>
                    </div>

                </div>
            </div>
        </section>
    );
}
