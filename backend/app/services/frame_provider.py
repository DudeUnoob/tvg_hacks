import hashlib
from datetime import datetime, timezone
from typing import Protocol

from pydantic import BaseModel, Field

from app.config import Settings
from app.models.event import Event


class CameraFrame(BaseModel):
    camera_id: str
    captured_at: datetime
    image_url: str | None = None
    estimated_parking_fill_pct: float = Field(ge=0.0, le=1.0)


class FrameProvider(Protocol):
    def get_frames(
        self,
        event: Event,
        sample_size: int,
        camera_ids: list[str] | None = None,
    ) -> list[CameraFrame]:
        ...


class MockFrameProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_frames(
        self,
        event: Event,
        sample_size: int,
        camera_ids: list[str] | None = None,
    ) -> list[CameraFrame]:
        if self.settings.mock_empty_frames:
            return []

        frame_count = min(sample_size, self.settings.mock_frame_count)
        selected_cameras = camera_ids or [f"txdot-cam-{index + 1}" for index in range(frame_count)]
        frames: list[CameraFrame] = []

        for index in range(frame_count):
            camera_id = selected_cameras[index % len(selected_cameras)]
            seed = hashlib.sha256(f"{event.event_id}:{camera_id}:{index}".encode()).hexdigest()
            fill_pct = 0.45 + (int(seed[:2], 16) / 255.0) * 0.5
            frames.append(
                CameraFrame(
                    camera_id=camera_id,
                    captured_at=datetime.now(timezone.utc),
                    estimated_parking_fill_pct=round(min(max(fill_pct, 0.0), 1.0), 4),
                )
            )
        return frames
