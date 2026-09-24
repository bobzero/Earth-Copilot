# Austin Fab Cooling Tower Operations Standard

**Facility scope:** `tx-fab-austin-01`, `tx-fab-austin-02`

## Design envelope

- Wet bulb ambient design: 78 °F.
- Approach temperature: 7 °F (process water to wet bulb).
- Combined cooling-tower capacity (shared farm): 25,000 m³/day.
- Single-tower fail-safe minimum: 18,000 m³/day across both fabs.

## Heat-stressed operating modes

When forecast dry-bulb temperature exceeds **100 °F**:

- Switch to **Mode H1**: increase blowdown to maintain cycles-of-concentration, accept water-usage hit.
- Notify Water Utilities Coordinator to confirm raw-water makeup supply.
- Verify chemistry: chlorine residual ≥ 0.5 ppm; pH 7.6–8.2.

When forecast exceeds **103 °F** for ≥ 2 days:

- Switch to **Mode H2**: pre-chill process water reservoir overnight.
- Coordinate with Plant Engineering to defer non-critical thermal loads.
- Brief on-call Fab Manager on potential wafer-start curtailment.

## Failure modes

- Loss of one tower at > 100 °F ambient: triggers Mode H2 even if forecast was Mode H1.
- ERCOT EEA-2: fan-VFD load shed of 10% is acceptable in Mode H1, **not** in Mode H2.

## Cross-references

- Heat Dome Business Continuity Playbook — Texas Operations
- Water Supply Contingency — Austin Site
