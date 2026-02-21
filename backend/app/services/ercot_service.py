from datetime import datetime, timezone
import re
from typing import Any

import httpx

from app.config import Settings
from app.models.layer3 import ErcotSnapshot


class ErcotService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cached_snapshot: ErcotSnapshot | None = None
        self._last_fetch_at: datetime | None = None

    def get_realtime_snapshot(self) -> ErcotSnapshot:
        now = datetime.now(timezone.utc)
        if (
            self._cached_snapshot is not None
            and self._last_fetch_at is not None
            and (now - self._last_fetch_at).total_seconds() < self.settings.ercot_refresh_seconds
        ):
            return self._cached_snapshot

        if self.settings.ercot_source in {"ercot_public_api", "ercot_public", "live"}:
            public_snapshot = self._get_ercot_public_api_snapshot()
            if public_snapshot is not None:
                self._cached_snapshot = public_snapshot
                self._last_fetch_at = now
                return public_snapshot
            if self.settings.ercot_use_legacy_dashboard_fallback:
                legacy_snapshot = self._get_ercot_legacy_dashboard_snapshot()
                if legacy_snapshot is not None:
                    self._cached_snapshot = legacy_snapshot
                    self._last_fetch_at = now
                    return legacy_snapshot

        if self.settings.ercot_source in {"eia", "ercot_public_api", "ercot_public", "live"}:
            eia_snapshot = self._get_eia_snapshot()
            if eia_snapshot is not None:
                self._cached_snapshot = eia_snapshot
                self._last_fetch_at = now
                return eia_snapshot
            if self._cached_snapshot is not None:
                return self._cached_snapshot

        hour_mod = (now.hour % 6) * 0.03
        price = self.settings.ercot_mock_price_mwh * (1.0 + hour_mod)
        load = self.settings.ercot_mock_load_mw * (1.0 + (hour_mod / 2.0))
        mock_snapshot = ErcotSnapshot(
            price_mwh=round(price, 2),
            load_mw=round(load, 1),
            source="mock",
            updated_at=now,
        )
        self._cached_snapshot = mock_snapshot
        self._last_fetch_at = now
        return mock_snapshot

    def _get_ercot_public_api_snapshot(self) -> ErcotSnapshot | None:
        primary_key = (self.settings.ercot_subscription_key or "").strip()
        secondary_key = (self.settings.ercot_subscription_secondary_key or "").strip()
        keys = [key for key in [primary_key, secondary_key] if key]
        if not keys:
            return None

        seen: set[str] = set()
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            snapshot = self._fetch_public_api_snapshot_with_key(key)
            if snapshot is not None:
                return snapshot
        return None

    def _fetch_public_api_snapshot_with_key(self, subscription_key: str) -> ErcotSnapshot | None:
        headers = {
            "Accept": "application/json",
            "Ocp-Apim-Subscription-Key": subscription_key,
        }
        id_token = (self.settings.ercot_id_token or "").strip()
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"

        timeout = self.settings.ercot_api_timeout_seconds
        try:
            with httpx.Client(timeout=timeout) as client:
                endpoint_url = self._resolve_public_data_endpoint_url(client=client, headers=headers)
                response = client.get(endpoint_url, headers=headers)
                response.raise_for_status()
                payload = response.json()
            rows = self._extract_rows(payload)
            if not rows:
                return None

            price, price_time, load, load_time = self._extract_latest_price_and_load(rows)
            if price is None and load is None:
                return None

            source = "ercot-public-api"
            if price is None or load is None:
                eia_snapshot = self._get_eia_snapshot()
                if eia_snapshot is None:
                    return None
                if price is None:
                    price = eia_snapshot.price_mwh
                    price_time = eia_snapshot.updated_at
                if load is None:
                    load = eia_snapshot.load_mw
                    load_time = eia_snapshot.updated_at
                source = "ercot-public-api+eia-fill"

            if price is None or load is None:
                return None

            updated_at = max([item for item in [price_time, load_time] if item is not None], default=datetime.now(timezone.utc))
            return ErcotSnapshot(
                price_mwh=round(float(price), 2),
                load_mw=round(float(load), 1),
                source=source,
                updated_at=updated_at,
            )
        except Exception:
            return None

    def _resolve_public_data_endpoint_url(self, client: httpx.Client, headers: dict[str, str]) -> str:
        base_url = self.settings.ercot_api_base_url.rstrip("/")
        reports_path = self.settings.ercot_public_reports_path.strip("/")
        emil_id = self.settings.ercot_public_emil_id.strip().lower()
        operation = self.settings.ercot_public_operation.strip().strip("/")
        default_url = f"{base_url}/{reports_path}/{emil_id}/{operation}"

        if not self.settings.ercot_endpoint_discovery:
            return default_url

        try:
            metadata_url = f"{base_url}/{reports_path}/{emil_id}"
            metadata_resp = client.get(metadata_url, headers=headers)
            metadata_resp.raise_for_status()
            metadata = metadata_resp.json()
        except Exception:
            return default_url

        artifacts = metadata.get("artifacts")
        if not isinstance(artifacts, list):
            return default_url

        operation_slug = operation.lower()
        discovered: list[str] = []
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            endpoint_href = ((artifact.get("_links") or {}).get("endpoint") or {}).get("href")
            if not isinstance(endpoint_href, str):
                continue
            clean_href = endpoint_href.strip()
            if not clean_href:
                continue
            discovered.append(clean_href)
            if operation_slug and operation_slug in clean_href.lower():
                return clean_href

        if len(discovered) == 1:
            return discovered[0]
        return default_url

    def _extract_rows(self, payload: Any) -> list[dict[str, Any]]:
        candidates: list[list[dict[str, Any]]] = []

        def walk(node: Any) -> None:
            if isinstance(node, list):
                dict_items = [item for item in node if isinstance(item, dict)]
                if dict_items:
                    candidates.append(dict_items)
                for item in node:
                    walk(item)
            elif isinstance(node, dict):
                for value in node.values():
                    walk(value)

        walk(payload)
        if not candidates:
            return []
        return max(candidates, key=len)

    def _extract_latest_price_and_load(
        self, rows: list[dict[str, Any]]
    ) -> tuple[float | None, datetime | None, float | None, datetime | None]:
        price_value: float | None = None
        load_value: float | None = None
        price_time: datetime | None = None
        load_time: datetime | None = None

        for row in rows:
            row_time = self._parse_row_timestamp(row)
            row_price = self._parse_price_value(row)
            row_load = self._parse_load_value(row)

            if row_price is not None and (price_time is None or (row_time is not None and row_time >= price_time)):
                price_value = row_price
                price_time = row_time or price_time
            if row_load is not None and (load_time is None or (row_time is not None and row_time >= load_time)):
                load_value = row_load
                load_time = row_time or load_time

        return price_value, price_time, load_value, load_time

    @staticmethod
    def _normalize_key(name: str) -> str:
        return re.sub(r"[^a-z0-9]", "", name.strip().lower())

    def _parse_price_value(self, row: dict[str, Any]) -> float | None:
        values = {self._normalize_key(key): value for key, value in row.items()}
        prioritized = [
            "price",
            "pricemwh",
            "settlementpointprice",
            "spp",
            "lmp",
            "mcpc",
            "hbhubavg",
            "lzaen",
            "lzhouston",
        ]
        for key in prioritized:
            if key in values:
                parsed = self._to_float(values[key])
                if parsed is not None:
                    return parsed

        for key, value in values.items():
            if any(token in key for token in ["price", "spp", "lmp", "mcpc"]):
                parsed = self._to_float(value)
                if parsed is not None:
                    return parsed
        return None

    def _parse_load_value(self, row: dict[str, Any]) -> float | None:
        values = {self._normalize_key(key): value for key, value in row.items()}
        prioritized = [
            "systemload",
            "actualsystemload",
            "currentloadforecast",
            "forecastload",
            "loadmw",
            "load",
            "demandmw",
            "demand",
        ]
        for key in prioritized:
            if key in values:
                parsed = self._to_float(values[key])
                if parsed is not None:
                    return parsed

        for key, value in values.items():
            if ("load" in key or "demand" in key) and "price" not in key and "spp" not in key:
                parsed = self._to_float(value)
                if parsed is not None:
                    return parsed
        return None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return None

    def _parse_row_timestamp(self, row: dict[str, Any]) -> datetime | None:
        for key, value in row.items():
            normalized = self._normalize_key(key)
            if any(
                token in normalized
                for token in ["timestamp", "datetime", "intervalending", "deliverydate", "hourending", "time"]
            ):
                parsed = self._parse_timestamp_value(value)
                if parsed is not None:
                    return parsed
        return None

    @staticmethod
    def _parse_timestamp_value(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            epoch = float(value)
            if epoch > 10_000_000_000:
                epoch = epoch / 1000.0
            return datetime.fromtimestamp(epoch, tz=timezone.utc)

        text = str(value).strip()
        if not text:
            return None

        iso_candidate = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(iso_candidate)
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
        except ValueError:
            pass

        formats = [
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %I:%M:%S %p",
            "%Y-%m-%d",
            "%m/%d/%Y",
        ]
        for fmt in formats:
            try:
                parsed = datetime.strptime(text, fmt)
                return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
            except ValueError:
                continue
        return None

    def _get_ercot_legacy_dashboard_snapshot(self) -> ErcotSnapshot | None:
        try:
            with httpx.Client(timeout=8.0) as client:
                price_resp = client.get(f"{self.settings.ercot_public_base_url}/system-wide-prices.json")
                demand_resp = client.get(f"{self.settings.ercot_public_base_url}/system-wide-demand.json")
                price_resp.raise_for_status()
                demand_resp.raise_for_status()
                price_body = price_resp.json()
                demand_body = demand_resp.json()

            rt_series = price_body.get("rtSppData", [])
            demand_series = ((demand_body.get("currentDay") or {}).get("data")) or []
            if not rt_series or not demand_series:
                return None

            latest_price = rt_series[-1]
            latest_demand = next(
                (
                    row
                    for row in reversed(demand_series)
                    if row.get("systemLoad") is not None or row.get("currentLoadForecast") is not None
                ),
                demand_series[-1],
            )
            price = latest_price.get("lzAen")
            if price is None:
                price = latest_price.get("hbHubAvg")
            if price is None:
                price = latest_price.get("lzHouston")
            load = latest_demand.get("systemLoad")
            if load is None:
                load = latest_demand.get("currentLoadForecast")
            timestamp = latest_demand.get("timestamp") or latest_price.get("timestamp")
            if price is None or load is None or timestamp is None:
                return None

            parsed = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S%z")
            updated_at = parsed.astimezone(timezone.utc)
            return ErcotSnapshot(
                price_mwh=round(float(price), 2),
                load_mw=round(float(load), 1),
                source="ercot-dashboard-legacy",
                updated_at=updated_at,
            )
        except Exception:
            return None

    def _get_eia_snapshot(self) -> ErcotSnapshot | None:
        query = {
            "api_key": self.settings.eia_api_key,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": "ERCO",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": "0",
            "length": "12",
        }
        try:
            with httpx.Client(timeout=9.0) as client:
                response = client.get(
                    "https://api.eia.gov/v2/electricity/rto/region-data/data/",
                    params=query,
                )
                response.raise_for_status()
                body = response.json()
            rows = body.get("response", {}).get("data", [])
            if not rows:
                return None

            demand = next((row for row in rows if row.get("type") == "D"), rows[0])
            forecast = next((row for row in rows if row.get("type") == "DF"), demand)
            load_mw = float(demand["value"])
            forecast_mw = float(forecast["value"])
            # EIA does not expose instant ERCOT price in this dataset. Estimate price from demand tightness.
            tightness = load_mw / max(forecast_mw, 1.0)
            price_mwh = max(28.0, min(900.0, 64.0 + (tightness - 0.9) * 520.0 + (load_mw - 42000.0) * 0.006))
            period = datetime.fromisoformat(str(demand["period"]).replace("Z", "+00:00"))
            updated_at = period.replace(tzinfo=timezone.utc) if period.tzinfo is None else period.astimezone(
                timezone.utc
            )

            return ErcotSnapshot(
                price_mwh=round(price_mwh, 2),
                load_mw=round(load_mw, 1),
                source="eia-derived",
                updated_at=updated_at,
            )
        except Exception:
            return None

    @staticmethod
    def comparable_signal(temperature_f: float, adjusted_attendance: int) -> str:
        if temperature_f >= 100 and adjusted_attendance >= 90_000:
            return "Historical profile: major game + extreme heat demand spike"
        if adjusted_attendance >= 40_000:
            return "Historical profile: major event return-home surge"
        return "Historical profile: medium event evening recovery wave"
