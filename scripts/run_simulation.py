"""Run a minimal smart factory simulation."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from policies.fifo_policy import FIFOPolicy
from simulator.factory_env import FactoryEnv
from utils.config_loader import load_config
from utils.seed import set_random_seed


def main() -> None:
    """Run the default FIFO-policy simulation."""

    config = load_config(PROJECT_ROOT / "config" / "default.yaml")
    set_random_seed(int(config.get("simulation", {}).get("random_seed", 42)))

    env = FactoryEnv(config=config, policy=FIFOPolicy())
    metrics = env.run()

    output_path = config.get("logging", {}).get("output_path", "data/logs/simulation_log.csv")
    env.logger.export_csv(PROJECT_ROOT / output_path)
    print(metrics)


if __name__ == "__main__":
    main()
