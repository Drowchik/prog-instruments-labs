from math import floor
from random import randint
from creature import Herbivore, Predator
from enity import Grass, Rock, Tree
from hellper import Reader
from mapping import Map
from point import Point


class Action:
    def __init__(self, map_coord: Map, proportion_file: str) -> None:
        self.map_matrix = map_coord
        self.proportion = Reader.read_json(proportion_file)
        self.object_map = {
            "Grass": Grass,
            "Rock": Rock,
            "Tree": Tree,
            "Herbivore": Herbivore,
            "Predator": Predator
        }

    def procnet_enity(self) -> list:
        list_count = [0]*3
        for enit in self.map_matrix.map_coord.values():
            if isinstance(enit, Predator):
                list_count[0] += 1
            elif isinstance(enit, Herbivore):
                list_count[1] += 1
            elif isinstance(enit, Grass):
                list_count[2] += 1
        return list_count

    def calculate_more_enity(self):
        list_count = self.procnet_enity()
        list_enity = ["Predator", "Herbivore", "Grass"]
        for i in range(len(list_enity)):
            self.add_objects(self.calculate_count(
                self.proportion[list_enity[i]])-list_count[i], self.object_map[list_enity[i]])

    def calculate_count(self, proportion):
        return floor(self.map_matrix.get_area()*proportion)

    def add_objects(self, count, object_class):
        while (count):
            point = Point(randint(0, self.map_matrix.weight - 1),
                          randint(0, self.map_matrix.height - 1))
            if not self.map_matrix.get_object(point):
                obj = object_class(point)
                self.map_matrix.add_object(obj)
                count -= 1

    def init_actions(self):
        for obj_name, proportion in self.proportion.items():
            self.add_objects(self.calculate_count(proportion),
                             self.object_map[obj_name])

    def search_short_path(self, sprite, obj):
        all_short_path = []
        for cord, enit in self.map_matrix.map_coord.items():
            if isinstance(enit, obj):
                grass = self.map_matrix.get_all_object(sprite)
                short_path = []
                for i in grass:
                    short_path.append(self.map_matrix.search_path(cord, i))
                non_empty_lists = [lst for lst in short_path if lst]
                if non_empty_lists:
                    all_short_path.append(min(non_empty_lists, key=len))
        return all_short_path

    def action_enity(self, lists):
        for shortest_list in lists:
            cord = shortest_list[0]
            enit = self.map_matrix.get_object(cord)
            if (len(shortest_list)-1) < enit.speed:
                self.map_matrix.delete_object(cord)
                enit.coordinate = shortest_list[-1]
                self.map_matrix.add_object(enit)
                enit.attack(self.map_matrix)
            else:
                self.map_matrix.delete_object(cord)
                enit.coordinate = shortest_list[enit.speed]
                self.map_matrix.add_object(enit)

    def turn_actions(self):
        self.action_enity(self.search_short_path("🐇", Predator))
        self.action_enity(self.search_short_path("🌱", Herbivore))
