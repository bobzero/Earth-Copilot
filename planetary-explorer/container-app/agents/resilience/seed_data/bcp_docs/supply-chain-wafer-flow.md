# Supply Chain Continuity — Wafer Flow Austin → San Antonio

**Edge scope:** wafer shipments `tx-fab-austin-01` → `tx-asm-san-antonio-01` (and Fab 2 → SA Assembly).

## Normal-mode profile

- Cadence: daily ground freight, climate-controlled.
- Lead time: 2 days fab-out to assembly-in.
- Volume baseline: 1.0× (Fab 1), 0.8× (Fab 2) on the resilience model's weekly scale.

## Disruption scenarios

### Heat dome (≥ 100 °F at Austin or San Antonio)

- Wafer transit is **not** at risk in transit (climate-controlled trailers).
- Bottleneck is **fab-side wafer-start curtailment** under cooling stress.
- Mitigations:
  - Pull forward 1 day of inventory from sub-assembly buffer at Waco.
  - Stretch San Antonio test cycle by 4 hours to absorb upstream slip.

### Wildfire (smoke at Austin)

- Outdoor air quality impacts cleanroom makeup air filtering.
- Mitigations:
  - Switch to recirculation-favored air-handler mode.
  - Defer planned cleanroom maintenance until AQI < 100.

### San Antonio assembly heat stress

- If San Antonio test floor heat-stressed, route a fraction of finished wafers
  directly to El Paso packaging (skip-test pilot lots only — engineering must
  approve per lot).

## Decision rights

- Disruption-mode reroute requires Director of Operations sign-off.
- Skip-test rerouting requires QE + ME concurrence.
