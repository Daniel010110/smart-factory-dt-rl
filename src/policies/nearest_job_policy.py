"""Nearest-job AGV dispatch policy."""

from typing import TYPE_CHECKING

from policies.base_policy import BasePolicy

if TYPE_CHECKING:
    from simulator.agv import AGV
    from simulator.layout import Layout
    from simulator.task import TransportTask


class NearestJobPolicy(BasePolicy):
    """Select the pending task with the nearest pickup location."""

    def select_task(
        self,
        agv: "AGV",
        pending_tasks: list["TransportTask"],
        layout: "Layout",
    ) -> "TransportTask | None":
        """Return the task whose source is closest to the AGV."""

        if not pending_tasks:
            return None
        return min(
            pending_tasks,
            key=lambda task: layout.manhattan_distance(agv.current_location, task.source),
        )
