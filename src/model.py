# Most of the tensorflow code is adapted from Tensorflow's tutorial on using
# CNNs to train MNIST
# https://www.tensorflow.org/get_started/mnist/pros#build-a-multilayer-convolutional-network.  # noqa: E501

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ray
import tensorflow as tf
import dataset

def load_data(data_dir="../data/"):
    return dataset.read_data_sets(data_dir)

class simple(object):
    def __init__(self, learning_rate=1e-4):
        with tf.Graph().as_default():

            # Create the model
            self.x = tf.placeholder(tf.float32, [None, 500])

            # Define loss and optimizer
            self.y_ = tf.placeholder(tf.float32, [None, 3])

            self.w = tf.Variable(tf.zeros([500, 3]))
            self.b = tf.Variable(tf.zeros([3]))
            self.y = tf.nn.softmax(tf.matmul(self.x, self.w) + self.b)

            with tf.name_scope('loss'):
                self.cross_entropy = tf.reduce_mean(-tf.reduce_sum(self.y_ * tf.log(self.y), reduction_indices=[1]))

            with tf.name_scope('adam_optimizer'):
                self.optimizer = tf.train.AdamOptimizer(learning_rate)
                self.train_step = self.optimizer.minimize(self.cross_entropy)

            with tf.name_scope('accuracy'):
                correct_prediction = tf.equal(tf.argmax(self.y, 1), tf.argmax(self.y_, 1))
                correct_prediction = tf.cast(correct_prediction, tf.float32)
            self.accuracy = tf.reduce_mean(correct_prediction)

            self.sess = tf.Session(config=tf.ConfigProto(
                intra_op_parallelism_threads=1,
                inter_op_parallelism_threads=1))
            self.sess.run(tf.global_variables_initializer())

            # Helper values.

            self.variables = ray.experimental.TensorFlowVariables(
                self.cross_entropy, self.sess)

            self.grads = self.optimizer.compute_gradients(
                self.cross_entropy)
            self.grads_placeholder = [
                (tf.placeholder("float", shape=grad[1].get_shape()), grad[1])
                for grad in self.grads]
            self.apply_grads_placeholder = self.optimizer.apply_gradients(
                self.grads_placeholder)

    def compute_update(self, x, y):
        # TODO(rkn): Computing the weights before and after the training step
        # and taking the diff is awful.
        weights = self.get_weights()[1]
        self.sess.run(self.train_step, feed_dict={self.x: x, self.y_: y})
        new_weights = self.get_weights()[1]
        return [x - y for x, y in zip(new_weights, weights)]

    def compute_gradients(self, x, y):
        return self.sess.run([grad[0] for grad in self.grads],
                             feed_dict={self.x: x, self.y_: y})

    def apply_gradients(self, gradients):
        feed_dict = {}
        for i in range(len(self.grads_placeholder)):
            feed_dict[self.grads_placeholder[i][0]] = gradients[i]
        self.sess.run(self.apply_grads_placeholder, feed_dict=feed_dict)

    def compute_accuracy(self, x, y):
        return self.sess.run(self.accuracy,
                             feed_dict={self.x: x, self.y_: y})

    def set_weights(self, variable_names, weights):
        self.variables.set_weights(dict(zip(variable_names, weights)))

    def get_weights(self):
        weights = self.variables.get_weights()
        return list(weights.keys()), list(weights.values())

