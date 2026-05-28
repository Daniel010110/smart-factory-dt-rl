"""Factory environment orchestration."""

import random

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

    def __init__(
        self,
        config: dict[str, object],
        policy: BasePolicy,
        scenario_name: str = "",
        policy_name: str = "",
        seed: int | None = None,
    ) -> None:
        self.config = config
        self.policy = policy
        self.scenario_name = scenario_name
        self.policy_name = policy_name
        self.seed = seed
        self.logger = SimulationLogger(scenario_name, policy_name, seed)
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
        self.logger = SimulationLogger(self.scenario_name, self.policy_name, self.seed)
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
            "throughput": self._throughput(),
            "total_agv_distance": self._total_agv_distance(),
            "bottleneck_station": self._bottleneck_station()[0],
            "bottleneck_queue_length": self._bottleneck_station()[1],
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
            "throughput": self._throughput(),
            "station_utilization": {
                name: station.utilization for name, station in self.stations.items()
            },
            "agv_total_distance": self._total_agv_distance(),
            "agv_distance_by_id": {agv.agv_id: agv.total_distance for agv in self.agvs},
        }

    def _build_layout(self) -> Layout:
        layout_config = self.config.get("layout", {})  # type: ignore[assignment]
        locations = {
            name: tuple(value)
            for name, value in layout_config.get("locations", {}).items()
        }
        agv_config = self.config.get("agv", {})  # type: ignore[assignment]
        factory_config = self.config.get("factory", {})  # type: ignore[assignment]
        speed = float(agv_config.get("speed", 0) or 0)
        travel_time_per_unit = 1.0 / speed if speed > 0 else float(factory_config.get("travel_time_per_unit", 1))
        return Layout(locations=locations, travel_time_per_unit=travel_time_per_unit)

    def _build_stations(self) -> dict[str, ProcessStation]:
        factory_config = self.config.get("factory", {})  # type: ignore[assignment]
        process_config = self.config.get("processes", {})  # type: ignore[assignment]
        if process_config:
            processing_times = {
                name: values.get("processing_time", 1)
                for name, values in process_config.items()
                if isinstance(values, dict)
            }
        else:
            processing_times = factory_config.get("processing_times", {})
        return {
            name: ProcessStation(name=name, processing_time=int(processing_time))
            for name, processing_time in processing_times.items()
        }

    def _build_agvs(self) -> list[AGV]:
        factory_config = self.config.get("factory", {})  # type: ignore[assignment]
        agv_config = self.config.get("agv", {})  # type: ignore[assignment]
        agv_count = int(agv_config.get("num_agvs", factory_config.get("agv_count", 1)))
        start_location = str(agv_config.get("start_location", "Input"))
        return [AGV(agv_id=i + 1, initial_location=start_location) for i in range(agv_count)]

    def _generate_jobs(self) -> None:
        simulation_config = self.config.get("simulation", {})  # type: ignore[assignment]
        job_generation_config = self.config.get("job_generation", {})  # type: ignore[assignment]
        arrival_interval = max(
            1,
            int(job_generation_config.get("arrival_interval", simulation_config.get("job_interval", 5))),
        )
        arrival_probability = job_generation_config.get(
            "arrival_probability",
            simulation_config.get("job_arrival_probability"),
        )
        arrival_mode = job_generation_config.get(
            "mode",
            "probability" if arrival_probability is not None else "interval",
        )
        max_jobs = int(simulation_config.get("max_jobs", 10))

        if len(self.jobs) >= max_jobs:
            return

        should_create = False
        if arrival_mode == "probability" and arrival_probability is not None:
            should_create = random.random() <= float(arrival_probability)
        else:
            should_create = self.time % arrival_interval == 0

        if not should_create:
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

    def _total_agv_distance(self) -> int:
        """Return total distance traveled by all AGVs."""

        return sum(agv.total_distance for agv in self.agvs)

    def _throughput(self) -> float:
        """Return completed jobs per elapsed step."""

        elapsed_steps = max(1, self.time + 1)
        return len(self.completed_jobs) / elapsed_steps

    def _bottleneck_station(self) -> tuple[str | None, int]:
        """Return the station with the longest current queue."""

        if not self.stations:
            return None, 0
        station = max(self.stations.values(), key=lambda item: len(item.queue))
        return station.name, len(station.queue)
