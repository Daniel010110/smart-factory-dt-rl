"""Factory layout and distance calculations."""

from math import ceil


class Layout:
    """Simple 2D layout using Manhattan distance."""

    def __init__(
        self,
        locations: dict[str, tuple[int, int]],
        travel_time_per_unit: float = 1.0,
    ) -> None:
        self.locations = locations
        self.travel_time_per_unit = travel_time_per_unit

    def manhattan_distance(self, source: str, destination: str) -> int:
        """Calculate Manhattan distance between named locations."""

        source_xy = self.locations[source]
        destination_xy = self.locations[destination]
        return abs(source_xy[0] - destination_xy[0]) + abs(source_xy[1] - destination_xy[1])

    def travel_time(self, source: str, destination: str) -> int:
        """Calculate discrete travel time between named locations."""

        distance = self.manhattan_distance(source, destination)
        return max(1, ceil(distance * self.travel_time_per_unit))
