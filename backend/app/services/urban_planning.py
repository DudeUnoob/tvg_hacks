import math
from dataclasses import dataclass

from app.models.layer3 import (
    CapitalProject,
    UrbanSimulationResult,
    UrbanStation,
    ZoningCorridor,
)


@dataclass(frozen=True)
class _UrbanScenario:
    scenario_id: str
    scenario_name: str
    current_capacity_mw: float
    building_units: int
    commercial_sqft: int


class UrbanPlanningService:
    def get_project_connect_stations(self) -> list[UrbanStation]:
        return [
            UrbanStation(
                station_id="pc-001",
                name="South Congress",
                latitude=30.2506,
                longitude=-97.7491,
                corridor="Orange Line",
            ),
            UrbanStation(
                station_id="pc-002",
                name="Riverside",
                latitude=30.2459,
                longitude=-97.7162,
                corridor="Blue Line",
            ),
            UrbanStation(
                station_id="pc-003",
                name="UT West Mall",
                latitude=30.2861,
                longitude=-97.7394,
                corridor="Orange Line",
            ),
        ]

    def get_capital_projects(self) -> list[CapitalProject]:
        return [
            CapitalProject(
                project_id="cip-201",
                name="Downtown Distribution Upgrade",
                latitude=30.2704,
                longitude=-97.7437,
                status="active-design",
                estimated_budget_usd=42_000_000,
            ),
            CapitalProject(
                project_id="cip-202",
                name="East Austin Substation Expansion",
                latitude=30.2668,
                longitude=-97.7015,
                status="construction",
                estimated_budget_usd=67_500_000,
            ),
        ]

    def get_zoning_corridors(self) -> list[ZoningCorridor]:
        return [
            ZoningCorridor(
                corridor_id="zone-401",
                name="South Lamar Density Corridor",
                latitude=30.2513,
                longitude=-97.7632,
                zoning_type="mixed-use-high-density",
                density_multiplier=1.35,
            ),
            ZoningCorridor(
                corridor_id="zone-402",
                name="Domain TOD Overlay",
                latitude=30.4017,
                longitude=-97.7244,
                zoning_type="transit-oriented-development",
                density_multiplier=1.48,
            ),
        ]

    def simulate_project(
        self,
        project_id: str | None,
        project_name: str | None,
        horizon_years: int,
        building_units: int | None,
        commercial_sqft: int | None,
    ) -> UrbanSimulationResult:
        scenario = self._resolve_scenario(
            project_id=project_id,
            project_name=project_name,
            building_units=building_units,
            commercial_sqft=commercial_sqft,
        )

        horizon_factor = 1.0 + (0.09 if horizon_years >= 10 else 0.04)
        residential_mw = (scenario.building_units * 2.4) / 1000.0
        commercial_mw = (scenario.commercial_sqft * 0.011) / 1000.0
        projected_load_mw = (residential_mw + commercial_mw) * horizon_factor
        projected_load_mw = round(projected_load_mw, 4)

        transformer_headroom_mw = round(scenario.current_capacity_mw - projected_load_mw, 4)
        shortfall_mw = max(projected_load_mw - scenario.current_capacity_mw, 0.0)
        recommended_battery_count = math.ceil((shortfall_mw * 1000.0) / 13.5)

        if shortfall_mw > 2.5:
            stress = "high"
        elif shortfall_mw > 0.6:
            stress = "medium"
        else:
            stress = "low"

        return UrbanSimulationResult(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.scenario_name,
            horizon_years=horizon_years,
            projected_load_mw=projected_load_mw,
            current_capacity_mw=scenario.current_capacity_mw,
            transformer_headroom_mw=transformer_headroom_mw,
            recommended_battery_count=recommended_battery_count,
            grid_stress_level=stress,
        )

    def _resolve_scenario(
        self,
        project_id: str | None,
        project_name: str | None,
        building_units: int | None,
        commercial_sqft: int | None,
    ) -> _UrbanScenario:
        if project_id == "cip-201":
            return _UrbanScenario(
                scenario_id="cip-201",
                scenario_name="Downtown Distribution Upgrade",
                current_capacity_mw=4.8,
                building_units=900,
                commercial_sqft=450_000,
            )
        if project_id == "cip-202":
            return _UrbanScenario(
                scenario_id="cip-202",
                scenario_name="East Austin Substation Expansion",
                current_capacity_mw=6.2,
                building_units=1200,
                commercial_sqft=310_000,
            )

        scenario_name = project_name or "SimCity Hypothetical Build"
        return _UrbanScenario(
            scenario_id=project_id or "simcity-hypothetical",
            scenario_name=scenario_name,
            current_capacity_mw=3.6,
            building_units=building_units or 800,
            commercial_sqft=commercial_sqft or 180_000,
        )
