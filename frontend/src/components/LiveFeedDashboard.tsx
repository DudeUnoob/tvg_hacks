import { ThreatList } from './ThreatList';
import { VisionCamera } from './VisionCamera';
import { WeatherStress } from './WeatherStress';

export function LiveFeedDashboard() {
    return (
        <section className="relative z-20 max-w-[1440px] mx-auto px-6 -mt-32 mb-24">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <ThreatList />
                <VisionCamera />
                <WeatherStress />
            </div>
        </section>
    );
}
