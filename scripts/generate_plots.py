"""Generate report-ready policy comparison plots."""

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from visualization.plot_policy_comparison import generate_policy_comparison_plots


def parse_args() -> argparse.Namespace:
    """Parse plotting arguments."""

    parser = argparse.ArgumentParser(description="Generate policy comparison plots.")
    parser.add_argument(
        "--input",
        default="results/tables/policy_comparison_agg.csv",
        help="Path to aggregate policy comparison CSV.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/figures",
        help="Directory for generated PNG figures.",
    )
    return parser.parse_args()


def main() -> None:
    """Generate all policy comparison figures."""

    args = parse_args()
    input_path = PROJECT_ROOT / args.input
    output_dir = PROJECT_ROOT / args.output_dir
    generated_paths = generate_policy_comparison_plots(input_path, output_dir)

    print("Generated figures:")
    for path in generated_paths:
        print(path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
