import numpy as np
from pong_game import Game
from collections import deque

np.random.seed(0)


def sigma(x):
    return 1 / (1 + np.exp(-x))


def sigma_der(x):
    return x * (1 - x)


class AI:

    def __init__(self):
        # initialize weights randomly with mean 0
        self.weights1 = np.random.random((4, 3))
        self.weights2 = np.random.random((3, 1))

    def activate(self, input_values):
        v1 = sigma(np.dot(input_values, self.weights1))
        return sigma(np.dot(v1, self.weights2))

    def train(self, tr_set, iterations=1000):

        for i in range(iterations):
            for inp, out in tr_set:
                # forward propagation
                l0 = inp
                l1 = sigma(np.dot(l0, self.weights1))
                l2 = sigma(np.dot(l1, self.weights2))

                # back error propagation
                l2_error = out - l2
                l2_delta = l2_error * sigma_der(l2)

                if i % 2 == 0:
                    self.weights2 += np.dot(l1.T, l2_delta)
                else:
                    l1_error = (self.weights2 * l2_error).T
                    l1_delta = l1_error * sigma_der(l1)
                    self.weights1 += np.dot(l0.T, l1_delta)


if __name__ == "__main__":
    ai = AI()

    g = Game()
    positions = deque(maxlen=2)

    direction = None
    bar_position = None
    pred_input = None

    last_x = None

    train_data = []
    trained_times = 0

    while True:
        g.update()

        if last_x is None or abs(last_x - g.circle_x) > 100:
            positions.append((g.circle_x / 640, g.circle_y / 420))
            last_x = g.circle_x

        if len(positions) > 1:
            new_direction = int(positions[0][0] > positions[1][0])
            if new_direction != direction:
                direction = new_direction
                bar_position = None

        if len(positions) > 1 and bar_position is None and direction:
            pred_input = np.array([[positions[0][0], positions[0][1], positions[1][0], positions[1][1]]])
            res = ai.activate(pred_input)[0][0]
            bar_position = res * 420 - 25

        if bar_position is not None and bar_position != g.bar1_y:
            if bar_position > g.bar1_y:
                g.bar1_move = g.ai_speed
            else:
                g.bar1_move = -g.ai_speed
        else:
            g.bar1_move = 0

        if g.bar1_y_los_pos is not None:
            if len(train_data) < 40:
                train_data.append(
                    (
                        pred_input,
                        np.array([[g.bar1_y_los_pos / 420]]),
                    )
                )
                trained_times = 0

            bar_position = None
            g.bar1_y_los_pos = None

        if train_data and trained_times < 100:
            print(len(train_data), trained_times)
            ai.train(train_data, iterations=10)
            trained_times += 1

