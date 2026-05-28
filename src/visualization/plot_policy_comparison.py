"""Policy comparison plotting utilities."""

from pathlib import Path

import pandas as pd


PLOT_SPECS = [
    ("completed_jobs_mean", "completed_jobs_std", "Completed jobs", "completed_jobs_by_policy.png"),
    ("throughput_mean", "throughput_std", "Throughput", "throughput_by_policy.png"),
    (
        "total_agv_distance_mean",
        "total_agv_distance_std",
        "Total AGV distance",
        "total_agv_distance_by_policy.png",
    ),
    (
        "bottleneck_count_mean",
        "bottleneck_count_std",
        "Bottleneck count",
        "bottleneck_count_by_policy.png",
    ),
    (
        "avg_agv_utilization_mean",
        "avg_agv_utilization_std",
        "Average AGV utilization",
        "avg_agv_utilization_by_policy.png",
    ),
]


def generate_policy_comparison_plots(
    aggregate_csv_path: str | Path = "results/tables/policy_comparison_agg.csv",
    output_dir: str | Path = "results/figures",
) -> list[Path]:
    """Generate report-ready policy comparison plots from an aggregate CSV."""

    data = pd.read_csv(aggregate_csv_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    generated_paths: list[Path] = []
    for mean_column, std_column, ylabel, filename in PLOT_SPECS:
        path = output / filename
        _plot_grouped_bar(
            data=data,
            mean_column=mean_column,
            std_column=std_column,
            ylabel=ylabel,
            title=ylabel + " by policy",
            output_path=path,
        )
        generated_paths.append(path)

    process_path = output / "process_utilization_by_policy.png"
    _plot_process_utilization(data=data, output_path=process_path)
    generated_paths.append(process_path)

    return generated_paths


def _plot_grouped_bar(
    data: pd.DataFrame,
    mean_column: str,
    std_column: str,
    ylabel: str,
    title: str,
    output_path: Path,
) -> None:
    """Create a grouped bar chart with scenarios on the x-axis and policy bars."""

    import matplotlib.pyplot as plt

    _require_columns(data, ["scenario", "policy", mean_column])
    scenarios = list(data["scenario"].drop_duplicates())
    policies = list(data["policy"].drop_duplicates())
    bar_width = 0.8 / max(1, len(policies))
    x_positions = list(range(len(scenarios)))

    fig, ax = plt.subplots(figsize=(10, 5))
    for index, policy in enumerate(policies):
        values = []
        errors = []
        for scenario in scenarios:
            row = data[(data["scenario"] == scenario) & (data["policy"] == policy)]
            values.append(float(row[mean_column].iloc[0]) if not row.empty else 0.0)
            if std_column in data.columns and not row.empty:
                errors.append(float(row[std_column].iloc[0]))
            else:
                errors.append(0.0)

        offset = (index - (len(policies) - 1) / 2) * bar_width
        bar_positions = [position + offset for position in x_positions]
        ax.bar(
            bar_positions,
            values,
            width=bar_width,
            label=policy,
            yerr=errors if any(errors) else None,
            capsize=3 if any(errors) else 0,
        )

    ax.set_title(title)
    ax.set_xlabel("Scenario")
    ax.set_ylabel(ylabel)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(scenarios, rotation=20, ha="right")
    ax.legend(title="Policy")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _plot_process_utilization(data: pd.DataFrame, output_path: Path) -> None:
    """Create a three-panel process utilization comparison plot."""

    import matplotlib.pyplot as plt

    processes = [
        ("ProcessA", "util_A_mean", "util_A_std"),
        ("ProcessB", "util_B_mean", "util_B_std"),
        ("ProcessC", "util_C_mean", "util_C_std"),
    ]
    _require_columns(data, ["scenario", "policy"] + [column for _, column, _ in processes])

    scenarios = list(data["scenario"].drop_duplicates())
    policies = list(data["policy"].drop_duplicates())
    bar_width = 0.8 / max(1, len(policies))
    x_positions = list(range(len(scenarios)))

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, (process_name, mean_column, std_column) in zip(axes, processes):
        for index, policy in enumerate(policies):
            values = []
            errors = []
            for scenario in scenarios:
                row = data[(data["scenario"] == scenario) & (data["policy"] == policy)]
                values.append(float(row[mean_column].iloc[0]) if not row.empty else 0.0)
                if std_column in data.columns and not row.empty:
                    errors.append(float(row[std_column].iloc[0]))
                else:
                    errors.append(0.0)

            offset = (index - (len(policies) - 1) / 2) * bar_width
            bar_positions = [position + offset for position in x_positions]
            ax.bar(
                bar_positions,
                values,
                width=bar_width,
                label=policy,
                yerr=errors if any(errors) else None,
                capsize=3 if any(errors) else 0,
            )

        ax.set_title(process_name)
        ax.set_xlabel("Scenario")
        ax.set_xticks(x_positions)
        ax.set_xticklabels(scenarios, rotation=20, ha="right")
        ax.grid(axis="y", alpha=0.25)

    axes[0].set_ylabel("Utilization")
    axes[-1].legend(title="Policy")
    fig.suptitle("Process utilization by policy")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _require_columns(data: pd.DataFrame, columns: list[str]) -> None:
    """Raise a clear error if required columns are missing."""

    missing = [column for column in columns if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
