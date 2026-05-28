"""Compare AGV dispatch policies across scenarios and seeds."""

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


SCENARIO_FILES = [
    "basic.yaml",
    "bottleneck_B.yaml",
    "congested.yaml",
    "agv_1.yaml",
    "agv_2.yaml",
    "agv_3.yaml",
]


POLICY_FACTORIES: dict[str, Callable[[], BasePolicy]] = {
    "fifo": FIFOPolicy,
    "nearest_job": NearestJobPolicy,
    "bottleneck_aware": BottleneckAwarePolicy,
}


def main() -> None:
    """Run a scenario x policy x seed comparison skeleton."""

    run_rows: list[dict[str, object]] = []

    for scenario_file in SCENARIO_FILES:
        config = load_config(PROJECT_ROOT / "config" / scenario_file)
        simulation_config = config.get("simulation", {})
        scenario_name = simulation_config.get("scenario_name", scenario_file.removesuffix(".yaml"))
        seeds = simulation_config.get("seeds", [simulation_config.get("random_seed", 42)])

        for seed in seeds:
            set_random_seed(int(seed))

            for policy_name, policy_factory in POLICY_FACTORIES.items():
                env = FactoryEnv(config=config, policy=policy_factory())
                metrics = env.run()
                run_row = {
                    "scenario": scenario_name,
                    "policy": policy_name,
                    "seed": seed,
                    **metrics,
                }
                run_rows.append(run_row)
                print(run_row)

    # TODO: Export run-level summary CSV to results/tables/run_summary.csv.
    # TODO: Export aggregated summary CSV to results/tables/aggregated_summary.csv.
    # TODO: Generate policy comparison plots in results/figures/.
    # TODO: Add complete metrics for throughput, average waiting time, bottleneck count,
    # process utilization, queue length over time, and AGV utilization.


if __name__ == "__main__":
    main()
