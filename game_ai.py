from game import Game
from datetime import datetime
import pygame
from pygame.locals import *
import cv2
from game_ai_model import AI
from time import sleep
from optparse import OptionParser


class AIConnector:

    regular_task_interval = .5 * 10 ** 6  # 0.5sec
    regular_task_last_run = datetime(1988, 11, 21)

    def __init__(self):
        parser = OptionParser()
        parser.add_option("-f", "--file", dest="file",
                          help="write model to FILE", metavar="FILE")
        options, args = parser.parse_args()

        self.game = None
        self.images = []
        self.actions = []
        self.ai = AI(options.file)

    def init(self, game):
        self.game = game

    def on_game_start(self):
        self.images = []
        self.actions = []

    def regular_task(self, time):
        if (time - self.regular_task_last_run).microseconds < self.regular_task_interval:
            return
        self.regular_task_last_run = time

        if self.game.is_started:
            frame = pygame.surfarray.array3d(self.game.screen)
            frame = frame.swapaxes(0, 1)
            frame = cv2.resize(frame, (84, 84))  # 160, 90
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, frame = cv2.threshold(frame, 127, 255, cv2.THRESH_BINARY)
            self.images.append(frame)

            action = self.ai.eval(frame)
            self.actions.append(action)

            if action in (1, 3):
                move = pygame.event.Event(KEYDOWN, key=K_LEFT)
                pygame.event.post(move)

            if action in (2, 4):
                move = pygame.event.Event(KEYDOWN, key=K_RIGHT)
                pygame.event.post(move)

            if action in (3, 4):
                move = pygame.event.Event(KEYDOWN, key=K_UP)
                pygame.event.post(move)
        else:
            self.game.start_game()

    def on_game_win(self, score):
        self.ai.train(self.images, self.actions, score * 10)
        sleep(1)

    def on_game_los(self, score):
        self.ai.train(self.images, self.actions, score)
        sleep(1)


if __name__ == "__main__":
    ai_connect = AIConnector()
    g = Game(ai_connect)
    while True:
        g.update()
