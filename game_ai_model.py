import tensorflow as tf
import os
import numpy as np

ACTIONS = 5  # none, move left, move right, jump left, jump right
# define our learning rate
GAMMA = 0.99
# for updating our gradient or training over time
INITIAL_EPSILON = 1.0
FINAL_EPSILON = 0.05
# how many frames to anneal epsilon
EXPLORE = 500000
# store our experiences, the size of it
REPLAY_MEMORY = 500000
# batch size to train on
BATCH = 100


def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)


def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)


class AI:

    def __init__(self, file=None):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.variables_file = os.path.join(dir_path, file or "model.ckpt")

        w1 = weight_variable([8, 8, 4, 32])
        b1 = bias_variable([32])

        w2 = weight_variable([4, 4, 32, 64])
        b2 = bias_variable([64])

        w3 = weight_variable([3, 3, 64, 64])
        b3 = bias_variable([64])

        wfc4 = weight_variable([3136, 784])
        bfc4 = bias_variable([784])

        wfc5 = weight_variable([784, ACTIONS])
        bfc5 = bias_variable([ACTIONS])

        # input for pixel data
        self.input = tf.placeholder("float", [None, 84, 84, 4])
        self.labels = tf.placeholder(tf.float32, shape=[None, ACTIONS])

        # Computes rectified linear unit activation function on  a 2-D convolution given 4-D input and filter tensors
        conv1 = tf.nn.relu(tf.nn.conv2d(self.input, w1, strides=[1, 4, 4, 1], padding="VALID") + b1)
        conv2 = tf.nn.relu(tf.nn.conv2d(conv1, w2, strides=[1, 2, 2, 1], padding="VALID") + b2)
        conv3 = tf.nn.relu(tf.nn.conv2d(conv2, w3, strides=[1, 1, 1, 1], padding="VALID") + b3)
        conv3_flat = tf.reshape(conv3, [-1, 3136])
        fc4 = tf.nn.relu(tf.matmul(conv3_flat, wfc4) + bfc4)

        self.fc5 = tf.matmul(fc4, wfc5) + bfc5
        self.session = tf.InteractiveSession()

        cross_entropy = tf.reduce_mean(
            tf.nn.softmax_cross_entropy_with_logits(labels=self.labels, logits=self.fc5)
        )
        self.train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
        self.session.run(tf.global_variables_initializer())

        # saver
        self.saver = tf.train.Saver()
        if os.path.exists(self.variables_file):
            self.saver.restore(self.session, self.variables_file)
            print("Model is restored.")

    def eval(self, frame):
        inp_t = np.stack((frame, frame, frame, frame), axis=2)
        inp_t = np.reshape(inp_t, (1, 84, 84, 4))
        out_t = self.fc5.eval(feed_dict={self.input: inp_t})
        return tf.argmax(out_t, 1).eval()[0]

    def train(self, inputs, actions, reward_t):
        # output tensor
        input_batch = []
        for inp in inputs:
            inp_t = np.stack((inp, inp, inp, inp), axis=2)
            input_batch.append(inp_t)

        labels_batch = []
        for ac in actions:
            labels = np.zeros([ACTIONS])
            labels[ac] = 1
            labels_batch.append(labels)

        # arg-max function
        for i in range(reward_t):
            self.train_step.run(feed_dict={self.input: input_batch, self.labels: labels_batch})
            print("train step#{}".format(i))

        self.saver.save(self.session, self.variables_file)
