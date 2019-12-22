import math


def distance(point_1=(0, 0), point_2=(0, 0)):
    """Returns the distance between two points"""
    return math.sqrt((point_1[0] - point_2[0]) ** 2 + (point_1[1] - point_2[1]) ** 2)


def abs_extract(a, b):
    assert b >= 0
    sign = a >= 0 or -1
    res = max(abs(a) - b, 0)
    return res * sign


def min_abs_value(value, limit):
    assert limit >= limit
    sign = value >= 0 or -1
    value = min(abs(value), limit)
    return value * sign


def get_color_for_position(x, y, img_data):
    data = img_data.get_region(int(x), int(y), 1, 1)
    color = data.get_data("RGB", data.width * 3)
    color = tuple(e for e in color)
    return color
