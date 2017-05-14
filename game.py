#!/usr/bin/env python
import pygame
from pygame.locals import *
from sys import exit
from datetime import datetime, timedelta
from collections import deque
import math

SCREEN = (1280, 720)
SCREEN_FPS = 30
SCREEN_UPDATE_INTERVAL = 10 ** 6 / SCREEN_FPS  # microseconds
MIN_UPDATES_PER_SECOND = 20  # required update cycle rate

BALL_RADIUS = 40
BALL_DIAMETER = BALL_RADIUS * 2

MOVE_SPEED = 180
JUMP_SPEED = 800

AIR_FRICTION = 40
PLATFORM_FRICTION = 150
GRAVITY = 1000
ELASTICITY = .10

WHITE = (255, 255, 255)
BACKGROUND_COLOR = Color("#2b2a45")
BALL_COLOR = Color("#c78a84")
PLATFORM_COLOR = Color("#5483fb")

PLATFORM_PARAMS = (SCREEN[0] / 8, 12)

PLATFORM_HEIGHTS = (
    355,
    200,
    640,
    240,
    400,
    550,
    100,
    355,
)
PLATFORM_SPEED = 50
GAME_DURATION = 60
TOP_LINE = 100
DEAD_LINE = 650


class Game:

    def __init__(self, ai_connect=None):
        self.ai_connect = ai_connect
        if self.ai_connect:
            self.ai_connect.init(self)

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
            if i == 0 or i + 1 == len(PLATFORM_HEIGHTS):
                speed = 0
            else:
                speed = PLATFORM_SPEED * (2 ** (i % 2))
            self.platforms.append(
                dict(
                    surface=platform,
                    x=i * PLATFORM_PARAMS[0],
                    y=PLATFORM_HEIGHTS[i],
                    speed=speed,
                )
            )

        circle_sur = pygame.Surface((BALL_DIAMETER, BALL_DIAMETER))
        self.circle = pygame.draw.circle(circle_sur, BALL_COLOR, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
        self.circle = circle_sur.convert()
        self.circle.set_colorkey((0, 0, 0))
        self.circle_x = self.circle_y = self.speed_x = self.speed_y = 0

        self.reset_game()

        self.stats = deque(maxlen=100)
        self.best_score = None
        self.is_started = False
        self.clock = pygame.time.Clock()
        now = datetime.now()
        self.last_screen_update = now
        self.game_start = now
        self.current_time = now
        self.font = pygame.font.SysFont("calibri", 40)

    def start_game(self):
        self.is_started = True
        now = datetime.now()
        self.game_start = now
        self.current_time = now
        if self.ai_connect:
            self.ai_connect.on_game_start()

    def reset_game(self):
        self.circle_x, self.circle_y = 0, PLATFORM_HEIGHTS[0] - BALL_DIAMETER
        self.speed_x = self.speed_y = 0
        self.is_started = False

        # set platforms into initial state
        for i, platform in enumerate(self.platforms):
            if i == 0 or i + 1 == len(PLATFORM_HEIGHTS):
                speed = 0
            else:
                speed = PLATFORM_SPEED * (2 ** (i % 2))
            platform['speed'] = speed
            platform['x'] = i * PLATFORM_PARAMS[0]
            platform['y'] = PLATFORM_HEIGHTS[i]

    def update(self):
        time_passed = self.clock.tick(100)  # milliseconds 500
        if 1000/time_passed < MIN_UPDATES_PER_SECOND:
            # if fps is too low, the game will run slower, but physics will work
            time_passed = 1000 / MIN_UPDATES_PER_SECOND
        self.current_time += timedelta(milliseconds=time_passed)  # all timers depend on fps
        time_sec = time_passed / 1000

        #  COLLISIONS
        # top and bottom
        if self.circle_y <= 0:
            self.speed_y = -self.speed_y * ELASTICITY
            self.circle_y = 0

        # left and right
        width = SCREEN[0] - BALL_DIAMETER
        if self.circle_x <= 0:
            self.speed_x = -self.speed_x * ELASTICITY
            self.circle_x = 0

        elif self.circle_x >= width:
            self.speed_x = -self.speed_x * ELASTICITY
            self.circle_x = width

        # platforms
        ball_is_controllable = False
        ball_is_on_platform = False
        for n, platform in enumerate(self.platforms):
            y, x = platform['y'], platform['x']

            # collisions
            coll = manage_collisions(self.circle_x, self.circle_y, BALL_RADIUS,
                                     self.speed_x, self.speed_y,
                                     x, y, *PLATFORM_PARAMS)
            if coll:
                self.circle_x, self.circle_y, self.speed_x, self.speed_y = coll
            # -- collisions

            if 0 <= y - (self.circle_y + BALL_DIAMETER) < 10:
                w = PLATFORM_PARAMS[0]
                if x + w >= self.circle_x + BALL_RADIUS >= x:
                    ball_is_controllable = True
                    if y - (self.circle_y + BALL_DIAMETER) < 2:
                        ball_is_on_platform = True

                        # if it is the last one, you win
                        if len(PLATFORM_HEIGHTS) - n == 1:
                            score = (self.current_time - self.game_start).seconds
                            if not self.best_score or self.best_score > score:
                                self.best_score = score
                            self.reset_game()
                            self.stats.append(1)

                            if self.ai_connect:
                                self.ai_connect.on_game_win(score)
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
            if self.speed_y > GRAVITY:
                self.speed_y = GRAVITY

        if self.ai_connect:
            self.ai_connect.regular_task(self.current_time)

        for event in pygame.event.get():
            if event.type == QUIT:
                exit()

            if event.type == KEYDOWN:
                if self.is_started:
                    if ball_is_controllable:
                        if event.key == K_UP:
                            self.speed_y = -JUMP_SPEED
                        elif event.key == K_DOWN:
                            self.speed_y = JUMP_SPEED
                        elif event.key == K_RIGHT:
                            self.speed_x = MOVE_SPEED
                        elif event.key == K_LEFT:
                            self.speed_x = -MOVE_SPEED
                else:
                    self.start_game()

        # new positions
        self.circle_x += self.speed_x * time_sec
        self.circle_y += self.speed_y * time_sec
        if self.is_started:
            for platform in self.platforms:
                if platform['y'] >= DEAD_LINE or platform['y'] <= TOP_LINE:
                    platform['y'] = DEAD_LINE if platform['y'] >= DEAD_LINE else TOP_LINE
                    platform['speed'] *= -1
                platform['y'] += platform['speed'] * time_sec

        if (self.current_time - self.last_screen_update).microseconds > SCREEN_UPDATE_INTERVAL:
            self.last_screen_update = self.current_time
            # draw the world
            self.screen.blit(self.background, (0, 0))
            for platform in self.platforms:
                self.screen.blit(platform['surface'], (platform['x'], platform['y']))

            self.screen.blit(self.circle, (self.circle_x, self.circle_y))

            score_title = self.font.render("Best score:", True, WHITE)
            score = self.font.render("-" if self.best_score is None else"{} sec".format(self.best_score), True, WHITE)
            self.screen.blit(score_title, (SCREEN[0] - 170, 20))
            self.screen.blit(score, (SCREEN[0] - 140, 60))

            wr_title = self.font.render("Win rate:", True, WHITE)
            wr = self.font.render(
                "{}% per {}".format(self.win_rate, len(self.stats)), True, WHITE)
            self.screen.blit(wr_title, (SCREEN[0] - 150, SCREEN[1] - 80))
            self.screen.blit(wr, (SCREEN[0] - 160, SCREEN[1] - 40))

            if self.is_started:
                timer = (self.current_time - self.game_start).seconds
                time_title = self.font.render("Timer:".format(timer), True, WHITE)
                time = self.font.render("{} sec".format(timer), True, WHITE)
                self.screen.blit(time_title, (30, 20))
                self.screen.blit(time, (40, 60))

                if timer > GAME_DURATION or self.circle_y > DEAD_LINE:
                    score = int(self.circle_x / BALL_DIAMETER)
                    self.reset_game()
                    self.stats.append(0)
                    if self.ai_connect:
                        self.ai_connect.on_game_los(score)
            else:
                start_text = self.font.render("Press any key to start the game", True, WHITE)
                self.screen.blit(start_text, (400, 350))

            pygame.display.update()

    @property
    def win_rate(self):
        return int(sum(self.stats)/len(self.stats)*100) if len(self.stats) else 0


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
            if new_speed_y1 > 0:
                new_speed_y1 = -abs(new_speed_y1 * ELASTICITY)
            new_y1 = y2 - r * 2

        elif y2 + h2 + r >= center_y > y2 + h2 / 2:  # collides from the bottom
            y_collision = True
            if new_speed_y1 < 0:
                new_speed_y1 = abs(new_speed_y1 * ELASTICITY)
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
        g.update()
