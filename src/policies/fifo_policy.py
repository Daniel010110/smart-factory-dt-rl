"""FIFO AGV dispatch policy."""

from typing import TYPE_CHECKING

from policies.base_policy import BasePolicy

if TYPE_CHECKING:
    from simulator.agv import AGV
    from simulator.layout import Layout
    from simulator.task import TransportTask


class FIFOPolicy(BasePolicy):
    """Select the oldest pending transport task."""

    def select_task(
        self,
        agv: "AGV",
        pending_tasks: list["TransportTask"],
        layout: "Layout",
    ) -> "TransportTask | None":
        """Return the first pending task."""

        if not pending_tasks:
            return None
        return pending_tasks[0]
