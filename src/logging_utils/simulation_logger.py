"""Step-level simulation logging."""

from pathlib import Path
from typing import Any

import pandas as pd


class SimulationLogger:
    """Collect and export step-level simulation records."""

    def __init__(
        self,
        scenario: str = "",
        policy_name: str = "",
        seed: int | None = None,
    ) -> None:
        self.scenario = scenario
        self.policy_name = policy_name
        self.seed = seed
        self.records: list[dict[str, Any]] = []

    def log_step(self, time: int, state: dict[str, object]) -> None:
        """Store a compact state record for one simulation step."""

        stations = state.get("stations", {})
        station_states = stations if isinstance(stations, dict) else {}
        process_a = station_states.get("ProcessA", {})
        process_b = station_states.get("ProcessB", {})
        process_c = station_states.get("ProcessC", {})

        record = {
            "scenario": self.scenario,
            "policy_name": self.policy_name,
            "seed": self.seed,
            "step": time,
            "queue_A": self._queue_length(process_a),
            "queue_B": self._queue_length(process_b),
            "queue_C": self._queue_length(process_c),
            "pending_tasks": state["pending_tasks"],
            "num_jobs_completed": state["completed_jobs"],
            "throughput": state["throughput"],
            "total_agv_distance": state["total_agv_distance"],
            "bottleneck_station": state["bottleneck_station"],
            "bottleneck_queue_length": state["bottleneck_queue_length"],
        }

        self.records.append(record)

    def _queue_length(self, station_state: object) -> int:
        """Return a queue length from a station state object."""

        if not isinstance(station_state, dict):
            return 0
        return int(station_state.get("queue_length", 0))

    def to_dataframe(self) -> pd.DataFrame:
        """Return records as a pandas DataFrame."""

        return pd.DataFrame(self.records)

    def export_csv(self, path: str | Path) -> None:
        """Export records to CSV."""

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_csv(output_path, index=False)
