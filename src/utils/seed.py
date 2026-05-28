"""Reproducibility helpers."""

import random


def set_random_seed(seed: int) -> None:
    """Set random seeds for currently used standard libraries."""

    random.seed(seed)
    # TODO: Seed numpy/torch here only after those dependencies are introduced.
