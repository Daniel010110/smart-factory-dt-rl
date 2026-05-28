"""Skeleton bottleneck-aware AGV dispatch policy."""

from typing import TYPE_CHECKING

from policies.base_policy import BasePolicy

if TYPE_CHECKING:
    from simulator.agv import AGV
    from simulator.layout import Layout
    from simulator.task import TransportTask


class BottleneckAwarePolicy(BasePolicy):
    """Select tasks using a placeholder bottleneck-aware scoring design.

    Intended design:
    - Compute bottleneck score using process queue length and optionally utilization.
    - Prefer tasks whose pickup location is the current bottleneck station.
    - Penalize tasks whose drop-off location is the current bottleneck station.
    - Combine task age, distance, bottleneck relief score, and bottleneck inflow penalty.
    """

    def __init__(
        self,
        age_weight: float = 1.0,
        distance_weight: float = 1.0,
        relief_weight: float = 2.0,
        inflow_penalty_weight: float = 2.0,
    ) -> None:
        self.age_weight = age_weight
        self.distance_weight = distance_weight
        self.relief_weight = relief_weight
        self.inflow_penalty_weight = inflow_penalty_weight

    def select_task(
        self,
        agv: "AGV",
        pending_tasks: list["TransportTask"],
        layout: "Layout",
    ) -> "TransportTask | None":
        """Select the highest-scoring pending task.

        This skeleton currently infers a simple placeholder bottleneck from pending
        task pickup locations. Full implementation should consume live process
        queue lengths and station utilization from the environment.
        """

        if not pending_tasks:
            return None

        bottleneck_location = self._estimate_bottleneck_location(pending_tasks)
        return max(
            pending_tasks,
            key=lambda task: self._score_task(agv, task, layout, bottleneck_location),
        )

    def _estimate_bottleneck_location(
        self,
        pending_tasks: list["TransportTask"],
    ) -> str | None:
        """Estimate a bottleneck location from currently visible tasks."""

        counts: dict[str, int] = {}
        for task in pending_tasks:
            counts[task.source] = counts.get(task.source, 0) + 1

        if not counts:
            return None

        # TODO: Replace this placeholder with station queue length and utilization.
        return max(counts, key=counts.get)

    def _score_task(
        self,
        agv: "AGV",
        task: "TransportTask",
        layout: "Layout",
        bottleneck_location: str | None,
    ) -> float:
        """Return a placeholder task score for future bottleneck-aware dispatch."""

        distance = layout.manhattan_distance(agv.current_location, task.source)
        relief_score = 1.0 if task.source == bottleneck_location else 0.0
        inflow_penalty = 1.0 if task.destination == bottleneck_location else 0.0

        # TODO: Use current simulation time to compute task age.
        task_age = 0.0

        return (
            self.age_weight * task_age
            - self.distance_weight * distance
            + self.relief_weight * relief_score
            - self.inflow_penalty_weight * inflow_penalty
        )
