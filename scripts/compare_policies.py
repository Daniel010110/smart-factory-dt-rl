"""Compare baseline AGV dispatch policies."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from policies.fifo_policy import FIFOPolicy
from policies.nearest_job_policy import NearestJobPolicy
from simulator.factory_env import FactoryEnv
from utils.config_loader import load_config
from utils.seed import set_random_seed


def main() -> None:
    """Run baseline policies and print summary metrics."""

    config = load_config(PROJECT_ROOT / "config" / "default.yaml")
    set_random_seed(int(config.get("simulation", {}).get("random_seed", 42)))

    policies = {
        "fifo": FIFOPolicy(),
        "nearest_job": NearestJobPolicy(),
    }

    for name, policy in policies.items():
        env = FactoryEnv(config=config, policy=policy)
        metrics = env.run()
        print(f"{name}: {metrics}")

    # TODO: Export comparison tables and statistical summaries.
