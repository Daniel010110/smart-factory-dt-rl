"""Factory environment orchestration."""

from logging_utils.simulation_logger import SimulationLogger
from policies.base_policy import BasePolicy
from simulator.agv import AGV
from simulator.job import Job
from simulator.layout import Layout
from simulator.process_station import ProcessStation
from simulator.task import TransportTask


class FactoryEnv:
    """Minimal smart factory environment for baseline AGV policy experiments."""

    ROUTE = ["Input", "ProcessA", "ProcessB", "ProcessC", "Output"]

    def __init__(self, config: dict[str, object], policy: BasePolicy) -> None:
        self.config = config
        self.policy = policy
        self.logger = SimulationLogger()
        self.time = 0
        self.next_job_id = 1
        self.next_task_id = 1
        self.jobs: list[Job] = []
        self.completed_jobs: list[Job] = []
        self.pending_tasks: list[TransportTask] = []
        self.layout = self._build_layout()
        self.stations = self._build_stations()
        self.agvs = self._build_agvs()

    def reset(self) -> dict[str, object]:
        """Reset the environment and return the initial state."""

        self.time = 0
        self.next_job_id = 1
        self.next_task_id = 1
        self.jobs = []
        self.completed_jobs = []
        self.pending_tasks = []
        self.logger = SimulationLogger()
        self.layout = self._build_layout()
        self.stations = self._build_stations()
        self.agvs = self._build_agvs()
        return self.get_state()

    def step(self) -> dict[str, object]:
        """Advance the simulation by one step."""

        self._generate_jobs()
        self._dispatch_idle_agvs()

        completed_tasks = [task for agv in self.agvs if (task := agv.step(self.time)) is not None]
        for task in completed_tasks:
            self._handle_completed_task(task)

        completed_station_jobs = [
            job for station in self.stations.values() if (job := station.step()) is not None
        ]
        for job in completed_station_jobs:
            self._create_next_transport_task(job)

        self.logger.log_step(self.time, self.get_state())
        self.time += 1
        return self.get_state()

    def run(self, max_steps: int | None = None) -> dict[str, object]:
        """Run the simulation and return collected metrics."""

        if max_steps is None:
            max_steps = int(self.config.get("simulation", {}).get("max_steps", 100))  # type: ignore[union-attr]

        self.reset()
        for _ in range(max_steps):
            self.step()
        return self.collect_metrics()

    def get_state(self) -> dict[str, object]:
        """Return a compact snapshot of environment state."""

        return {
            "time": self.time,
            "pending_tasks": len(self.pending_tasks),
            "completed_jobs": len(self.completed_jobs),
            "agvs": [
                {
                    "agv_id": agv.agv_id,
                    "location": agv.current_location,
                    "status": agv.status,
                    "remaining_travel_time": agv.remaining_travel_time,
                }
                for agv in self.agvs
            ],
            "stations": {
                name: {
                    "queue_length": len(station.queue),
                    "current_job_id": station.current_job.job_id if station.current_job else None,
                    "remaining_time": station.remaining_time,
                    "utilization": station.utilization,
                }
                for name, station in self.stations.items()
            },
        }

    def collect_metrics(self) -> dict[str, object]:
        """Collect basic simulation metrics."""

        return {
            "completed_jobs": len(self.completed_jobs),
            "pending_tasks": len(self.pending_tasks),
            "station_utilization": {
                name: station.utilization for name, station in self.stations.items()
            },
            "agv_total_distance": {
                agv.agv_id: agv.total_distance for agv in self.agvs
            },
        }

    def _build_layout(self) -> Layout:
        layout_config = self.config.get("layout", {})  # type: ignore[assignment]
        locations = {
            name: tuple(value)
            for name, value in layout_config.get("locations", {}).items()
        }
        travel_time_per_unit = float(self.config.get("factory", {}).get("travel_time_per_unit", 1))  # type: ignore[union-attr]
        return Layout(locations=locations, travel_time_per_unit=travel_time_per_unit)

    def _build_stations(self) -> dict[str, ProcessStation]:
        factory_config = self.config.get("factory", {})  # type: ignore[assignment]
        processing_times = factory_config.get("processing_times", {})
        return {
            name: ProcessStation(name=name, processing_time=int(processing_time))
            for name, processing_time in processing_times.items()
        }

    def _build_agvs(self) -> list[AGV]:
        factory_config = self.config.get("factory", {})  # type: ignore[assignment]
        agv_count = int(factory_config.get("agv_count", 1))
        return [AGV(agv_id=i + 1, initial_location="Input") for i in range(agv_count)]

    def _generate_jobs(self) -> None:
        simulation_config = self.config.get("simulation", {})  # type: ignore[assignment]
        job_interval = int(simulation_config.get("job_interval", 5))
        max_jobs = int(simulation_config.get("max_jobs", 10))

        if self.time % job_interval != 0 or len(self.jobs) >= max_jobs:
            return

        job = Job(job_id=self.next_job_id, created_at=self.time, route=self.ROUTE.copy())
        self.next_job_id += 1
        self.jobs.append(job)
        self._create_next_transport_task(job)

    def _dispatch_idle_agvs(self) -> None:
        for agv in self.agvs:
            if agv.current_task is not None or not self.pending_tasks:
                continue

            task = self.policy.select_task(agv, self.pending_tasks, self.layout)
            if task is None:
                continue

            self.pending_tasks.remove(task)
            agv.assign_task(task, self.layout, self.time)

    def _handle_completed_task(self, task: TransportTask) -> None:
        task.job.advance()
        if task.destination == "Output":
            task.job.completed_at = self.time
            self.completed_jobs.append(task.job)
            return

        station = self.stations.get(task.destination)
        if station is not None:
            station.enqueue(task.job)

    def _create_next_transport_task(self, job: Job) -> None:
        destination = job.next_location
        if destination is None:
            return

        task = TransportTask(
            task_id=self.next_task_id,
            job=job,
            source=job.current_location,
            destination=destination,
            created_at=self.time,
        )
        self.next_task_id += 1
        self.pending_tasks.append(task)

        # TODO: Add blocking/starvation semantics once station buffers are modeled.
        # TODO: Add event callbacks for future Gymnasium observation/reward design.
