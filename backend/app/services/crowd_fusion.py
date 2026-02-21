from datetime import datetime, timezone

from app.models.crowd_signal import CrowdSignal
from app.models.event import Event
from app.models.forecast import Forecast


class CrowdFusionService:
    def build_forecast(self, event: Event, crowd_signal: CrowdSignal) -> Forecast:
        effective_confidence = crowd_signal.confidence
        if crowd_signal.fallback_used:
            effective_confidence = min(effective_confidence, 0.5)

        adjusted_attendance = int(
            round(
                (event.baseline_attendance * (1.0 - effective_confidence))
                + (crowd_signal.estimated_attendance * effective_confidence)
            )
        )
        adjustment_delta = adjusted_attendance - event.baseline_attendance

        reasoning_trace = (
            f"Baseline {event.baseline_attendance}; VLM estimate {crowd_signal.estimated_attendance} "
            f"at {crowd_signal.confidence * 100:.1f}% confidence. "
            f"{'Fallback path used. ' if crowd_signal.fallback_used else ''}"
            f"Adjusted forecast {adjusted_attendance} (delta {adjustment_delta:+d})."
        )

        return Forecast(
            event_id=event.event_id,
            generated_at=datetime.now(timezone.utc),
            baseline_attendance=event.baseline_attendance,
            vlm_estimated_attendance=crowd_signal.estimated_attendance,
            confidence=crowd_signal.confidence,
            adjusted_attendance=max(adjusted_attendance, 0),
            adjustment_delta=adjustment_delta,
            fallback_used=crowd_signal.fallback_used,
            reasoning_trace=reasoning_trace,
        )
