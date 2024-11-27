from abc import ABC

from point import Point


class Enity(ABC):
    def __init__(self, point: Point, sprite: str) -> None:
        self.coordinate = point
        self.sprite = sprite

    def get_coord(self) -> tuple:
        return self.coordinate.x, self.coordinate.y


class Grass(Enity):
    def __init__(self, point: Point, sprite: str = "🌱") -> None:
        super().__init__(point, sprite)


class Rock(Enity):
    def __init__(self, point: Point, sprite: str = "⛰️ ") -> None:
        super().__init__(point, sprite)


class Tree(Enity):
    def __init__(self, point: Point, sprite: str = "🌲") -> None:
        super().__init__(point, sprite)
