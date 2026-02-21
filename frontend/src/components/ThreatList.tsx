import { useEffect, useState, useRef } from 'react';
import gsap from 'gsap';
import { AlertTriangle, MapPin, Users } from 'lucide-react';

const MOCK_THREATS = [
    { id: 1, name: "Texas Longhorns vs. OU", cap: "100,247", time: "22:00", zone: "DKR Stadium" },
    { id: 2, name: "Formula 1 US Grand Prix", cap: "120,000", time: "17:30", zone: "COTA" },
    { id: 3, name: "SXSW Keynote Finale", cap: "85,000", time: "21:00", zone: "Downtown Core" },
];

export function ThreatList() {
    const [activeIndex, setActiveIndex] = useState(0);
    const pathRef = useRef<SVGPathElement>(null);

    useEffect(() => {
        const interval = setInterval(() => {
            setActiveIndex((prev) => (prev + 1) % MOCK_THREATS.length);
        }, 4000);

        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        // Animate the sparkline drawing every time the active threat changes
        if (pathRef.current) {
            const length = pathRef.current.getTotalLength();
            gsap.set(pathRef.current, { strokeDasharray: length, strokeDashoffset: length });
            gsap.to(pathRef.current, { strokeDashoffset: 0, duration: 1.5, ease: 'power2.out' });
        }
    }, [activeIndex]);

    return (
        <div className="tech-panel tech-interactive p-6 flex flex-col h-full h-[400px]">
            <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
                <h2 className="text-xl uppercase tracking-widest text-pale-slate flex items-center gap-2">
                    <AlertTriangle className="text-olive w-5 h-5" />
                    Layer 1: Intelligence
                </h2>
                <span className="telemetry-text text-taupe animate-pulse">LIVELINK ACTIVE</span>
            </div>

            <div className="flex-1 flex flex-col gap-4 overflow-hidden relative">
                {MOCK_THREATS.map((threat, idx) => {
                    const isActive = idx === activeIndex;
                    return (
                        <div
                            key={threat.id}
                            className={`p-4 border rounded-sm transition-all duration-500 ${isActive
                                    ? 'bg-olive/10 border-olive/50 scale-[1.02]'
                                    : 'bg-dark-panel border-white/5 opacity-50 grayscale'
                                }`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <h3 className={`font-space font-semibold tracking-wide ${isActive ? 'text-white' : 'text-pale-slate'}`}>
                                    {threat.name}
                                </h3>
                                <span className={`telemetry-text ${isActive ? 'text-olive' : 'text-grey-olive'}`}>
                                    T - {threat.time}
                                </span>
                            </div>
                            <div className="flex gap-4 text-xs font-mono text-grey-olive mt-3">
                                <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {threat.cap} Cap</span>
                                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {threat.zone}</span>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Sparkline Canvas */}
            <div className="mt-6 pt-4 border-t border-white/10">
                <div className="flex justify-between mb-2">
                    <span className="telemetry-text text-[10px] text-grey-olive">Projected Dispersal Sequence</span>
                    <span className="telemetry-text text-[10px] text-olive">T+0..T+4h</span>
                </div>
                <svg viewBox="0 0 100 40" className="w-full h-16 overflow-visible" preserveAspectRatio="none">
                    {/* Grid lines */}
                    <line x1="0" y1="20" x2="100" y2="20" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
                    <line x1="0" y1="40" x2="100" y2="40" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />

                    <path
                        ref={pathRef}
                        // Generate a random-looking curve based on index so it changes
                        d={
                            activeIndex === 0 ? "M 0 35 Q 20 35, 40 10 T 80 5 T 100 30" :
                                activeIndex === 1 ? "M 0 30 Q 30 30, 50 5 T 90 20 T 100 35" :
                                    "M 0 38 Q 10 38, 30 15 T 70 8 T 100 30"
                        }
                        fill="none"
                        stroke="#4F5D2F"
                        strokeWidth="2"
                        strokeLinecap="round"
                        className="drop-shadow-[0_0_8px_rgba(79,93,47,0.8)]"
                    />
                </svg>
            </div>
        </div>
    );
}
