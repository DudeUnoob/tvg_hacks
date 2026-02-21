import { TelemetryBar } from './components/TelemetryBar';
import { HeroSection } from './components/HeroSection';
import { LiveFeedDashboard } from './components/LiveFeedDashboard';
import { DispatchTerminal } from './components/DispatchTerminal';
import { Footer } from './components/Footer';

export default function App() {
  return (
    <div className="min-h-screen bg-dark w-full overflow-x-hidden selection:bg-olive/30 selection:text-white pb-0">
      <TelemetryBar price={42.50} load={45902} />
      <HeroSection />
      <LiveFeedDashboard />
      <DispatchTerminal />
      <Footer />
    </div>
  );
}

