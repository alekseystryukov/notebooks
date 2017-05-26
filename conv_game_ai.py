from game import Game
from datetime import datetime
import pygame
from pygame.locals import *
from time import sleep
from optparse import OptionParser
import tensorflow as tf
import os
import numpy as np
import random
import cv2

INPUTS = 3  # iteration, circle_x, circle_y
ACTIONS = 6  # none, jump, move left, jump left, move right, jump right


class ConvAI:

    def __init__(self, filename=None):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.variables_file = os.path.join(dir_path, filename or "conv_model.ckpt")

        self.stats = tf.Variable(tf.zeros([2]), name="statistic")  # wins, min time
        self.input = tf.placeholder("float", [None, 100, 100, 1])
        self.labels = tf.placeholder(tf.float32, shape=[None, ACTIONS])

        # Convolutional Layer #1
        conv1 = tf.layers.conv2d(
            inputs=self.input,
            filters=32,
            kernel_size=5,
            padding="same",
            activation=tf.nn.relu,
        )

        # Pooling Layer #1
        pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2], strides=2)

        # Convolutional Layer #2 and Pooling Layer #2
        conv2 = tf.layers.conv2d(
            inputs=pool1,
            filters=64,
            kernel_size=5,
            padding="same",
            activation=tf.nn.relu)
        pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)

        # Dense Layer
        pool2_flat = tf.reshape(pool2, [-1, 25 * 25 * 64])
        dense = tf.layers.dense(inputs=pool2_flat, units=1024, activation=tf.nn.relu)
        self.y = tf.layers.dense(inputs=dense, units=ACTIONS)

        self.session = tf.InteractiveSession()

        cross_entropy = tf.reduce_mean(
            tf.nn.softmax_cross_entropy_with_logits(labels=self.labels, logits=self.y)
        )
        self.train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
        self.session.run(tf.global_variables_initializer())

        # saver
        self.saver = tf.train.Saver()
        if os.path.exists("{}.meta".format(self.variables_file)):
            self.saver.restore(self.session, self.variables_file)
            print("Model is restored.")

    def eval(self, inp_t):
        out_t = self.y.eval(feed_dict={self.input: [inp_t]})
        return tf.argmax(out_t, 1).eval()[0]

    def train(self, inputs, actions, reward_t):

        labels_batch = []
        for ac in actions:
            labels = np.zeros([ACTIONS])
            labels[ac] = 1
            labels_batch.append(labels)

        # arg-max function
        print("Train iterations:", reward_t)
        for i in range(reward_t):
            self.train_step.run(feed_dict={self.input: inputs, self.labels: labels_batch})

        self.saver.save(self.session, self.variables_file)


class AIConnector:

    regular_task_interval = .5 * 10 ** 6  # 0.5sec
    regular_task_last_run = datetime(1988, 11, 21)

    def __init__(self):
        parser = OptionParser()
        parser.add_option("-f", "--file", dest="file",
                          help="write model to FILE", metavar="FILE")
        parser.add_option("-t", "--train", dest="train",
                          help="train AI", metavar="TRAIN")
        parser.add_option("-r", "--random", dest="random",
                          help="use random actions to train AI", metavar="RANDOM")
        options, args = parser.parse_args()

        self.game = None
        self.inputs = []
        self.actions = []
        self.ai = ConvAI(options.file)
        self.train = int(options.train) if options.train is not None else 0
        self.random = int(options.random or 0)

    def init(self, game):
        self.game = game

    def on_game_start(self):
        self.inputs = []
        self.actions = []

    def regular_task(self, time):
        if (time - self.regular_task_last_run).microseconds < self.regular_task_interval:
            return
        self.regular_task_last_run = time

        if self.game.is_started:
            frame = pygame.surfarray.array3d(self.game.screen)
            frame = frame.swapaxes(0, 1)
            frame = cv2.resize(frame, (100, 100))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, frame = cv2.threshold(frame, 127, 255, cv2.THRESH_BINARY)
            frame = np.reshape(frame, (100, 100, 1))

            if self.random and random.randint(1, 100) <= self.random:
                action = random.randint(0, ACTIONS - 1)
                print("Random action {}".format(action))
            else:
                action = self.ai.eval(frame)
                print("Action from the model {}".format(action))

            self.inputs.append(frame)
            self.actions.append(action)

            if action in (2, 3):
                move = pygame.event.Event(KEYDOWN, key=K_LEFT)
                pygame.event.post(move)

            if action in (4, 5):
                move = pygame.event.Event(KEYDOWN, key=K_RIGHT)
                pygame.event.post(move)

            if action in (1, 3, 5):
                move = pygame.event.Event(KEYDOWN, key=K_UP)
                pygame.event.post(move)
        else:
            self.game.start_game()

    def on_game_win(self, time):
        wins, min_time = self.ai.session.run(self.ai.stats)
        print(wins, min_time)

        if self.train and (self.game.win_rate < 100 and time <= min_time + self.train or
                           time < min_time or not min_time):
            speed = 120 / len(self.actions)
            self.ai.train(self.inputs, self.actions, int(100 * speed))

            wins += 1
            if not min_time or min_time > time:
                min_time = time
            assign_op = self.ai.stats.assign([wins, min_time])
            self.ai.session.run(assign_op)
            sleep(1)

    def on_game_los(self, score):
        pass


if __name__ == "__main__":
    ai_connect = AIConnector()
    g = Game(ai_connect)
    while True:
        g.update()
