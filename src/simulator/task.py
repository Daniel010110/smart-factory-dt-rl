"""Transport task data model."""

from dataclasses import dataclass

from simulator.job import Job


@dataclass
class TransportTask:
    """A request for an AGV to move one job between two locations."""

    task_id: int
    job: Job
    source: str
    destination: str
    created_at: int
    assigned_at: int | None = None
    completed_at: int | None = None

    @property
    def is_completed(self) -> bool:
        """Return whether this transport task has finished."""

        return self.completed_at is not None
