"""Process station model."""

from collections import deque
from typing import Deque

from simulator.job import Job


class ProcessStation:
    """A fixed-time processing station with a FIFO queue."""

    def __init__(self, name: str, processing_time: int) -> None:
        self.name = name
        self.processing_time = processing_time
        self.queue: Deque[Job] = deque()
        self.current_job: Job | None = None
        self.remaining_time = 0
        self.busy_time = 0
        self.idle_time = 0

    def enqueue(self, job: Job) -> None:
        """Add a job to the station queue."""

        self.queue.append(job)

    def step(self) -> Job | None:
        """Advance station state by one step and return a completed job if any."""

        completed_job: Job | None = None

        if self.current_job is None and self.queue:
            self.current_job = self.queue.popleft()
            self.remaining_time = self.processing_time

        if self.current_job is not None:
            self.busy_time += 1
            self.remaining_time -= 1
            if self.remaining_time <= 0:
                completed_job = self.current_job
                self.current_job = None
        else:
            self.idle_time += 1

        return completed_job

    @property
    def utilization(self) -> float:
        """Return cumulative station utilization."""

        total_time = self.busy_time + self.idle_time
        if total_time == 0:
            return 0.0
        return self.busy_time / total_time
