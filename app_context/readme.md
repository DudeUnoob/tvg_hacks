Elevator Pitch
Austin's power grid is blind — it can't see a 100,000-person football game, a Moody Center sellout, or a new light rail corridor reshaping density across the city. GridPulse is a real-time AI simulator that turns crowd intelligence, live event data, and urban planning projections into actionable energy forecasts and battery dispatch commands — so the grid can finally see what's coming.

The Problem
Texas's grid, operated by ERCOT, faces a uniquely difficult challenge: demand is not just growing, it's increasingly spiky and hyperlocal. Standard grid forecasting models operate at the city or county level and plan for days or weeks ahead. But the most dangerous demand events happen at the neighborhood level, in hours — and they're caused by things that are entirely predictable if you know where to look.
Three specific gaps make this worse:
1. Crowds are invisible to the grid.
When 100,000 people leave DKR-Texas Memorial Stadium after a Longhorns game on a 99°F September night, they all go home and simultaneously blast their AC units. ERCOT has no signal for this. Base Power's battery dispatch system has no signal for this. The surge hits without warning, prices spike to $400–$9,000/MWh, and the grid strains at exactly the moment it matters most. The same applies to Moody Center concerts (up to 70,000 attendees), SXSW, ACL Festival, and Formula 1 at COTA — all massive, predictable, crowd-driven demand events that today are completely absent from energy forecasting models.
2. Weather multipliers are unaccounted for.
A Longhorns game in October draws the same crowd as one in September — but the energy impact is completely different. A 100°F game day can produce 3–4x the post-event AC load of a mild October night. No existing tool combines event crowd size × weather conditions × historical ERCOT load response into a unified, interactive forecast.
3. Urban infrastructure planning ignores grid capacity.
Austin is in the middle of its largest infrastructure expansion in decades. Project Connect — Austin's $8.23B light rail system — will build 15 stations along a 9.8-mile alignment with a new bridge across Lady Bird Lake and construction starting in 2027. Hundreds of new mixed-use developments, transit-oriented corridors, and densification zones are reshaping where people live and work. Each of these projects reshapes neighborhood-level energy demand for decades. Yet grid planners and urban designers operate in completely separate silos — infrastructure gets planned without grid impact modeling, and grid operators have no view into what the city is building next.

The Solution
GridPulse is a three-layer AI platform that synthesizes crowd intelligence, real-time weather, and urban planning data into an interactive energy simulation canvas — then outputs actionable battery pre-charge commands for Base Power's distributed fleet.

Layer 1 — Live Event Intelligence Engine
GridPulse ingests a continuous stream of Austin event data:
UT Austin athletic and academic event calendars (DKR capacity: 100,247)
Moody Center live schedule (capacity: ~15,000–70,000 depending on configuration)
Eventbrite, Ticketmaster, and venue APIs for concerts and conferences
Formula 1 COTA schedule, ACL Festival, SXSW official calendars
Each event is assigned a baseline crowd estimate, a geographic footprint, and a projected dispersal time — the moment when crowds leave and residential energy demand spikes. This is the foundational signal layer that makes everything downstream possible.

Layer 2 — VLM Crowd Confirmation (Real-Time Ground Truth)
Event calendar data gives us expected crowds. GridPulse adds a ground-truth confirmation layer using publicly accessible camera feeds and a Vision Language Model:
Gemini VLM analyzes live feeds from Austin's public TXDOT traffic cameras and campus parking infrastructure around DKR Stadium and Moody Center
The model estimates real-time parking lot fill percentage (e.g., "Lot 38 is 87% full at T-minus 45 minutes to kickoff")
This VLM estimate dynamically adjusts the crowd forecast up or down, correcting for weather cancellations, no-shows, and event underperformance
The output is a confidence-weighted crowd density signal that feeds directly into the load projection model
This is the novel data source at the core of GridPulse — no energy system today is using computer vision on live camera feeds as a grid input signal.

Layer 3 — The Interactive Simulation Canvas
This is GridPulse's central interface: a live Austin map that functions as an energy simulation environment. It has three modes:
Real-Time Mode
The map shows Austin right now — active events displayed as pulsing nodes, crowd density heat maps radiating outward from venues, and a live ERCOT price ticker in the corner. As events approach their end times, the system projects demand wave propagation through the surrounding zip codes, showing which neighborhoods will absorb returning crowds and how fast the load spike will travel.
Weather Pressure Test Mode (Mehak's addition)
A slider lets you toggle between weather scenarios for any active or upcoming event. Drag from 65°F to 102°F and watch the projected post-event AC load multiply in real time, neighborhood by neighborhood. A Longhorns game at 100°F doesn't just add 100,000 people's worth of demand — it adds 100,000 people all running 3-ton HVAC systems simultaneously the moment they walk in the door. This mode lets planners and operators instantly visualize worst-case energy scenarios before they happen.
Urban Planning Mode (the new layer)
This mode loads Austin's active urban development and infrastructure projects as map overlays:
All 15 Project Connect light rail stations and the proposed Lady Bird Lake bridge alignment
Austin's active capital improvement projects from the city's public Capital Projects Explorer
Approved zoning changes and densification corridors from Austin's open data portal
Users can click on any planned project — a new transit-oriented development near the South Congress station, for example — and GridPulse simulates the 5-year and 10-year energy demand footprint that development will create in that neighborhood. It shows: current grid capacity vs. projected load, whether existing transformer infrastructure can absorb it, and how many Base Power home batteries would need to be deployed in that zip code to buffer the new demand.
You can also add hypothetical buildings or corridors (the SimCity moment) — drop a proposed 800-unit apartment complex on the map near The Domain and instantly see the projected neighborhood load impact, the grid stress it creates, and the recommended infrastructure investment to handle it. Urban planners, developers, and grid operators all get answers to questions that today require weeks of separate analysis.

Layer 4 — Automated Dispatch Recommendation
All three layers feed a unified output: a ranked pre-charge recommendation for Base Power's distributed battery fleet.
The system outputs:
Which zip codes to pre-charge and by what percentage of capacity
When to initiate pre-charge (default: 2 hours before projected dispersal peak)
Why — a plain-English reasoning trace: "UT vs. Georgia, 99,000 attendance confirmed by VLM at 94% confidence. Weather: 101°F. Historical ERCOT data from similar events shows a 287MW demand spike in zip codes 78705, 78751, 78752 within 35 minutes of final whistle. Initiating pre-charge at 8:45pm for 3,400 Base batteries in target zones."
Revenue estimate — projected arbitrage captured by discharging during the spike vs. baseline dispatch, in dollars

