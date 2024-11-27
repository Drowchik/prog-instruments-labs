from abc import ABC, abstractmethod

from enity import Enity, Grass
from mapping import Map
from point import Point


class Creature(Enity, ABC):
    def __init__(self, point: Point, sprite: str, speed: int, health: int) -> None:
        super().__init__(point, sprite)
        self.speed = speed
        self.health = health

    def make_move(self, new_x, new_y):
        self.point = Point(new_x. new_y)

    @abstractmethod
    def attack(self, map_matrix: Map):
        pass


class Herbivore(Creature):
    def __init__(self, point: Point, speed: int = 1, health: int = 5, sprite: str = "🐇") -> None:
        super().__init__(point, sprite, speed, health)

    def attack(self, map_matrix: Map):
        coord = self.coordinate.get_neighboors()
        for i in coord:
            if isinstance(map_matrix.get_object(i), Grass):
                map_matrix.delete_object(i)


class Predator(Creature):
    def __init__(self, point: Point, speed: int = 2, health: int = 8, atack: int = 5, sprite: str = '🐺') -> None:
        super().__init__(point, sprite, speed, health)
        self.atack = atack

    def attack(self, map_matrix: Map):
        coord = self.coordinate.get_neighboors()
        for i in coord:
            if isinstance(map_matrix.get_object(i), Herbivore):
                enit = map_matrix.get_object(i)
                enit.health -= self.atack
                if enit.health <= 0:
                    map_matrix.delete_object(i)
                break
