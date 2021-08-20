# This script implements a convolutional probabilistic autoencoder, drawing on
# descriptions from the following papers:
# Böhm, Vanessa, and Uroš Seljak. “Probabilistic Auto-Encoder.”
# ArXiv:2006.05479 [Cs, Stat], Oct. 2020.
# Prochaska, J. Xavier, Peter C Cornillon, and David M Reiman. "Deep Learning of
# Sea Surface Temperature Patterns to Identify Ocean Extremes." Remote Sensing,
# v. 13,.4 doi: 10.3390/rs13040744
#
# See copyright notice at end.
#
# Author: Bryce Dubayah
# Date created: August 16, 2021

from dora_exp_pipeline.outlier_detection import OutlierDetection
import os
import math
import numpy as np
from PIL import Image
from itertools import accumulate
from copy import deepcopy
import tensorflow as tf
import tensorflow_addons as tfa
from tensorflow import keras
from tensorflow.keras import layers, losses
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow_probability import distributions, bijectors, layers as tfpl


class ConvPAEOutlierDetection(OutlierDetection):
    def __init__(self):
        super(ConvPAEOutlierDetection, self).__init__('conv_pae')

    def _rank_internal(self, data_to_fit, data_to_score, data_to_score_ids,
                       top_n, seed, latent_dim, max_epochs=1000, patience=10,
                       val_split=0.25, verbose=0, optimizer='adam'):
        if data_to_fit is None:
            data_to_fit = deepcopy(data_to_score)

        if latent_dim < 1:
            raise RuntimeError('The dimensionality of the latent space must be '
                               '>= 1')

        # Check if directory of images was passed in
        if not is_list_of_images(data_to_fit):
            raise RuntimeError('The convolutional PAE must be used with the'
                               'Imagedir data loader')

        # Check that the number of hidden layers <= number of features
        image_shape = get_image_dimensions(data_to_fit)
        num_features = np.prod(image_shape)
        if latent_dim > num_features:
            raise RuntimeError(f'The dimensionality of the latent space'
                               f'(latent_dim = {latent_dim}) '
                               f'must be <= number of features '
                               f'({num_features})')

        # Set tensorflow logging level
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' if verbose == 0 else '0'

        # Set seed
        tf.random.set_seed(seed)

        # Rank targets
        scores = train_and_run_conv_PAE(data_to_fit, data_to_score, latent_dim,
                                        image_shape, seed, max_epochs, patience,
                                        val_split, verbose, optimizer)
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


def train_and_run_conv_PAE(train, test, latent_dim, image_shape, seed,
                           max_epochs, patience, val_split, verbose, optimizer):
    # Make tensorflow datasets
    channels = image_shape[2]
    train_ds, val_ds, test_ds = get_train_val_test(train, test, seed, channels,
                                                   val_split)

    # Progress bar formatting
    autoencoder_lbar = 'Autoencoder training: {percentage:3.0f}%|{bar} '
    flow_lbar = 'Flow training: {percentage:3.0f}%|{bar} '
    rbar = '{n_fmt}/{total_fmt} ETA: {remaining}s,  {rate_fmt}{postfix}'

    # Initialize callbacks
    autoencoder_callbacks = [
        EarlyStopping(monitor='val_loss', patience=patience),
        tfa.callbacks.TQDMProgressBar(
            show_epoch_progress=False,
            overall_bar_format=autoencoder_lbar + rbar
        )]

    flow_callbacks = [
        EarlyStopping(monitor='val_loss', patience=patience),
        tfa.callbacks.TQDMProgressBar(
            show_epoch_progress=False,
            overall_bar_format=flow_lbar + rbar
        )]

    # Train autoencoder
    autoencoder = ConvAutoencoder(latent_dim, image_shape)
    autoencoder.compile(optimizer=optimizer, loss=losses.MeanSquaredError())
    autoencoder.fit(x=train_ds, validation_data=val_ds, verbose=verbose,
                    epochs=max_epochs, callbacks=autoencoder_callbacks)

    # Encode datasets
    enc_train = autoencoder.encoder.predict(train_ds)
    enc_val = autoencoder.encoder.predict(val_ds)
    encoded_train = np.append(enc_train, enc_val, axis=0)

    # Train flow
    flow = NormalizingFlow(latent_dim)
    flow.compile(optimizer=optimizer, loss=lambda y, rv_y: -rv_y.log_prob(y))
    flow.fit(np.zeros((len(encoded_train), 0)), encoded_train,
             verbose=verbose, epochs=max_epochs, callbacks=flow_callbacks,
             validation_split=val_split)

    # Calculate scores
    trained_dist = flow.dist(np.zeros(0,))
    encoded_test = autoencoder.encoder.predict(test_ds)
    log_probs = trained_dist.log_prob(encoded_test)
    scores = np.negative(log_probs)

    return scores


def is_list_of_images(data):
    fit_elem = data[0][0]
    supported_exts = tuple(['.jpg', '.png', '.bmp', '.gif'])
    return isinstance(fit_elem, str) and fit_elem.endswith(supported_exts)


def get_image_dimensions(data):
    fit_elem = data[0][0]
    im_pil = Image.open(fit_elem)
    im_data = np.array(im_pil)
    im_pil.close()
    image_shape = im_data.shape
    if len(image_shape) < 3:  # Add channel dimension to grayscale images
        image_shape += (1,)
    return image_shape


def get_train_val_test(train_images, test_images, seed, channels, val_split):
    # Make training and validation sets
    fit_ds = make_tensorlow_dataset(train_images, channels)
    test_ds = make_tensorlow_dataset(test_images, channels)
    fit_ds = fit_ds.shuffle(len(train_images), seed=seed,
                            reshuffle_each_iteration=True)
    val_size = int(len(train_images) * val_split)
    train_ds = fit_ds.skip(val_size)
    val_ds = fit_ds.take(val_size)

    train_ds = configure_for_performance(train_ds)
    val_ds = configure_for_performance(val_ds)
    test_ds = configure_for_performance(test_ds)

    return train_ds, val_ds, test_ds


def make_tensorlow_dataset(image_list, channels):
    elem = image_list[0][0]
    images_dir = os.path.split(elem)[0]
    ext = os.path.splitext(elem)[1]
    ds = tf.data.Dataset.list_files(images_dir + '/*' + ext, shuffle=False)
    ds = ds.map(lambda x: process_path(x, channels),
                num_parallel_calls=tf.data.AUTOTUNE)
    return ds


def process_path(file_path, channels):
    img = tf.io.read_file(file_path)
    img = tf.io.decode_image(img, channels=channels)
    return img, img


def configure_for_performance(ds):
    ds = ds.cache()
    ds = ds.batch(32)
    ds = ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    return ds


class ConvAutoencoder(Model):
    def __init__(self, latent_dim, input_shape):
        super(ConvAutoencoder, self).__init__()

        self._height = input_shape[0]
        self._width = input_shape[1]
        self._channels = input_shape[2]

        self._encoder_layers = [
            layers.InputLayer(input_shape=input_shape),
            layers.experimental.preprocessing.Rescaling(1./255)
        ]
        self._decoder_layers = [
            layers.InputLayer(input_shape=(latent_dim,))
        ]

        # Calculate # of convolution layers and final dimensions before
        # dense layer
        num_conv_layers = math.ceil(math.log2(input_shape[0])) - 2

        # Target width/height and channels after convolution layers
        layer_sizes = list(accumulate(
            range(num_conv_layers),
            lambda curr_dim, _: math.ceil(curr_dim/2),
            initial=self._width
        ))
        target_width = layer_sizes[-1]
        target_shape = (target_width, target_width,
                        32*2**(num_conv_layers - 1))

        # Convolution layers for encoder
        for i in range(num_conv_layers):
            self._encoder_layers.append(
                layers.Conv2D(
                    filters=32*2**i,
                    kernel_size=3,
                    strides=2,
                    padding='same',
                    activation='relu'))

        # Flatten and map to latent dim
        self._encoder_layers.extend([
            layers.Flatten(),
            layers.Dense(latent_dim)
        ])

        # Add dense layer to map back from latent dim, then reshape to 2D
        self._decoder_layers.extend([
            layers.Dense(units=np.prod(target_shape), activation='relu'),
            layers.Reshape(target_shape=target_shape)
        ])

        # Convolution layers for decoder
        for i in range(num_conv_layers):
            self._decoder_layers.append(
                layers.Conv2DTranspose(
                    filters=32*2**(num_conv_layers - i - 1),
                    kernel_size=3,
                    strides=2,
                    output_padding=(
                        0 if layer_sizes[-1-i-1] % 2 != 0 else None
                    ),  # Don't pad output if next layer is odd
                    padding='same',
                    activation='relu'))

        # Final decoder layer to map back to input channels
        self._decoder_layers.extend([
            layers.Conv2DTranspose(
                filters=self._channels,
                kernel_size=3,
                strides=1,
                padding='same'),
            layers.experimental.preprocessing.Rescaling(255)
        ])

        self.encoder = keras.Sequential(self._encoder_layers)
        self.decoder = keras.Sequential(self._decoder_layers)

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
