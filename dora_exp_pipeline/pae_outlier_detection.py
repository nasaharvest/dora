# This script implements a probabilistic autoencoder, as described in the
# following paper:
# Böhm, Vanessa, and Uroš Seljak. “Probabilistic Auto-Encoder.”
# ArXiv:2006.05479 [Cs, Stat], Oct. 2020.
#
# See copyright notice at end.
#
# Author: Bryce Dubayah
# Date created: August 16, 2021

from dora_exp_pipeline.outlier_detection import OutlierDetection
import numpy as np
from copy import deepcopy
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, losses
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow_probability import distributions, bijectors, layers as tfpl


class PAEOutlierDetection(OutlierDetection):
    def __init__(self):
        super(PAEOutlierDetection, self).__init__('pae')

    def _rank_internal(self, data_to_fit, data_to_score, data_to_score_ids,
                       top_n, seed, latent_dim):
        if data_to_fit is None:
            data_to_fit = deepcopy(data_to_score)

        if latent_dim < 1:
            raise RuntimeError('The dimensionality of the latent space must be '
                               '>= 1')

        # Check that the number of hidden layers <= number of features
        num_features = data_to_fit.shape[1]
        if latent_dim > num_features:
            raise RuntimeError(f'The dimensionality of the latent space'
                               f'(latent_dim = {latent_dim}) '
                               f'must be <= number of features '
                               f'({num_features})')

        # Rank targets
        scores = train_and_run_PAE(data_to_fit, data_to_score, latent_dim,
                                   num_features)
        selection_indices = np.argsort(scores)[::-1]

        results = dict()
        results.setdefault('scores', list())
        results.setdefault('sel_ind', list())
        results.setdefault('dts_ids', list())
        for ind in selection_indices[:top_n]:
            results['scores'].append(scores[ind])
            results['sel_ind'].append(ind)
            results['dts_ids'].append(data_to_score_ids[ind])

        return results


def train_and_run_PAE(train, test, latent_dim, num_features):
    # Train autoencoder
    autoencoder = Autoencoder(latent_dim, num_features)
    autoencoder.compile(optimizer='adam', loss=losses.MeanSquaredError())
    callback = EarlyStopping(monitor='val_loss', patience=3)
    autoencoder.fit(train, train, epochs=500, verbose=0, callbacks=[callback],
                    validation_split=0.25)

    # Train flow
    encoded_train = autoencoder.encoder(train).numpy()
    flow = NormalizingFlow(latent_dim)
    flow.compile(optimizer='adam', loss=lambda y, rv_y: -rv_y.log_prob(y))
    callback = EarlyStopping(monitor='val_loss', patience=3)
    flow.fit(np.zeros((len(encoded_train), 0)), encoded_train, epochs=500,
             verbose=0, callbacks=[callback], validation_split=0.25)

    # Calculate scores
    trained_dist = flow.dist(np.zeros(0,))
    encoded_test = autoencoder.encoder(test).numpy()
    log_probs = trained_dist.log_prob(encoded_test).numpy()
    scores = np.negative(log_probs)

    return scores


class Autoencoder(Model):
    def __init__(self, latent_dim, num_features):
        super(Autoencoder, self).__init__()

        self.encoder = keras.Sequential([
            layers.InputLayer(input_shape=(num_features,)),
            layers.Dense(latent_dim, activation='relu')
        ])

        self.decoder = keras.Sequential([
            layers.InputLayer(input_shape=(latent_dim,)),
            layers.Dense(num_features, activation='sigmoid')
        ])

    def call(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class NormalizingFlow(Model):
    def __init__(self, latent_dim):
        super(NormalizingFlow, self).__init__()

        self.dist = keras.Sequential([
            layers.InputLayer(input_shape=(0,), dtype=tf.float32),
            tfpl.DistributionLambda(
                lambda t: distributions.MultivariateNormalDiag(
                    loc=tf.zeros(tf.concat([tf.shape(t)[:-1],
                                           [latent_dim]],
                                           axis=0)))),
            tfpl.AutoregressiveTransform(bijectors.AutoregressiveNetwork(
                params=2, hidden_units=[10, 10], activation='relu')),
        ])

    def call(self, x):
        return self.dist(x)


# Copyright (c) 2021 California Institute of Technology ("Caltech").
# U.S. Government sponsorship acknowledged.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of Caltech nor its operating division, the Jet Propulsion
#   Laboratory, nor the names of its contributors may be used to endorse or
#   promote products derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
