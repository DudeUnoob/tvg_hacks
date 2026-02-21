import { useEffect, useRef } from 'react';
import gsap from 'gsap';

interface TelemetryBarProps {
    price?: number;
    load?: number;
}

export function TelemetryBar({ price = 42.50, load = 45000 }: TelemetryBarProps) {
    const tickerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Simple marquee animation
            gsap.to('.ticker-content', {
                xPercent: -50,
                ease: 'none',
                duration: 20,
                repeat: -1,
            });

            // Periodic flash for simulated spikes
            gsap.to('.spike-alert', {
                color: '#4F5D2F', // Olive Leaf
                textShadow: '0 0 10px rgba(79, 93, 47, 0.8)',
                duration: 0.5,
                repeat: -1,
                yoyo: true,
                repeatDelay: 5,
            });
        }, tickerRef);

        return () => ctx.revert();
    }, []);

    return (
        <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between h-14 px-6 bg-dark/80 backdrop-blur-md border-b border-white/10 tech-panel">

            {/* LEFT: Logo */}
            <div className="flex items-center gap-2">
                <span className="font-inter font-bold text-lg tracking-widest text-pale-slate">GRIDPULSE</span>
                <div className="w-2 h-2 rounded-full bg-lavender animate-pulse" style={{ boxShadow: '0 0 8px #CFD6EA' }} />
            </div>

            {/* CENTER: Telemetry Ticker */}
            <div
                ref={tickerRef}
                className="flex-1 max-w-2xl mx-8 overflow-hidden relative h-full flex items-center border-l border-r border-white/5 bg-dark-panel/50"
            >
                <div className="ticker-content flex whitespace-nowrap gap-12 text-sm font-mono text-grey-olive">
                    {/* Duplicate content for seamless scrolling */}
                    <div className="flex gap-12 items-center">
                        <span>[ ERCOT LIVE FEED ]</span>
                        <span>RTP: ${price.toFixed(2)}/MWh</span>
                        <span>LOAD: {load.toLocaleString()} MW</span>
                        <span className="spike-alert font-bold">WARNING: STRESS DETECTED IN SECTOR 7</span>
                        <span>RTP: ${price.toFixed(2)}/MWh</span>
                        <span>LOAD: {load.toLocaleString()} MW</span>
                    </div>
                    <div className="flex gap-12 items-center">
                        <span>[ ERCOT LIVE FEED ]</span>
                        <span>RTP: ${price.toFixed(2)}/MWh</span>
                        <span>LOAD: {load.toLocaleString()} MW</span>
                        <span className="spike-alert font-bold">WARNING: STRESS DETECTED IN SECTOR 7</span>
                        <span>RTP: ${price.toFixed(2)}/MWh</span>
                        <span>LOAD: {load.toLocaleString()} MW</span>
                    </div>
                </div>

                {/* Glow gradients on edges */}
                <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-dark-panel to-transparent z-10" />
                <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-dark-panel to-transparent z-10" />
            </div>

            {/* RIGHT: Status */}
            <div className="flex items-center gap-3 font-mono text-xs text-pale-slate uppercase tracking-wider">
                <span>System Status: Online</span>
                <div className="w-2 h-2 rounded-sm bg-olive" style={{ boxShadow: '0 0 8px #4F5D2F' }} />
            </div>

        </header>
    );
}
