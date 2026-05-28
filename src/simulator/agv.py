"""Automated guided vehicle model."""

from simulator.layout import Layout
from simulator.task import TransportTask


class AGV:
    """Minimal AGV state machine for transport tasks."""

    def __init__(self, agv_id: int, initial_location: str = "Input") -> None:
        self.agv_id = agv_id
        self.current_location = initial_location
        self.status = "idle"
        self.current_task: TransportTask | None = None
        self.remaining_travel_time = 0
        self.total_distance = 0
        self.busy_time = 0
        self.idle_time = 0

    def assign_task(self, task: TransportTask, layout: Layout, current_time: int) -> None:
        """Assign a transport task to the AGV."""

        task.assigned_at = current_time
        self.current_task = task
        self.status = "moving"

        to_pickup = layout.travel_time(self.current_location, task.source)
        to_dropoff = layout.travel_time(task.source, task.destination)
        self.remaining_travel_time = to_pickup + to_dropoff
        self.total_distance += layout.manhattan_distance(self.current_location, task.source)
        self.total_distance += layout.manhattan_distance(task.source, task.destination)

    def step(self, current_time: int) -> TransportTask | None:
        """Advance AGV state by one step and return a completed task if any."""

        if self.current_task is None:
            self.status = "idle"
            self.idle_time += 1
            return None

        self.busy_time += 1
        self.remaining_travel_time -= 1

        if self.remaining_travel_time <= 0:
            completed_task = self.current_task
            completed_task.completed_at = current_time
            self.current_location = completed_task.destination
            self.current_task = None
            self.status = "idle"
            return completed_task

        return None
