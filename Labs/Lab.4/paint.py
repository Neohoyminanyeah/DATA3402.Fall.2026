

import json
import math


class Canvas:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.data = [[' '] * width for i in range(height)]

    def set_pixel(self, row, col, char='*'):
        self.data[row][col] = char

    def get_pixel(self, row, col):
        return self.data[row][col]

    def clear_canvas(self):
        self.data = [[' '] * self.width for i in range(self.height)]

    def v_line(self, x, y, h, **kargs):
        for i in range(x,x+h):
            self.set_pixel(i,y, **kargs)

    def h_line(self, x, y, w, **kargs):
        for i in range(y,y+w):
            self.set_pixel(x,i, **kargs)

    def line(self, x1, y1, x2, y2, **kargs):
        slope = (x2-x1) / (y2-y1)
        for y in range(y1,y2):
            x= x1 + int(slope * (y-y1))
            self.set_pixel(x,y, **kargs)

    def display(self):
        print("\n".join(["".join(row) for row in self.data]))


class Counter:
    def __init__(self, max_value):
        self.__max_value = max_value
        self.__count = 0

    def increment(self):
        if self.__count < self.__max_value:
            self.__count += 1
        else:
            print("Error: counter cannot exceed the maximum value.")

    def reset(self):
        self.__count = 0

    def get_count(self):
        return self.__count

    def get_max_value(self):
        return self.__max_value

    def is_at_max(self):
        return self.__count == self.__max_value


def _draw_line(canvas, start, end, char):
    """Draw an edge in either direction, including both endpoints."""
    x1, y1 = start
    x2, y2 = end
    steps = max(1, math.ceil(max(abs(x2 - x1), abs(y2 - y1))))

    for i in range(steps + 1):
        fraction = i / steps
        x = round(x1 + fraction * (x2 - x1))
        y = round(y1 + fraction * (y2 - y1))
        row = canvas.height - 1 - y
        col = x

        if 0 <= row < canvas.height and 0 <= col < canvas.width:
            canvas.set_pixel(row, col, char=char)


def _paint_outline(canvas, points, char):
    """Connect consecutive points and close the outline."""
    for i in range(len(points)):
        _draw_line(canvas, points[i], points[(i + 1) % len(points)], char)


class Shape:
    def __init__(self, char="*"):
        self.__char = char

    def get_char(self):
        return self.__char

    def area(self):
        raise NotImplementedError("Subclasses must implement area().")

    def perimeter(self):
        raise NotImplementedError("Subclasses must implement perimeter().")

    def get_x(self):
        raise NotImplementedError("Subclasses must implement get_x().")

    def get_y(self):
        raise NotImplementedError("Subclasses must implement get_y().")

    def perimeter_points(self):
        raise NotImplementedError("Subclasses must implement perimeter_points().")

    def contains_point(self, x, y):
        raise NotImplementedError("Subclasses must implement contains_point().")

    def paint(self, canvas):
        raise NotImplementedError("Subclasses must implement paint().")

    def to_dict(self):
        raise NotImplementedError("Subclasses must implement to_dict().")

    def overlaps(self, other):
        if isinstance(other, CompoundShape):
            return other.overlaps(self)

        if isinstance(self, Circle) and isinstance(other, Circle):
            distance = math.hypot(
                self.get_x() - other.get_x(),
                self.get_y() - other.get_y()
            )
            return distance <= self.get_radius() + other.get_radius()

        points1 = [] if isinstance(self, Circle) else self.perimeter_points()
        points2 = [] if isinstance(other, Circle) else other.perimeter_points()
        axes = []

        for points in [points1, points2]:
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                axis = (-(y2 - y1), x2 - x1)
                if axis != (0, 0):
                    axes.append(axis)

        if isinstance(self, Circle) or isinstance(other, Circle):
            if isinstance(self, Circle):
                circle, corners = self, points2
            else:
                circle, corners = other, points1
            cx, cy = circle.get_x(), circle.get_y()
            nearest = min(
                corners,
                key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2
            )
            axis = (nearest[0] - cx, nearest[1] - cy)
            if axis != (0, 0):
                axes.append(axis)

        def project(shape, points, axis):
            ax, ay = axis
            if isinstance(shape, Circle):
                center = shape.get_x() * ax + shape.get_y() * ay
                radius = shape.get_radius() * math.hypot(ax, ay)
                return center - radius, center + radius
            values = [x * ax + y * ay for x, y in points]
            return min(values), max(values)

        for axis in axes:
            low1, high1 = project(self, points1, axis)
            low2, high2 = project(other, points2, axis)
            if high1 < low2 or high2 < low1:
                return False
        return True


class Rectangle(Shape):
    def __init__(self, length, width, x, y, char="*"):
        super().__init__(char)
        self.__length = length
        self.__width = width
        self.__x = x
        self.__y = y

    def area(self):
        return self.__length * self.__width

    def perimeter(self):
        return 2 * (self.__length + self.__width)

    def get_length(self):
        return self.__length

    def get_width(self):
        return self.__width

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def perimeter_points(self):
        x, y = self.__x, self.__y
        length, width = self.__length, self.__width
        return [(x, y), (x + length, y),
                (x + length, y + width), (x, y + width)]

    def contains_point(self, x, y):
        return (self.__x <= x <= self.__x + self.__length
                and self.__y <= y <= self.__y + self.__width)

    def paint(self, canvas):
        _paint_outline(canvas, self.perimeter_points(), self.get_char())


    def to_dict(self):
        return {
            "type": "Rectangle",
            "parameters": {
                "length": self.__length, "width": self.__width,
                "x": self.__x, "y": self.__y, "char": self.get_char()
            }
        }


class Circle(Shape):
    def __init__(self, radius, x, y, char="*"):
        super().__init__(char)
        self.__radius = radius
        self.__x = x
        self.__y = y

    def area(self):
        return math.pi * self.__radius ** 2

    def perimeter(self):
        return 2 * math.pi * self.__radius

    def get_radius(self):
        return self.__radius

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def perimeter_points(self):
        points = []
        for i in range(16):
            angle = 2 * math.pi * i / 16
            points.append((
                self.__x + self.__radius * math.cos(angle),
                self.__y + self.__radius * math.sin(angle)
            ))
        return points

    def contains_point(self, x, y):
        return ((x - self.__x) ** 2 + (y - self.__y) ** 2
                <= self.__radius ** 2)

    def paint(self, canvas):
        count = max(16, math.ceil(4 * math.pi * self.__radius))
        points = []
        for i in range(count):
            angle = 2 * math.pi * i / count
            points.append((
                self.__x + self.__radius * math.cos(angle),
                self.__y + self.__radius * math.sin(angle)
            ))
        _paint_outline(canvas, points, self.get_char())


    def to_dict(self):
        return {
            "type": "Circle",
            "parameters": {
                "radius": self.__radius, "x": self.__x,
                "y": self.__y, "char": self.get_char()
            }
        }


class Triangle(Shape):
    def __init__(self, x1, y1, x2, y2, x3, y3, char="*"):
        super().__init__(char)
        self.__x1, self.__y1 = x1, y1
        self.__x2, self.__y2 = x2, y2
        self.__x3, self.__y3 = x3, y3

    def area(self):
        return abs(
            self.__x1 * (self.__y2 - self.__y3)
            + self.__x2 * (self.__y3 - self.__y1)
            + self.__x3 * (self.__y1 - self.__y2)
        ) / 2

    def perimeter(self):
        side1 = math.hypot(self.__x2 - self.__x1, self.__y2 - self.__y1)
        side2 = math.hypot(self.__x3 - self.__x2, self.__y3 - self.__y2)
        side3 = math.hypot(self.__x1 - self.__x3, self.__y1 - self.__y3)
        return side1 + side2 + side3

    def get_x(self):
        return self.__x1

    def get_y(self):
        return self.__y1

    def get_vertices(self):
        return [(self.__x1, self.__y1), (self.__x2, self.__y2),
                (self.__x3, self.__y3)]

    def perimeter_points(self):
        return self.get_vertices()

    def contains_point(self, x, y):
        a, b, c = self.get_vertices()
        point = (x, y)

        def cross(p1, p2, p3):
            return ((p2[0] - p1[0]) * (p3[1] - p1[1])
                    - (p2[1] - p1[1]) * (p3[0] - p1[0]))

        if cross(a, b, c) == 0:
            return False
        side1 = cross(a, b, point)
        side2 = cross(b, c, point)
        side3 = cross(c, a, point)
        return ((side1 >= 0 and side2 >= 0 and side3 >= 0)
                or (side1 <= 0 and side2 <= 0 and side3 <= 0))

    def paint(self, canvas):
        _paint_outline(canvas, self.perimeter_points(), self.get_char())


    def to_dict(self):
        return {
            "type": "Triangle",
            "parameters": {
                "x1": self.__x1, "y1": self.__y1,
                "x2": self.__x2, "y2": self.__y2,
                "x3": self.__x3, "y3": self.__y3,
                "char": self.get_char()
            }
        }


class CompoundShape(Shape):
    """Group shapes so one paint() call draws them all, as in Lecture 9.

Area and perimeter of a union are not calculated by this drawing group.
"""

    def __init__(self, shapes):
        super().__init__()
        self.__shapes = list(shapes)

    def get_shapes(self):
        return list(self.__shapes)

    def add_shape(self, shape):
        self.__shapes.append(shape)

    def paint(self, canvas):
        for shape in self.__shapes:
            shape.paint(canvas)

    def contains_point(self, x, y):
        return any(shape.contains_point(x, y) for shape in self.__shapes)

    def overlaps(self, other):
        return any(shape.overlaps(other) for shape in self.__shapes)

    def to_dict(self):
        return {
            "type": "CompoundShape",
            "shapes": [shape.to_dict() for shape in self.__shapes]
        }


def _shape_from_dict(data):
    """Rebuild a shape from its saved type and constructor parameters."""
    if data["type"] == "CompoundShape":
        return CompoundShape([
            _shape_from_dict(child) for child in data["shapes"]
        ])

    constructors = {
        "Rectangle": Rectangle,
        "Circle": Circle,
        "Triangle": Triangle
    }
    if data["type"] not in constructors:
        raise ValueError("Unknown saved shape type: " + str(data["type"]))

    constructor = constructors[data["type"]]
    return constructor(**data["parameters"])


class RasterDrawing:
    """Keep named shapes so a drawing can be changed and repainted."""

    def __init__(self):
        self.__shapes = {}

    def add_shape(self, shape, name=None):
        if name is None:
            i = 0
            while "shape_" + str(i) in self.__shapes:
                i += 1
            name = "shape_" + str(i)

        if name in self.__shapes:
            raise ValueError("A shape with that name already exists.")

        self.__shapes[name] = shape
        return name

    def replace_shape(self, name, shape):
        if name not in self.__shapes:
            raise KeyError("No shape has that name.")
        self.__shapes[name] = shape

    def remove_shape(self, name):
        del self.__shapes[name]

    def paint(self, canvas):
        for shape in self.__shapes.values():
            shape.paint(canvas)

    def update(self, canvas):
        canvas.clear_canvas()
        self.paint(canvas)

    def save(self, filename):
        data = {
            "shapes": [
                {"name": name, "shape": shape.to_dict()}
                for name, shape in self.__shapes.items()
            ]
        }
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)


def load_drawing(filename):
    """Load a saved drawing as new shape objects that can still be edited."""
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    drawing = RasterDrawing()
    for entry in data["shapes"]:
        shape = _shape_from_dict(entry["shape"])
        drawing.add_shape(shape, entry["name"])
    return drawing
