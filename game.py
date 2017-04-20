#!/usr/bin/env python
import pygame
from pygame.locals import *
from sys import exit
from datetime import datetime
import math


SCREEN = (1280, 720)
SCREEN_FPS = 60
SCREEN_UPDATE_INTERVAL = 10 ** 6 / SCREEN_FPS  # microseconds

BALL_RADIUS = 40
BALL_DIAMETER = BALL_RADIUS * 2

MOVE_SPEED = 180
JUMP_SPEED = 500

AIR_FRICTION = 40
PLATFORM_FRICTION = 150
GRAVITY = 500
ELASTICITY = .25

WHITE = (255, 255, 255)
BACKGROUND_COLOR = Color("#2b2a45")
BALL_COLOR = Color("#c78a84")
PLATFORM_COLOR = Color("#5483fb")

PLATFORM_PARAMS = (SCREEN[0] / 8, 10)

PLATFORM_HEIGHTS = (
    355,
    540,
    300,
    540,
    300,
    540,
    300,
    355,
)

GAME_DURATION = 60
DEAD_LINE = 550


class Game:

    def __init__(self):

        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN, 0, 32)
        pygame.display.set_caption("Notebook12")

        background = pygame.Surface(SCREEN)
        self.background = background.convert()
        self.background.fill(BACKGROUND_COLOR)

        self.platforms = []
        for i in range(len(PLATFORM_HEIGHTS)):
            platform = pygame.Surface(PLATFORM_PARAMS)
            platform = platform.convert()
            platform.fill(PLATFORM_COLOR)
            self.platforms.append(platform)

        circle_sur = pygame.Surface((BALL_DIAMETER, BALL_DIAMETER))
        self.circle = pygame.draw.circle(circle_sur, BALL_COLOR, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
        self.circle = circle_sur.convert()
        self.circle.set_colorkey((0, 0, 0))
        self.circle_x = self.circle_y = self.speed_x = self.speed_y = 0
        self.game_start = datetime.now()
        self.reset_game()

        self.best_score = None
        self.clock = pygame.time.Clock()
        self.last_screen_update = datetime.now()
        self.font = pygame.font.SysFont("calibri", 40)

    def reset_game(self):
        self.circle_x, self.circle_y = 0, PLATFORM_HEIGHTS[0] - BALL_DIAMETER
        self.speed_x = self.speed_y = 0
        self.game_start = datetime.now()

    def update(self):
        now = datetime.now()
        time_passed = self.clock.tick(500)
        time_sec = time_passed / 1000

        #  COLLISIONS
        # top and bottom
        height = SCREEN[1] - BALL_DIAMETER
        if self.circle_y <= 0:
            self.speed_y = -self.speed_y * ELASTICITY
            self.circle_y = 0

        elif self.circle_y >= height:
            self.speed_y = -self.speed_y * ELASTICITY
            self.circle_y = height

        # left and right
        width = SCREEN[0] - BALL_DIAMETER
        if self.circle_x <= 0:
            self.speed_x = -self.speed_x * ELASTICITY
            self.circle_x = 0

        elif self.circle_x >= width:
            self.speed_x = -self.speed_x * ELASTICITY
            self.circle_x = width

        # platforms
        for n, y in enumerate(PLATFORM_HEIGHTS):
            x = n * PLATFORM_PARAMS[0]
            coll = manage_collisions(self.circle_x, self.circle_y, BALL_RADIUS,
                                     self.speed_x, self.speed_y,
                                     x, y, *PLATFORM_PARAMS)
            if coll:
                self.circle_x, self.circle_y, self.speed_x, self.speed_y = coll

        ball_is_controllable = False
        ball_is_on_platform = False
        for n, y in enumerate(PLATFORM_HEIGHTS):
            if 0 <= y - (self.circle_y + BALL_DIAMETER) < 10:
                w = PLATFORM_PARAMS[0]
                x = n * w
                if x + w >= self.circle_x + BALL_RADIUS >= x:
                    ball_is_controllable = True
                    if y - (self.circle_y + BALL_DIAMETER) < 2:
                        ball_is_on_platform = True

                        # if it is the last one, you win
                        if len(PLATFORM_HEIGHTS) - n == 1:
                            self.best_score = (now - self.game_start).seconds
                            self.reset_game()
        # PHYSICS
        # friction
        abs_speed_x = abs(self.speed_x)
        friction_speed_x = AIR_FRICTION * time_sec
        if ball_is_on_platform:
            friction_speed_x += PLATFORM_FRICTION * time_sec
        new_abs_speed = max(abs_speed_x - friction_speed_x, 0)
        self.speed_x = new_abs_speed * (-1 if self.speed_x < 0 else 1)

        abs_speed_y = abs(self.speed_y)
        new_abs_speed = max(abs_speed_y - AIR_FRICTION * time_sec, 0)
        self.speed_y = new_abs_speed * (-1 if self.speed_y < 0 else 1)
        # gravity
        if not ball_is_on_platform:
            self.speed_y += GRAVITY * time_sec

        for event in pygame.event.get():
            if event.type == QUIT:
                exit()

            if ball_is_controllable:
                if event.type == KEYDOWN:
                    if event.key == K_UP:
                        self.speed_y = -JUMP_SPEED
                    elif event.key == K_DOWN:
                        self.speed_y = JUMP_SPEED
                    elif event.key == K_RIGHT:
                        self.speed_x = MOVE_SPEED
                    elif event.key == K_LEFT:
                        self.speed_x = -MOVE_SPEED

        # new ball position
        self.circle_x += self.speed_x * time_sec
        self.circle_y += self.speed_y * time_sec

        if (now - self.last_screen_update).microseconds > SCREEN_UPDATE_INTERVAL:
            self.last_screen_update = now
            # draw the world
            self.screen.blit(self.background, (0, 0))
            for n, platform in enumerate(self.platforms):
                self.screen.blit(platform, (n * PLATFORM_PARAMS[0], PLATFORM_HEIGHTS[n]))

            self.screen.blit(self.circle, (self.circle_x, self.circle_y))

            timer = (datetime.now() - self.game_start).seconds
            time_title = self.font.render("Timer:".format(timer), True, WHITE)
            time = self.font.render("{} sec".format(timer), True, WHITE)
            score_title = self.font.render("Best score:", True, WHITE)
            score = self.font.render("-" if self.best_score is None else"{} sec".format(self.best_score), True, WHITE)
            self.screen.blit(time_title, (30, 20))
            self.screen.blit(time, (40, 60))
            self.screen.blit(score_title, (SCREEN[0] - 170, 20))
            self.screen.blit(score, (SCREEN[0] - 140, 60))

            if timer > GAME_DURATION or self.circle_y > DEAD_LINE:
                self.reset_game()

            pygame.display.update()


def manage_collisions(x1, y1, r, sx1, sy1, x2, y2, w2, h2):  # rectangles collision
    center_x, center_y = x1 + r, y1 + r

    x_collision = y_collision = False

    new_x1, new_y1 = x1, y1
    new_speed_x1 = sx1
    new_speed_y1 = sy1

    # check simple(flat) cases
    if x2 + w2 > center_x > x2:  # is under or upper of the rectangle
        x_collision = True

        if y2 + h2 / 2 >= center_y >= y2 - r:  # collides from the top
            y_collision = True
            new_speed_y1 = -new_speed_y1 * ELASTICITY
            new_y1 = y2 - r * 2

        elif y2 + h2 + r >= center_y > y2 + h2 / 2:  # collides from the bottom
            y_collision = True
            new_speed_y1 = -new_speed_y1 * ELASTICITY
            new_y1 = y2 + h2

    if y2 + h2 > center_y > y2:  # is from the left or right
        x_collision = True

        if x2 + w2 / 2 >= center_x >= x2 - r:   # collides from the left
            y_collision = True
            new_speed_x1 = -new_speed_x1 * ELASTICITY
            new_x1 = x2 - r * 2

        elif x2 + w2 + r >= center_x > x2 + w2 / 2:  # collides from the right
            y_collision = True
            new_speed_x1 = -new_speed_x1 * ELASTICITY
            new_x1 = x2 + w2

    # check collisions at the corners
    if not any((x_collision, y_collision)):

        half_x_speed = abs(new_speed_x1 * ELASTICITY) / 2
        half_y_speed = abs(new_speed_y1 * ELASTICITY) / 2

        if math.hypot(x2 - center_x, y2 - center_y) <= r:  # top left corner
            x_collision = y_collision = True
            new_speed_x1 = -1 * (half_x_speed + half_y_speed)
            new_speed_y1 = -1 * (half_x_speed + half_y_speed)
            new_x1 = x2 - math.sqrt(r * r - (y2 - center_y) ** 2) - r - 3

        elif math.hypot(x2 + w2 - center_x, y2 - center_y) < r:  # top right corner
            x_collision = y_collision = True
            new_speed_x1 = half_x_speed + half_y_speed
            new_speed_y1 = -1 * (half_x_speed + half_y_speed)
            new_x1 = x2 + w2 + math.sqrt(r * r - (y2 - center_y) ** 2) - r + 3

        elif math.hypot(x2 - center_x, y2 + h2 - center_y) <= r:  # bottom left corner
            x_collision = y_collision = True
            new_speed_x1 = -1 * (half_x_speed + half_y_speed)
            new_speed_y1 = half_x_speed + half_y_speed
            new_x1 = x2 - math.sqrt(r * r - (y2 + h2 - center_y) ** 2) - r

        elif math.hypot(x2 + w2 - center_x, y2 + h2 - center_y) <= r:  # bottom right corner
            x_collision = y_collision = True
            new_speed_x1 = half_x_speed + half_y_speed
            new_speed_y1 = half_x_speed + half_y_speed
            new_x1 = x2 + w2 + math.sqrt(r * r - (y2 + h2 - center_y) ** 2) - r

    return (new_x1, new_y1, new_speed_x1, new_speed_y1) if x_collision and y_collision else False


if __name__ == "__main__":
    g = Game()
    while True:
        try:
            g.update()
        except ValueError:
            break
