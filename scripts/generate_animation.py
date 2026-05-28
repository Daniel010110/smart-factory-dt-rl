"""Generate a lightweight 2D factory animation from a step log."""

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from visualization.animate_factory import animate_factory_log, default_animation_output_path


def parse_args() -> argparse.Namespace:
    """Parse animation generation arguments."""

    parser = argparse.ArgumentParser(description="Generate a 2D factory GIF from a step log CSV.")
    parser.add_argument("--log", required=True, help="Path to step log CSV.")
    parser.add_argument("--output", default=None, help="Output GIF path.")
    parser.add_argument("--fps", type=int, default=5, help="Frames per second.")
    parser.add_argument("--step-interval", type=int, default=2, help="Use every Nth log row.")
    return parser.parse_args()


def main() -> None:
    """Generate the animation GIF."""

    args = parse_args()
    log_path = PROJECT_ROOT / args.log
    output_path = PROJECT_ROOT / args.output if args.output else PROJECT_ROOT / default_animation_output_path(log_path)

    generated_path = animate_factory_log(
        log_csv_path=log_path,
        output_path=output_path,
        fps=args.fps,
        step_interval=args.step_interval,
    )
    print(f"Generated animation: {generated_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
