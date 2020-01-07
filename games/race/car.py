import pyglet, math
from pyglet.window import key
from resources import car_image
from utils import abs_extract, min_abs_value


class Car(pyglet.sprite.Sprite):

    def __init__(self, track, window):
        super(Car, self).__init__(img=car_image,  x=950, y=445)

        self.track = track
        # Velocity
        self.velocity_x, self.velocity_y = 0.0, 0.0
        self.rotation = 316
        self.move_ahead = 1

        # Set some easy-to-tweak constants
        self.power = 300.0
        self.max_speed = 100.0
        self.rotate_speed = 100.0
        self.friction = 50
        self.stabilization = 0.9
        self.breaks = 0.9
        self.crash = 0.7

        # Tell the game handler about any event handlers
        self.key_handler = key.KeyStateHandler()
        window.push_handlers(self.key_handler)

    def update(self, dt):
        max_retries = 5
        while max_retries:
            # Update position according to velocity and time
            new_x = self.x + self.velocity_x * dt
            new_y = self.y + self.velocity_y * dt
            # check collisions
            left, right = self.get_bounds(new_x, new_y)
            left_touch = not self.track.position_is_on_track(*left)
            right_touch = not self.track.position_is_on_track(*right)
            if left_touch and right_touch:
                self.velocity_x = self.velocity_y = 0
                break
            elif left_touch:
                self.multiply_velocity(self.crash)
                self.turn(dt, 1)
            elif right_touch:
                self.multiply_velocity(self.crash)
                self.turn(dt, -1)
            else:
                self.x = new_x
                self.y = new_y
                break
            max_retries -= 1

        self.extract_friction(dt)

        # handle key presses
        if self.key_handler[key.SPACE]:
            self.multiply_velocity(self.breaks)
        else:
            if self.key_handler[key.LEFT]:
                self.turn(dt, -1)
            elif self.key_handler[key.RIGHT]:
                self.turn(dt)

            if self.key_handler[key.UP]:
                self.move_ahead = 1
                self.move(dt)
            elif self.key_handler[key.DOWN]:
                self.move_ahead = -1
                self.move(dt)

    def extract_friction(self, dt):
        force = self.friction * dt
        self.velocity_x = abs_extract(self.velocity_x, force)
        self.velocity_y = abs_extract(self.velocity_y, force)

    def multiply_velocity(self, multiplier):
        self.velocity_x *= multiplier
        self.velocity_y *= multiplier

    def turn(self, dt, direction=1):
        """
        :param dt:
        :param direction:  1 - right, -1 left
        :return:
        """
        self.rotation = self.rotation + direction * self.move_ahead * self.rotate_speed * dt * self.relative_velocity
        # -------
        # stabilization - is amount of speed that gets redirected to the new direction
        redirected_velocity = self.abs_velocity * self.stabilization
        direction_vector = self.direction_vector
        # decrease speed along prev direction
        self.multiply_velocity(1 - self.stabilization)
        # add some speed along new direction
        self.velocity_x += direction_vector[0] * redirected_velocity
        self.velocity_y += direction_vector[1] * redirected_velocity

    def move(self, dt):
        direction_vector = self.direction_vector
        force_x = direction_vector[0] * self.power * dt * self.move_ahead
        force_y = direction_vector[1] * self.power * dt * self.move_ahead

        max_x = abs(direction_vector[0]) * self.max_speed
        max_y = abs(direction_vector[1]) * self.max_speed
        self.velocity_x = min_abs_value(self.velocity_x + force_x, max_x)
        self.velocity_y = min_abs_value(self.velocity_y + force_y, max_y)

    @property
    def direction_vector(self):
        angle_radians = math.radians(self.rotation)
        return [math.sin(angle_radians), math.cos(angle_radians)]

    @property
    def relative_velocity(self):
        return self.abs_velocity / self.max_speed

    @property
    def abs_velocity(self):
        return math.sqrt(self.velocity_y ** 2 + self.velocity_x ** 2)

    def get_bounds(self, rel_x, rel_y):
        anchor_y = car_image.anchor_y + 5
        if self.move_ahead > 0:  # top
            left = - car_image.anchor_x, car_image.height - anchor_y
            right = car_image.width - car_image.anchor_x, car_image.height - anchor_y
        else:
            left = - car_image.anchor_x, - anchor_y
            right = car_image.width - car_image.anchor_x, - anchor_y

        # rotate
        angle = -math.radians(self.rotation)
        cos = math.cos(angle)
        sin = math.sin(angle)
        rotated_vectors = [(x * cos - y * sin, x * sin + y * cos)
                           for x, y in (left, right)]
        # add relative pos
        abs_positions = [(int(rel_x + x), int(rel_y + y)) for x, y in rotated_vectors]
        return abs_positions

    # lap events and methods
    _finish_visited = False

    @property
    def crossed_finish(self):
        if self.track.position_is_on_finish(self.x, self.y):
            self._finish_visited = True
        elif self._finish_visited:
            self._finish_visited = False
            return True
        return False
