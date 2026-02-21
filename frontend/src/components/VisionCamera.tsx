import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { Camera, Scan } from 'lucide-react';

export function VisionCamera() {
    const boxRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [confidence, setConfidence] = useState(82);
    const [attendance, setAttendance] = useState(98400);

    useEffect(() => {
        // Tick up the numbers rapidly to simulate active processing
        const interval = setInterval(() => {
            setConfidence((prev) => Math.min(99, prev + Math.floor(Math.random() * 3)));
            setAttendance((prev) => Math.min(101500, prev + Math.floor(Math.random() * 250)));
        }, 800);

        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Simulate scanning bounding box
            gsap.to(boxRef.current, {
                x: "random(-40, 40)",
                y: "random(-30, 30)",
                width: "random(40, 100)",
                height: "random(40, 100)",
                duration: 1.5,
                ease: "power2.inOut",
                repeat: -1,
                repeatRefresh: true,
            });

            // Subtle digital noise/flicker on the camera container
            gsap.to(containerRef.current, {
                opacity: 0.85,
                duration: 0.1,
                yoyo: true,
                repeat: -1,
                repeatDelay: Math.random() * 2,
            });
        }, containerRef);

        return () => ctx.revert();
    }, []);

    return (
        <div className="tech-panel tech-interactive p-6 flex flex-col h-full h-[400px]">
            <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
                <h2 className="text-xl uppercase tracking-widest text-pale-slate flex items-center gap-2">
                    <Camera className="text-taupe w-5 h-5" />
                    Layer 2: VLM Vision
                </h2>
                <span className="telemetry-text text-pale-slate">TXDOT-CAM-04</span>
            </div>

            <div className="flex-1 flex flex-col relative bg-black/60 rounded border border-white/5 overflow-hidden">
                {/* Mock Camera Feed with scan lines */}
                <div
                    ref={containerRef}
                    className="absolute inset-0 bg-cover bg-center grayscale contrast-125 brightness-50 mix-blend-screen"
                    style={{
                        backgroundImage: 'url("https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?q=80&w=3540&auto=format&fit=crop")',
                    }}
                >
                    {/* Scanline overlay */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%] pointer-events-none z-10" />
                </div>

                {/* Animated Bounding Box */}
                <div className="absolute inset-0 z-20 flex items-center justify-center">
                    <div
                        ref={boxRef}
                        className="border border-olive bg-olive/10 shadow-[0_0_15px_rgba(79,93,47,0.5)] relative flex items-center justify-center"
                        style={{ width: '60px', height: '60px' }}
                    >
                        <Scan className="w-10 h-10 text-olive opacity-80" />

                        {/* Crosshairs */}
                        <div className="absolute -top-1 -left-1 w-2 h-2 border-t-2 border-l-2 border-white/80" />
                        <div className="absolute -top-1 -right-1 w-2 h-2 border-t-2 border-r-2 border-white/80" />
                        <div className="absolute -bottom-1 -left-1 w-2 h-2 border-b-2 border-l-2 border-white/80" />
                        <div className="absolute -bottom-1 -right-1 w-2 h-2 border-b-2 border-r-2 border-white/80" />
                    </div>
                </div>

                {/* Telemetry Overlay */}
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 to-transparent z-30 font-mono text-[10px] sm:text-xs">
                    <div className="flex justify-between text-taupe mb-1">
                        <span>[ TARGET ACQUIRED ]</span>
                        <span>PROCESSING...</span>
                    </div>
                    <div className="flex justify-between text-white font-bold tracking-wider">
                        <span>CONFIDENCE: {confidence}%</span>
                        <span>ESTIMATE: {attendance.toLocaleString()} PAX</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
