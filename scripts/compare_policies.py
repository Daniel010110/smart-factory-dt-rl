"""Run policy comparison experiments and export summary CSV files."""

import argparse
from pathlib import Path
import sys
from typing import Callable

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from policies.base_policy import BasePolicy
from policies.bottleneck_aware_policy import BottleneckAwarePolicy
from policies.fifo_policy import FIFOPolicy
from policies.nearest_job_policy import NearestJobPolicy
from simulator.factory_env import FactoryEnv
from utils.config_loader import load_config
from utils.seed import set_random_seed


DEFAULT_CONFIGS = [
    "config/basic.yaml",
    "config/bottleneck_B.yaml",
    "config/congested.yaml",
]

DEFAULT_POLICIES = ["fifo", "nearest", "bottleneck_aware"]
DEFAULT_SEEDS = [42]

POLICY_FACTORIES: dict[str, Callable[[], BasePolicy]] = {
    "fifo": FIFOPolicy,
    "nearest": NearestJobPolicy,
    "nearest_job": NearestJobPolicy,
    "bottleneck_aware": BottleneckAwarePolicy,
}


def parse_args() -> argparse.Namespace:
    """Parse experiment runner arguments."""

    parser = argparse.ArgumentParser(description="Compare AGV dispatch policies.")
    parser.add_argument("--configs", nargs="+", default=DEFAULT_CONFIGS)
    parser.add_argument("--policies", nargs="+", default=DEFAULT_POLICIES)
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--output-dir", default="results/tables")
    return parser.parse_args()


def main() -> None:
    """Run scenario x policy x seed experiments and export summaries."""

    args = parse_args()
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    run_rows: list[dict[str, object]] = []

    for config_arg in args.configs:
        config_path = (PROJECT_ROOT / config_arg).resolve()
        config = load_config(config_path)
        scenario = config_path.stem
        max_steps = _max_steps(config, args.max_steps)

        for policy_name in args.policies:
            if policy_name not in POLICY_FACTORIES:
                raise ValueError(f"Unknown policy: {policy_name}")

            for seed in args.seeds:
                set_random_seed(seed)
                env = FactoryEnv(
                    config=config,
                    policy=POLICY_FACTORIES[policy_name](),
                    scenario_name=scenario,
                    policy_name=policy_name,
                    seed=seed,
                )
                metrics = env.run(max_steps=max_steps)

                step_log_path = (
                    PROJECT_ROOT
                    / "data"
                    / "logs"
                    / f"step_log_{scenario}_{policy_name}_seed{seed}.csv"
                )
                env.logger.export_csv(step_log_path)

                step_log = env.logger.to_dataframe()
                run_rows.append(
                    _build_run_row(
                        scenario=scenario,
                        policy_name=policy_name,
                        seed=seed,
                        max_steps=max_steps,
                        config=config,
                        metrics=metrics,
                        env=env,
                        step_log=step_log,
                    )
                )

    runs = pd.DataFrame(run_rows, columns=_run_columns())
    runs_path = output_dir / "policy_comparison_runs.csv"
    runs.to_csv(runs_path, index=False)

    agg = _aggregate_runs(runs)
    agg_path = output_dir / "policy_comparison_agg.csv"
    agg.to_csv(agg_path, index=False)

    print("\nRun-level summary:")
    print(runs.to_string(index=False))
    print(f"\nSaved run summary: {runs_path.relative_to(PROJECT_ROOT)}")
    print(f"Saved aggregate summary: {agg_path.relative_to(PROJECT_ROOT)}")


def _build_run_row(
    scenario: str,
    policy_name: str,
    seed: int,
    max_steps: int,
    config: dict[str, object],
    metrics: dict[str, object],
    env: FactoryEnv,
    step_log: pd.DataFrame,
) -> dict[str, object]:
    """Build one run-level summary row."""

    station_utilization = metrics.get("station_utilization", {})
    if not isinstance(station_utilization, dict):
        station_utilization = {}

    threshold = _bottleneck_threshold(config)
    bottleneck_a = step_log["queue_A"] >= threshold
    bottleneck_b = step_log["queue_B"] >= threshold
    bottleneck_c = step_log["queue_C"] >= threshold

    return {
        "scenario": scenario,
        "policy": policy_name,
        "seed": seed,
        "max_steps": max_steps,
        "num_agvs": _num_agvs(config),
        "completed_jobs": metrics["completed_jobs"],
        "throughput": metrics["throughput"],
        "pending_tasks": metrics["pending_tasks"],
        "total_agv_distance": metrics["agv_total_distance"],
        "avg_agv_utilization": _avg_agv_utilization(env),
        "util_A": station_utilization.get("ProcessA", 0.0),
        "util_B": station_utilization.get("ProcessB", 0.0),
        "util_C": station_utilization.get("ProcessC", 0.0),
        "avg_queue_A": step_log["queue_A"].mean(),
        "avg_queue_B": step_log["queue_B"].mean(),
        "avg_queue_C": step_log["queue_C"].mean(),
        "max_queue_A": step_log["queue_A"].max(),
        "max_queue_B": step_log["queue_B"].max(),
        "max_queue_C": step_log["queue_C"].max(),
        "bottleneck_count": (bottleneck_a | bottleneck_b | bottleneck_c).sum(),
        "bottleneck_count_A": bottleneck_a.sum(),
        "bottleneck_count_B": bottleneck_b.sum(),
        "bottleneck_count_C": bottleneck_c.sum(),
    }


def _aggregate_runs(runs: pd.DataFrame) -> pd.DataFrame:
    """Aggregate numeric run metrics by scenario and policy."""

    metric_columns = [
        column
        for column in runs.select_dtypes(include="number").columns
        if column != "seed"
    ]
    agg = runs.groupby(["scenario", "policy"], as_index=False)[metric_columns].agg(["mean", "std"])
    agg.columns = [
        "_".join(part for part in column if part)
        if isinstance(column, tuple)
        else column
        for column in agg.columns
    ]
    return agg.fillna({column: 0 for column in agg.columns if column.endswith("_std")})


def _max_steps(config: dict[str, object], override: int | None) -> int:
    if override is not None:
        return override
    simulation = config.get("simulation", {})
    if isinstance(simulation, dict):
        return int(simulation.get("max_steps", 100))
    return 100


def _num_agvs(config: dict[str, object]) -> int:
    agv = config.get("agv", {})
    if isinstance(agv, dict) and "num_agvs" in agv:
        return int(agv["num_agvs"])

    factory = config.get("factory", {})
    if isinstance(factory, dict):
        return int(factory.get("agv_count", 1))
    return 1


def _avg_agv_utilization(env: FactoryEnv) -> float:
    utilizations = []
    for agv in env.agvs:
        total_time = agv.busy_time + agv.idle_time
        utilizations.append(agv.busy_time / total_time if total_time else 0.0)
    return sum(utilizations) / len(utilizations) if utilizations else 0.0


def _bottleneck_threshold(config: dict[str, object]) -> int:
    metrics = config.get("metrics", {})
    if isinstance(metrics, dict):
        return int(metrics.get("bottleneck_queue_threshold", 1))
    return 1


def _run_columns() -> list[str]:
    return [
        "scenario",
        "policy",
        "seed",
        "max_steps",
        "num_agvs",
        "completed_jobs",
        "throughput",
        "pending_tasks",
        "total_agv_distance",
        "avg_agv_utilization",
        "util_A",
        "util_B",
        "util_C",
        "avg_queue_A",
        "avg_queue_B",
        "avg_queue_C",
        "max_queue_A",
        "max_queue_B",
        "max_queue_C",
        "bottleneck_count",
        "bottleneck_count_A",
        "bottleneck_count_B",
        "bottleneck_count_C",
    ]


if __name__ == "__main__":
    main()
