import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ThermometerSun } from 'lucide-react';

export function WeatherStress() {
    const containerRef = useRef<HTMLDivElement>(null);
    const sliderRef = useRef<HTMLInputElement>(null);
    const [temp, setTemp] = useState(70);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Automatically animate the slider to 105 to simulate stress test
            const obj = { val: 70 };
            gsap.to(obj, {
                val: 105,
                duration: 4,
                ease: 'power2.inOut',
                delay: 1,
                onUpdate: () => setTemp(Math.round(obj.val)),
                repeat: -1,
                yoyo: true,
                repeatDelay: 2
            });
        }, containerRef);

        return () => ctx.revert();
    }, []);

    // Calculate stress level based on temp (70 = 0%, 105 = 100%)
    const stressPercent = Math.max(0, Math.min(100, ((temp - 70) / (105 - 70)) * 100));

    // Interpolate color from Pale Slate (#B0B2B8) to Olive Leaf (#4F5D2F)
    // Simplified logic by just using the stress percent for opacity or direct GSAP color, but let's use a dynamic CSS var
    const getBarColor = (index: number, total: number) => {
        const threshold = (index / total) * 100;
        if (stressPercent > threshold) {
            // Active bar
            return stressPercent > 80 ? '#423629' : '#4F5D2F'; // Turns Taupe at extremely high stress, else Olive Leaf
        }
        return '#141414'; // Background empty
    };

    return (
        <div ref={containerRef} className="tech-panel tech-interactive p-6 flex flex-col h-full h-[400px]">
            <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
                <h2 className="text-xl uppercase tracking-widest text-pale-slate flex items-center gap-2">
                    <ThermometerSun className="text-lavender w-5 h-5" />
                    Layer 3: Simulation
                </h2>
                <span className="telemetry-text text-grey-olive">STRESS TEST</span>
            </div>

            <div className="flex-1 flex flex-col justify-between">
                <div className="space-y-4">
                    <div className="flex justify-between items-end">
                        <span className="font-mono text-xs text-grey-olive uppercase tracking-widest">Ambient Context</span>
                        <span className="font-space text-4xl font-bold text-white tracking-tighter">
                            {temp}°<span className="text-xl text-pale-slate">F</span>
                        </span>
                    </div>

                    <div className="relative pt-4">
                        <input
                            ref={sliderRef}
                            type="range"
                            min="70"
                            max="110"
                            value={temp}
                            readOnly
                            className="w-full h-1 bg-white/10 rounded-full appearance-none outline-none overflow-hidden "
                            style={{
                                boxShadow: 'inset 0 0 5px rgba(0,0,0,0.5)',
                            }}
                        />
                        {/* Custom thumb via CSS is possible, but we'll use a visual overlay for the slider track */}
                        <div
                            className="absolute top-4 left-0 h-1 bg-olive rounded-full transition-all duration-75"
                            style={{ width: `${((temp - 70) / 40) * 100}%`, boxShadow: '0 0 10px rgba(79, 93, 47, 0.8)' }}
                        />
                    </div>
                    <div className="flex justify-between font-mono text-[10px] text-grey-olive mt-2">
                        <span>70°F (Base)</span>
                        <span>110°F (Critical)</span>
                    </div>
                </div>

                {/* Stress Bar Chart */}
                <div className="mt-8 space-y-2">
                    <div className="flex justify-between items-center mb-4">
                        <span className="font-mono text-xs text-grey-olive uppercase tracking-widest">Projected Load Strain</span>
                        <span className={`font-mono text-sm font-bold ${stressPercent > 80 ? 'text-taupe animate-pulse' : 'text-olive'}`}>
                            +{((temp - 70) * 8.4).toFixed(1)} MW
                        </span>
                    </div>

                    <div className="flex gap-1 h-32 items-end">
                        {[...Array(15)].map((_, i) => {
                            const height = 20 + Math.pow(i, 1.8) * 0.5; // Exponential curve shape
                            const isActive = stressPercent > (i / 15) * 100;
                            return (
                                <div
                                    key={i}
                                    className="flex-1 rounded-sm transition-all duration-150"
                                    style={{
                                        height: `${height}%`,
                                        backgroundColor: isActive ? (stressPercent > 80 ? '#423629' : '#4F5D2F') : '#1A1A1A',
                                        boxShadow: isActive ? `0 0 8px ${stressPercent > 80 ? '#423629' : '#4F5D2F'}` : 'none',
                                        opacity: isActive ? 0.8 + Math.random() * 0.2 : 0.3
                                    }}
                                />
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
