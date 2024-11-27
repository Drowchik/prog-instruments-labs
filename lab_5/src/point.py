class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __eq__(self, other) -> bool:
        return self.x == other.x and self.y == other.y

    def __str__(self) -> str:
        return f"X: {self.x} Y: {self.y}"

    def __repr__(self) -> str:
        return f"Point(X:{self.x}, Y:{self.y})"

    def get_neighboors(self) -> list:
        # возможна проверка не вышел ли я за границу
        return [Point(self.x, self.y+1), Point(self.x, self.y-1),
                Point(self.x+1, self.y), Point(self.x-1, self.y)]

    @property
    def point(self) -> tuple:
        return self.x, self.y

    @point.setter
    def point(self, x: int, y: int) -> None:
        self.x, self.y = x, y
