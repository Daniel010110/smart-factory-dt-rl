"""Skeleton tests for initial project structure."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from policies.fifo_policy import FIFOPolicy
from simulator.factory_env import FactoryEnv
from simulator.layout import Layout
from utils.config_loader import load_config


def test_layout_manhattan_distance() -> None:
    """Layout should calculate Manhattan distance."""

    layout = Layout({"A": (0, 0), "B": (3, 2)})
    assert layout.manhattan_distance("A", "B") == 5


def test_factory_env_core_methods() -> None:
    """FactoryEnv should expose the expected MVP API."""

    config = load_config(PROJECT_ROOT / "config" / "default.yaml")
    env = FactoryEnv(config=config, policy=FIFOPolicy())

    assert isinstance(env.reset(), dict)
    assert isinstance(env.step(), dict)
    assert isinstance(env.get_state(), dict)
    assert isinstance(env.collect_metrics(), dict)


def test_factory_env_run_returns_metrics() -> None:
    """A short simulation run should return metrics."""

    config = load_config(PROJECT_ROOT / "config" / "default.yaml")
    env = FactoryEnv(config=config, policy=FIFOPolicy())

    metrics = env.run(max_steps=5)

    assert "completed_jobs" in metrics
    assert "station_utilization" in metrics
