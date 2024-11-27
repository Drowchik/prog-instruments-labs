from collections import deque
from typing import Dict, List, Tuple

from enity import Enity, Grass
from point import Point


class Map:
    def __init__(self, height: int, weight: int) -> None:
        self.height = height
        self.weight = weight
        self.map_coord = {}

    def get_size(self) -> Tuple[int]:
        return self.height, self.weight

    def get_area(self) -> int:
        return self.height*self.weight

    def add_object(self, obj: Enity) -> Dict:
        point = obj.coordinate
        self.map_coord[point] = obj
        return self.map_coord[point]

    def delete_object(self, point) -> None:
        del self.map_coord[point]

    def get_object(self, point) -> Enity | bool:
        if point in self.map_coord.keys():
            return self.map_coord[point]
        return False

    def get_all_object(self, sprite: str) -> List[Enity]:
        return [point for point, enity in self.map_coord.items() if enity.sprite == sprite]

    def check_have_object(self, point: Point) -> bool:
        return 0 <= point.x < self.weight and 0 <= point.y < self.height

    def search_path(self, start: Point, target: Point) -> List[Point]:
        queue = deque([(start, [start])])
        visited = set([start])
        neighbor_target = target.get_neighboors()
        while queue:
            current, path = queue.popleft()

            if current in neighbor_target:
                return path

            for neighbor in current.get_neighboors():
                if not self.check_have_object(neighbor):
                    continue
                if neighbor in self.map_coord:
                    continue
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []
