"""Job data model."""

from dataclasses import dataclass, field


@dataclass
class Job:
    """A production job moving through the factory flow."""

    job_id: int
    created_at: int
    route: list[str]
    current_stage_index: int = 0
    completed_at: int | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def current_location(self) -> str:
        """Return the job's current route location."""

        return self.route[self.current_stage_index]

    @property
    def next_location(self) -> str | None:
        """Return the next route location, if one exists."""

        next_index = self.current_stage_index + 1
        if next_index >= len(self.route):
            return None
        return self.route[next_index]

    def advance(self) -> None:
        """Advance the job to the next route location."""

        if self.next_location is not None:
            self.current_stage_index += 1
