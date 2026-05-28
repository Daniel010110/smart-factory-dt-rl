"""Policy interface for AGV dispatch."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulator.agv import AGV
    from simulator.layout import Layout
    from simulator.task import TransportTask


class BasePolicy(ABC):
    """Abstract base class for selecting transport tasks."""

    @abstractmethod
    def select_task(
        self,
        agv: "AGV",
        pending_tasks: list["TransportTask"],
        layout: "Layout",
    ) -> "TransportTask | None":
        """Select a task for the given AGV."""
