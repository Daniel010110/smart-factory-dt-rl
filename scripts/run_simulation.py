"""Run a smart factory simulation with explicit config traceability."""

import argparse
from pathlib import Path
import sys
from typing import Callable

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


POLICY_FACTORIES: dict[str, Callable[[], BasePolicy]] = {
    "fifo": FIFOPolicy,
    "nearest": NearestJobPolicy,
    "nearest_job": NearestJobPolicy,
    "bottleneck_aware": BottleneckAwarePolicy,
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Run one smart factory simulation.")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config.")
    parser.add_argument("--policy", default="fifo", choices=sorted(POLICY_FACTORIES))
    parser.add_argument("--seed", type=int, default=None, help="Override simulation seed.")
    parser.add_argument("--max-steps", type=int, default=None, help="Override max simulation steps.")
    return parser.parse_args()


def main() -> None:
    """Run a single policy simulation and print traceable run metadata."""

    args = parse_args()
    config_path = (PROJECT_ROOT / args.config).resolve()
    config = load_config(config_path)

    scenario = config_path.stem
    simulation_config = config.get("simulation", {})
    seed = args.seed
    if seed is None:
        seed = int(simulation_config.get("seed", simulation_config.get("random_seed", 42)))
    max_steps = args.max_steps
    if max_steps is None:
        max_steps = int(simulation_config.get("max_steps", 100))

    policy_name = args.policy
    set_random_seed(seed)

    env = FactoryEnv(
        config=config,
        policy=POLICY_FACTORIES[policy_name](),
        scenario_name=scenario,
        policy_name=policy_name,
        seed=seed,
    )
    metrics = env.run(max_steps=max_steps)

    log_path = PROJECT_ROOT / "data" / "logs" / f"step_log_{scenario}_{policy_name}_seed{seed}.csv"
    env.logger.export_csv(log_path)

    run_summary = {
        "scenario": scenario,
        "policy_name": policy_name,
        "seed": seed,
        "max_steps": max_steps,
        "job_arrival_mode": _arrival_mode(config),
        "arrival_probability": _arrival_probability(config),
        "arrival_interval": _arrival_interval(config),
        "process_processing_times": _processing_times(config),
        "num_agvs": _num_agvs(config),
        "completed_jobs": metrics["completed_jobs"],
        "pending_tasks": metrics["pending_tasks"],
        "throughput": metrics["throughput"],
        "station_utilization": metrics["station_utilization"],
        "agv_total_distance": metrics["agv_total_distance"],
        "saved_log_path": str(log_path.relative_to(PROJECT_ROOT)),
    }
    print(run_summary)


def _arrival_mode(config: dict[str, object]) -> str:
    job_generation = config.get("job_generation", {})
    simulation = config.get("simulation", {})
    if isinstance(job_generation, dict) and "mode" in job_generation:
        return str(job_generation["mode"])
    if isinstance(job_generation, dict) and "arrival_probability" in job_generation:
        return "probability"
    if isinstance(simulation, dict) and "job_arrival_probability" in simulation:
        return "probability"
    return "interval"


def _arrival_probability(config: dict[str, object]) -> float | None:
    job_generation = config.get("job_generation", {})
    simulation = config.get("simulation", {})
    if isinstance(job_generation, dict) and "arrival_probability" in job_generation:
        return float(job_generation["arrival_probability"])
    if isinstance(simulation, dict) and "job_arrival_probability" in simulation:
        return float(simulation["job_arrival_probability"])
    return None


def _arrival_interval(config: dict[str, object]) -> int | None:
    job_generation = config.get("job_generation", {})
    simulation = config.get("simulation", {})
    if isinstance(job_generation, dict) and "arrival_interval" in job_generation:
        return int(job_generation["arrival_interval"])
    if isinstance(simulation, dict) and "job_interval" in simulation:
        return int(simulation["job_interval"])
    return None


def _processing_times(config: dict[str, object]) -> dict[str, int]:
    processes = config.get("processes", {})
    if isinstance(processes, dict) and processes:
        return {
            name: int(values.get("processing_time", 1))
            for name, values in processes.items()
            if isinstance(values, dict)
        }

    factory = config.get("factory", {})
    if isinstance(factory, dict):
        processing_times = factory.get("processing_times", {})
        if isinstance(processing_times, dict):
            return {name: int(value) for name, value in processing_times.items()}
    return {}


def _num_agvs(config: dict[str, object]) -> int:
    agv = config.get("agv", {})
    if isinstance(agv, dict) and "num_agvs" in agv:
        return int(agv["num_agvs"])

    factory = config.get("factory", {})
    if isinstance(factory, dict):
        return int(factory.get("agv_count", 1))
    return 1


if __name__ == "__main__":
    main()
