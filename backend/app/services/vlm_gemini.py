import json
from datetime import datetime, timezone
from statistics import pvariance
from typing import Any

import httpx

from app.config import Settings
from app.models.crowd_signal import CrowdSignal
from app.models.event import Event
from app.services.frame_provider import CameraFrame


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


class GeminiCrowdEstimator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def estimate(self, event: Event, frames: list[CameraFrame]) -> CrowdSignal:
        if not frames:
            return CrowdSignal(
                event_id=event.event_id,
                observed_at=datetime.now(timezone.utc),
                camera_count=0,
                avg_parking_fill_pct=0.0,
                estimated_attendance=event.baseline_attendance,
                confidence=0.3,
                fallback_used=True,
                reasoning="No camera frames available; fallback to Layer 1 baseline attendance.",
            )

        if self.settings.mock_mode:
            return self._estimate_from_mock(event, frames, fallback_used=False)

        if not self.settings.gemini_api_key:
            return self._estimate_from_mock(event, frames, fallback_used=True)

        try:
            response = self._call_gemini(event, frames)
            return CrowdSignal(
                event_id=event.event_id,
                observed_at=datetime.now(timezone.utc),
                camera_count=len(frames),
                avg_parking_fill_pct=round(sum(frame.estimated_parking_fill_pct for frame in frames) / len(frames), 4),
                estimated_attendance=max(int(response["estimated_attendance"]), 0),
                confidence=_clamp(float(response["confidence"]), 0.0, 1.0),
                fallback_used=False,
                reasoning=str(response.get("reasoning", "Gemini-based crowd estimate generated.")),
            )
        except Exception:
            return self._estimate_from_mock(event, frames, fallback_used=True)

    def _estimate_from_mock(
        self,
        event: Event,
        frames: list[CameraFrame],
        fallback_used: bool,
    ) -> CrowdSignal:
        avg_fill = sum(frame.estimated_parking_fill_pct for frame in frames) / len(frames)
        fill_values = [frame.estimated_parking_fill_pct for frame in frames]
        variance = pvariance(fill_values) if len(fill_values) > 1 else 0.0

        crowd_multiplier = 0.72 + (avg_fill * 0.62)
        estimated_attendance = int(event.baseline_attendance * crowd_multiplier)

        confidence = 0.58 + min(len(frames), 5) * 0.05 - (variance * 0.45)
        confidence = _clamp(confidence, 0.35, 0.93)

        mode_label = "VLM" if self.settings.mock_mode else "fallback VLM"
        reasoning = (
            f"{mode_label} inferred attendance from {len(frames)} camera frames; "
            f"avg parking fill {avg_fill * 100:.1f}%."
        )
        return CrowdSignal(
            event_id=event.event_id,
            observed_at=datetime.now(timezone.utc),
            camera_count=len(frames),
            avg_parking_fill_pct=round(avg_fill, 4),
            estimated_attendance=max(estimated_attendance, 0),
            confidence=round(confidence, 4),
            fallback_used=fallback_used,
            reasoning=reasoning,
        )

    def _call_gemini(self, event: Event, frames: list[CameraFrame]) -> dict[str, Any]:
        frame_summary = ", ".join(
            f"{frame.camera_id}:{frame.estimated_parking_fill_pct:.2f}" for frame in frames
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Estimate event attendance from parking fill observations.\n"
                                f"Event: {event.name} at {event.venue}\n"
                                f"Baseline attendance: {event.baseline_attendance}\n"
                                f"Observed fills: {frame_summary}\n"
                                "Respond with strict JSON: "
                                '{"estimated_attendance": <int>, "confidence": <0-1 float>, "reasoning": "<short text>"}'
                            )
                        }
                    ]
                }
            ]
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent"
            f"?key={self.settings.gemini_api_key}"
        )
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()

        text = (
            body.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "{}")
        )
        parsed = json.loads(text)
        return {
            "estimated_attendance": parsed["estimated_attendance"],
            "confidence": parsed["confidence"],
            "reasoning": parsed.get("reasoning", "Gemini generated estimate."),
        }
