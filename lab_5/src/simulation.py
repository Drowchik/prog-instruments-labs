import asyncio
import time
from action import Action
from const import PATH
from mapping import Map
from point import Point


class Render:
    def __init__(self, map_coord: Map) -> None:
        self.map_matrix = map_coord

    @staticmethod
    def print_info() -> None:
        dict_info_object = {
            'P': 'predator',
            'H': 'herbivores',
            'G': 'grass',
            'R': 'rock',
            'T': 'tree',
        }
        for key, value in dict_info_object.items():
            print(f'{key} - {value}')
        print("Нажмите Enter для переключения паузы:")

    def draw_map(self) -> None:
        for i in range(self.map_matrix.height):
            for j in range(self.map_matrix.weight):
                obj = self.map_matrix.get_object(Point(j, i))
                if obj:
                    print("|" + obj.sprite + "|", end="")
                else:
                    print("|  |", end="")
            print()


class Simulation:
    def __init__(self, height: int, weight: int) -> None:
        self.move_count = 0
        self.matrix = Map(height, weight)
        self.render = Render(map_coord=self.matrix)
        self.action = Action(map_coord=self.matrix, proportion_file=PATH)
        self.is_paused = False

    def next_turn(self) -> None:
        self.render.draw_map()
        self.action.turn_actions()
        self.move_count += 1

    def start_simulation(self) -> None:
        self.render.print_info()
        self.action.init_actions()
        while (True):
            if not self.is_paused:
                print(f"Итерация: {self.move_count}")
                self.next_turn()
                if not self.move_count % 3:
                    self.action.calculate_more_enity()
            time.sleep(1.5)

    def listen_for_pause(self):
        while True:
            input()
            self.is_paused = not self.is_paused
            if self.is_paused:
                print("Игра на паузе. Для продолжения тыкните Enter")
            else:
                print("Игра продолжается.")
