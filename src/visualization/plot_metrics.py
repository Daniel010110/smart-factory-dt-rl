"""Basic plotting helpers for simulation metrics."""

from pathlib import Path

import pandas as pd


def plot_completed_jobs_over_time(log_csv_path: str | Path, output_path: str | Path) -> None:
    """Plot completed jobs over time from a simulation log CSV."""

    import matplotlib.pyplot as plt

    data = pd.read_csv(log_csv_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(data["time"], data["completed_jobs"], label="Completed jobs")
    ax.set_xlabel("Time step")
    ax.set_ylabel("Completed jobs")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)

    # TODO: Add queue length, AGV utilization, and bottleneck-focused plots.
