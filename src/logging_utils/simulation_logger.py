"""Step-level simulation logging."""

from pathlib import Path
from typing import Any

import pandas as pd


class SimulationLogger:
    """Collect and export step-level simulation records."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def log_step(self, time: int, state: dict[str, object]) -> None:
        """Store a compact state record for one simulation step."""

        record = {
            "time": time,
            "pending_tasks": state["pending_tasks"],
            "completed_jobs": state["completed_jobs"],
        }

        stations = state.get("stations", {})
        if isinstance(stations, dict):
            for name, station_state in stations.items():
                if isinstance(station_state, dict):
                    record[f"{name}_queue_length"] = station_state.get("queue_length")
                    record[f"{name}_utilization"] = station_state.get("utilization")

        self.records.append(record)

    def to_dataframe(self) -> pd.DataFrame:
        """Return records as a pandas DataFrame."""

        return pd.DataFrame(self.records)

    def export_csv(self, path: str | Path) -> None:
        """Export records to CSV."""

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_csv(output_path, index=False)
