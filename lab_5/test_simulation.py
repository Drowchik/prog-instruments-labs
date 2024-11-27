import pytest
from src.enity import Grass
from src.mapping import Map
from src.point import Point


@pytest.mark.parametrize(
    "point,result",
    [
        (Point(0, 0), [Point(0, 1), Point(0, -1), Point(1, 0), Point(-1, 0)]),
        (Point(1, 1), [Point(1, 2),
                       Point(1, 0), Point(2, 1), Point(0, 1)]),
        (Point(-1, -1), [Point(-1, 0),
         Point(-1, -2), Point(0, -1), Point(-2, -1)])
    ]
)
def test_point_get_neighboors(point: Point, result: list[Point]):
    assert sorted(point.get_neighboors(), key=lambda p: (
        p.x, p.y)) == sorted(result, key=lambda p: (p.x, p.y))


@pytest.mark.parametrize(
    "point,result",
    [
        (Point(0, 0), [Point(0, 1), Point(0, -1), Point(1, 0), Point(-1, 0)]),
        (Point(1, 1), [Point(1, 2), Point(1, 0), Point(2, 1), Point(0, 1)]),
        (Point(-1, -1), [Point(-1, 0),
         Point(-1, -2), Point(0, -1), Point(-2, -1)])
    ]
)
def test_point_eq(point: Point, result: list[Point]):
    assert sorted(point.get_neighboors(), key=lambda p: (
        p.x, p.y)) == sorted(result, key=lambda p: (p.x, p.y))


@pytest.mark.parametrize(
    "point1, point2, expected",
    [
        (Point(0, 0), Point(0, 0), True),
        (Point(1, 1), Point(1, 2), False),
        (Point(-1, -1), Point(-1, -1), True),
        (Point(1, 0), Point(0, 1), False),
        (Point(0, 0), Point(0, -1), False),
    ]
)
def test_point_eq(point1: Point, point2: Point, expected: bool):
    assert (point1 == point2) == expected


def test_get_size():
    assert Map(height=10, weight=15).get_size() == (10, 15)
    assert Map(height=21, weight=53).get_size() == (21, 53)


def test_get_area():
    assert Map(height=5, weight=8).get_area() == 40
    assert Map(height=10, weight=12).get_area() == 120


@pytest.mark.parametrize(
    "point",
    [
        (Point(0, 0)),
        (Point(5, 5))
    ]
)
def test_add_and_get_object(point):
    m = Map(height=10, weight=10)
    entity = Grass(point)
    coord = m.add_object(Grass(point))
    assert m.get_object(point).coordinate == entity.coordinate
    assert m.get_object(point).sprite == entity.sprite
    assert type(m.get_object(point)) == type(entity)


def test_search_path_no_obstacles():
    m = Map(height=5, weight=5)
    start = Point(0, 0)
    target = Point(3, 3)
    path = m.search_path(start, target)
    assert path == [
        Point(0, 0),
        Point(0, 1),
        Point(0, 2),
        Point(0, 3),
        Point(1, 3),
        Point(2, 3)
    ]
    start = Point(0, 0)
    target = Point(1, 1)
    path = m.search_path(start, target)
    assert path == [Point(0, 0), Point(0, 1)]
