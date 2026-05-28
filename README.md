# smart-factory-dt-rl

A research-oriented Python project for studying AGV dispatching policies in a 2D smart factory digital twin.

## MVP Research Topic

**Performance analysis of bottleneck-aware AGV dispatching policies in a 2D smart factory digital twin.**

The first real result will compare baseline and bottleneck-aware dispatch policies across controlled factory scenarios. The simulator is still intentionally small, but the project direction is now experiment-first: define scenarios, run comparable policies, collect metrics, and build toward publishable analysis.

## Factory Flow

```text
Input -> ProcessA -> ProcessB -> ProcessC -> Output
```

Initial scope:

- 1 to 3 AGVs
- Job generation
- Process queues with fixed processing times
- AGV transport tasks
- FIFO, nearest-job, and bottleneck-aware dispatch policies
- Step-level logging
- Scenario-based policy comparison

## Policies

- `FIFO`: select the oldest pending transport task.
- `Nearest-job`: select the task with the nearest pickup location.
- `Bottleneck-aware`: prefer tasks that relieve the current bottleneck and avoid sending more jobs into it.

The bottleneck-aware policy is currently a skeleton. Its intended score combines task age, AGV distance, bottleneck relief, and bottleneck inflow penalty.

## Metrics

Target experiment metrics:

- `completed_jobs`
- `throughput`
- `average_waiting_time`
- `total_agv_distance`
- `bottleneck_count`
- `process_utilization`
- `queue_length_over_time`
- `agv_utilization`

Some metrics are not fully implemented yet and are tracked as TODOs in the simulation and comparison code.

## Scenarios

Scenario config files live in `config/`:

- `basic.yaml`: similar processing times at ProcessA/B/C.
- `bottleneck_B.yaml`: ProcessB has much larger processing time.
- `congested.yaml`: high job arrival pressure.
- `agv_1.yaml`: one AGV.
- `agv_2.yaml`: two AGVs.
- `agv_3.yaml`: three AGVs.

## Project Structure

```text
config/                 Experiment scenario configurations
data/logs/              Step-level simulation logs
reports/                Research notes and generated reports
results/figures/        Policy comparison plots
results/tables/         Run-level and aggregated summary CSVs
scripts/                Experiment entry points
src/
  logging_utils/        Simulation logging helpers
  policies/             AGV dispatch policies
  simulator/            Core factory simulation entities
  utils/                Config and reproducibility utilities
  visualization/        Plotting helpers
tests/                  Skeleton tests
```

## Quick Start

```bash
python -m venv .venv
pip install -r requirements.txt
python scripts/run_simulation.py
python scripts/compare_policies.py
pytest
```

## Current Scope

The current codebase provides safe, minimal class skeletons and simple placeholder behavior. It does not yet implement complex path planning, collision avoidance, 3D simulation, reinforcement learning dependencies, or a Gymnasium environment.

## Research Roadmap

TODO:

- Implement complete run-level metrics for throughput, waiting time, bottleneck count, and AGV utilization.
- Export run-level summary CSV files.
- Export aggregated scenario × policy summary CSV files.
- Add policy comparison plots for throughput, distance, waiting time, utilization, and queue dynamics.
- Expand bottleneck-aware policy inputs to include live station queue lengths and utilization.
- Add richer event semantics for job release, station completion, and AGV pickup/drop-off.
- Add a Gymnasium-compatible environment only after the simulator API stabilizes.
