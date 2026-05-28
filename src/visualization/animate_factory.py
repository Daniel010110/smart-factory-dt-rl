"""2D factory animation utilities for step-level simulation logs."""

from pathlib import Path
import re

import pandas as pd
from matplotlib.animation import FuncAnimation, PillowWriter


LAYOUT = {
    "Input": (0.0, 0.0),
    "ProcessA": (2.0, 0.0),
    "ProcessB": (4.0, 0.0),
    "ProcessC": (6.0, 0.0),
    "Output": (8.0, 0.0),
}

QUEUE_COLUMNS = {
    "ProcessA": "queue_A",
    "ProcessB": "queue_B",
    "ProcessC": "queue_C",
}


def animate_factory_log(
    log_csv_path: str | Path,
    output_path: str | Path,
    fps: int = 5,
    step_interval: int = 2,
) -> Path:
    """Create a GIF animation from a step-level simulation log CSV."""

    import matplotlib.pyplot as plt

    log_path = Path(log_csv_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(log_path)
    if data.empty:
        raise ValueError(f"Step log is empty: {log_path}")
    for queue_column in QUEUE_COLUMNS.values():
        if queue_column not in data.columns:
            data[queue_column] = 0

    frames = data.iloc[:: max(1, step_interval)].reset_index(drop=True)
    agv_location_columns = _find_agv_location_columns(frames)
    agv_xy_columns = _find_agv_xy_columns(frames)
    max_queue = max(1, int(frames[list(QUEUE_COLUMNS.values())].max().max()))

    fig, ax = plt.subplots(figsize=(11, 5))

    def update(frame_index: int) -> None:
        row = frames.iloc[frame_index]
        ax.clear()
        _draw_layout(ax, row)
        _draw_queues(ax, row, max_queue)
        _draw_bottleneck(ax, row)

        if agv_location_columns:
            _draw_agvs_from_locations(ax, row, agv_location_columns)
        elif agv_xy_columns:
            _draw_agvs_from_xy(ax, row, agv_xy_columns)
        else:
            # TODO: Add AGV location columns to step logs for true movement replay.
            ax.text(4.0, -1.25, "AGV locations not available in log", ha="center", fontsize=9)

        _draw_metadata(ax, row)
        ax.set_xlim(-0.8, 8.8)
        ax.set_ylim(-1.6, 3.2 + max_queue * 0.15)
        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")

    animation = FuncAnimation(fig, update, frames=len(frames), interval=1000 / max(1, fps))
    animation.save(output, writer=PillowWriter(fps=fps))
    plt.close(fig)
    return output


def default_animation_output_path(log_csv_path: str | Path) -> Path:
    """Return the default output GIF path for a step log."""

    log_path = Path(log_csv_path)
    name = log_path.stem
    if name.startswith("step_log_"):
        name = name.removeprefix("step_log_")
    return Path("results") / "animations" / f"factory_{name}.gif"


def _draw_layout(ax, row: pd.Series) -> None:
    """Draw the fixed factory layout."""

    bottleneck_station = str(row.get("bottleneck_station", ""))
    x_values = [position[0] for position in LAYOUT.values()]
    y_values = [position[1] for position in LAYOUT.values()]
    ax.plot(x_values, y_values, color="#777777", linewidth=2, zorder=1)

    for station, (x, y) in LAYOUT.items():
        facecolor = "#f8f8f8"
        edgecolor = "#333333"
        linewidth = 1.5
        if station == bottleneck_station:
            facecolor = "#ffe6e6"
            edgecolor = "#c62828"
            linewidth = 2.5

        ax.scatter([x], [y], s=900, marker="s", facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth, zorder=3)
        ax.text(x, y, station, ha="center", va="center", fontsize=9, zorder=4)


def _draw_queues(ax, row: pd.Series, max_queue: int) -> None:
    """Draw process queue lengths as bars above stations."""

    for station, queue_column in QUEUE_COLUMNS.items():
        x, y = LAYOUT[station]
        queue_length = int(row.get(queue_column, 0))
        height = 0.25 + 1.6 * queue_length / max_queue
        ax.bar(
            x,
            height,
            width=0.6,
            bottom=y + 0.65,
            color="#4c78a8",
            alpha=0.8,
            zorder=2,
        )
        ax.text(x, y + 0.95 + height, f"Q={queue_length}", ha="center", fontsize=9)


def _draw_bottleneck(ax, row: pd.Series) -> None:
    """Draw bottleneck label if present."""

    station = row.get("bottleneck_station")
    if not isinstance(station, str) or station not in LAYOUT:
        return

    x, y = LAYOUT[station]
    queue_length = row.get("bottleneck_queue_length", "")
    ax.text(
        x,
        y + 2.75,
        f"Bottleneck: {station} (Q={queue_length})",
        ha="center",
        fontsize=10,
        color="#b71c1c",
        weight="bold",
    )


def _draw_agvs_from_locations(ax, row: pd.Series, columns: list[str]) -> None:
    """Draw AGV markers from station-name location columns."""

    for index, column in enumerate(columns):
        location = row.get(column)
        if not isinstance(location, str) or location not in LAYOUT:
            continue

        x, y = LAYOUT[location]
        y_offset = -0.45 - 0.18 * index
        ax.scatter([x], [y + y_offset], s=180, marker="o", color="#f58518", edgecolor="#222222", zorder=5)
        ax.text(x, y + y_offset, _agv_label(column), ha="center", va="center", fontsize=8, zorder=6)


def _draw_agvs_from_xy(ax, row: pd.Series, columns: dict[str, tuple[str, str]]) -> None:
    """Draw AGV markers from numeric x/y columns."""

    for label, (x_column, y_column) in columns.items():
        x = row.get(x_column)
        y = row.get(y_column)
        if pd.isna(x) or pd.isna(y):
            continue
        ax.scatter([float(x)], [float(y) - 0.45], s=180, marker="o", color="#f58518", edgecolor="#222222", zorder=5)
        ax.text(float(x), float(y) - 0.45, label, ha="center", va="center", fontsize=8, zorder=6)


def _draw_metadata(ax, row: pd.Series) -> None:
    """Draw run and step metadata."""

    scenario = row.get("scenario", "")
    policy = row.get("policy_name", "")
    step = row.get("step", "")
    completed = row.get("num_jobs_completed", "")
    throughput = float(row.get("throughput", 0.0))
    pending = row.get("pending_tasks", "")

    title = f"Scenario: {scenario} | Policy: {policy} | Step: {step}"
    ax.text(-0.65, 3.0, title, ha="left", fontsize=12, weight="bold")
    ax.text(
        -0.65,
        2.65,
        f"Completed jobs: {completed}   Throughput: {throughput:.3f}   Pending tasks: {pending}",
        ha="left",
        fontsize=10,
    )


def _find_agv_location_columns(data: pd.DataFrame) -> list[str]:
    """Find AGV location columns, if the log contains them."""

    pattern = re.compile(r"agv.*location", re.IGNORECASE)
    return [column for column in data.columns if pattern.search(column)]


def _find_agv_xy_columns(data: pd.DataFrame) -> dict[str, tuple[str, str]]:
    """Find AGV x/y column pairs, if the log contains them."""

    pairs: dict[str, tuple[str, str]] = {}
    for column in data.columns:
        match = re.match(r"(agv[_-]?\d+)[_-]x$", column, re.IGNORECASE)
        if not match:
            continue
        label = match.group(1).replace("_", "").upper()
        y_column = re.sub(r"[_-]x$", "_y", column, flags=re.IGNORECASE)
        if y_column in data.columns:
            pairs[label] = (column, y_column)
    return pairs


def _agv_label(column: str) -> str:
    """Create a compact AGV label from a log column name."""

    match = re.search(r"(\d+)", column)
    return f"AGV{match.group(1)}" if match else "AGV"
