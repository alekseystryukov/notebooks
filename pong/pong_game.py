#!/usr/bin/env python
import pygame
from pygame.locals import *
from sys import exit


class Game:

    def __init__(self):

        pygame.init()

        self.screen = pygame.display.set_mode((640,480),0,32)
        pygame.display.set_caption("Pong Pong!")

        #Creating 2 bars, a ball and background.
        back = pygame.Surface((640, 480))
        self.background = back.convert()
        self.background.fill((0,0,0))
        bar = pygame.Surface((10,50))
        self.bar1 = bar.convert()
        self.bar1.fill((0,0,255))
        self.bar2 = bar.convert()
        self.bar2.fill((255,0,0))
        circ_sur = pygame.Surface((15,15))
        self.circ = pygame.draw.circle(circ_sur,(0,255,0),(15/2,15/2),15/2)
        self.circle = circ_sur.convert()
        self.circle.set_colorkey((0,0,0))

        # some definitions
        self.bar1_x, self.bar2_x = 10., 620.
        self.bar1_y_los_pos = None
        self.bar1_y, self.bar2_y = 215., 215.
        self.circle_x, self.circle_y = 307.5, 232.5
        self.bar1_move, self.bar2_move = 0., 0.
        self.ai_speed = 0
        self.speed_x,self.speed_y, self.speed_circ = 250., 250., 250.
        self.bar1_score, self.bar2_score = 0, 0
        #clock and font objects
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("calibri", 40)

    def update(self):

        for event in pygame.event.get():
            if event.type == QUIT:
                exit()
            if event.type == KEYDOWN:
                if event.key == K_UP:
                    self.bar1_move = -self.ai_speed
                elif event.key == K_DOWN:
                    self.bar1_move = self.ai_speed
            elif event.type == KEYUP:
                if event.key == K_UP:
                    self.bar1_move = 0.
                elif event.key == K_DOWN:
                    self.bar1_move = 0.

        self.score1 = self.font.render(str(self.bar1_score), True, (255,255,255))
        self.score2 = self.font.render(str(self.bar2_score), True, (255,255,255))

        self.screen.blit(self.background,(0,0))
        frame = pygame.draw.rect(self.screen,(255,255,255),Rect((5,5),(630,470)),2)
        middle_line = pygame.draw.aaline(self.screen,(255,255,255),(330,5),(330,475))
        self.screen.blit(self.bar1,(self.bar1_x,self.bar1_y))
        self.screen.blit(self.bar2,(self.bar2_x,self.bar2_y))
        self.screen.blit(self.circle,(self.circle_x,self.circle_y))
        self.screen.blit(self.score1,(250.,210.))
        self.screen.blit(self.score2,(380.,210.))

        self.bar1_y += self.bar1_move

        # movement of circle
        time_passed = self.clock.tick(3000)
        time_sec = time_passed / 1000.0

        self.circle_x += self.speed_x * time_sec
        self.circle_y += self.speed_y * time_sec
        self.ai_speed = self.speed_circ * time_sec
        # AI of the computer.
        if self.circle_x >= 305.:
            if not self.bar2_y == self.circle_y + 7.5:
                if self.bar2_y < self.circle_y + 7.5:
                    self.bar2_y += self.ai_speed
                if self.bar2_y > self.circle_y - 42.5:
                    self.bar2_y -= self.ai_speed
            else:
                self.bar2_y = self.circle_y + 7.5

        if self.bar1_y >= 420:
            self.bar1_y = 420.
        elif self.bar1_y <= 10:
            self.bar1_y = 10.
        if self.bar2_y >= 420:
            self.bar2_y = 420.
        elif self.bar2_y <= 10:
            self.bar2_y = 10.

        # since i don't know anything about collision, ball hitting bars goes like this.
        if self.circle_x <= self.bar1_x + 10:
            if self.bar1_y - 7.5 <= self.circle_y <= self.bar1_y + 42.5:
                self.circle_x = 20.
                self.speed_x = -self.speed_x
        if self.circle_x >= self.bar2_x - 15:
            if self.bar2_y - 7.5 <= self.circle_y <= self.bar2_y + 42.5:
                self.circle_x = 605.
                self.speed_x = -self.speed_x

        # win and lose
        if self.circle_x < 5.:
            self.bar1_y_los_pos = self.circle_y
            self.bar2_score += 1
            self.circle_x, self.circle_y = 320., 232.5
            self.bar1_y, self.bar_2_y = 215., 215.
        elif self.circle_x > 620.:
            self.bar1_score += 1
            self.circle_x, self.circle_y = 307.5, 232.5
            self.bar1_y, self.bar2_y = 215., 215.

        # top and bottom
        if self.circle_y <= 10.:
            self.speed_y = -self.speed_y
            self.circle_y = 10.

        elif self.circle_y >= 457.5:
            self.speed_y = -self.speed_y
            self.circle_y = 457.5

        pygame.display.update()


if __name__ == "__main__":
    g = Game()
    while True:
        g.update()
