import hashlib
from datetime import datetime, timezone
from typing import Protocol

import httpx
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
        self._cached_live_ids: list[str] = []
        self._last_live_fetch_at: datetime | None = None

    def get_frames(
        self,
        event: Event,
        sample_size: int,
        camera_ids: list[str] | None = None,
    ) -> list[CameraFrame]:
        if self.settings.mock_empty_frames:
            return []

        frame_count = min(sample_size, self.settings.mock_frame_count)
        live_ids = self._get_live_camera_ids()
        selected_cameras = camera_ids or live_ids or [f"txdot-cam-{index + 1}" for index in range(frame_count)]
        frames: list[CameraFrame] = []
        minute_bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")

        for index in range(frame_count):
            camera_id = selected_cameras[index % len(selected_cameras)]
            seed = hashlib.sha256(f"{event.event_id}:{camera_id}:{index}:{minute_bucket}".encode()).hexdigest()
            fill_pct = 0.45 + (int(seed[:2], 16) / 255.0) * 0.5
            frames.append(
                CameraFrame(
                    camera_id=camera_id,
                    captured_at=datetime.now(timezone.utc),
                    estimated_parking_fill_pct=round(min(max(fill_pct, 0.0), 1.0), 4),
                )
            )
        return frames

    def _get_live_camera_ids(self) -> list[str]:
        if not self.settings.txdot_camera_catalog_url:
            return []

        now = datetime.now(timezone.utc)
        if (
            self._last_live_fetch_at is not None
            and (now - self._last_live_fetch_at).total_seconds() < self.settings.camera_catalog_refresh_seconds
        ):
            return self._cached_live_ids

        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(self.settings.txdot_camera_catalog_url)
                response.raise_for_status()
                payload = response.json()
            self._cached_live_ids = self._extract_camera_ids(payload)[:50]
            self._last_live_fetch_at = now
            return self._cached_live_ids
        except Exception:
            return self._cached_live_ids

    def _extract_camera_ids(self, payload: object) -> list[str]:
        collected: list[str] = []

        def walk(node: object) -> None:
            if isinstance(node, dict):
                for key in ("id", "cameraId", "camera_id", "name"):
                    value = node.get(key)
                    if isinstance(value, (str, int)):
                        text = str(value).strip()
                        if text and text not in collected and len(text) <= 80:
                            collected.append(text)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(payload)
        return collected
