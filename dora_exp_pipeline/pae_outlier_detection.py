from dora_exp_pipeline.outlier_detection import OutlierDetection
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, losses
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow_probability import distributions, bijectors, layers as tfpl
from sklearn.model_selection import train_test_split


class PAEOutlierDetection(OutlierDetection):
    def __init__(self):
        super(PAEOutlierDetection, self).__init__('pae')

    def _rank_internal(self, data_to_fit, data_to_score, seed,
                                latent_dim):
        if latent_dim < 1:
            raise RuntimeError('The dimensionality of the latent space must be '
                               '>= 1')

        # Check that the number of hidden layers <= number of features
        if latent_dim > data_to_fit.shape[1]:
            raise RuntimeError(f'The dimensionality of the latent space'
                               f'(latent_dim = {latent_dim}) '
                               f'must be <= number of features '
                               f'({data_to_fit.shape[1]})')

        # Rank targets
        return train_and_run_PAE(data_to_fit, data_to_score, latent_dim)


def train_and_run_PAE(train, test, latent_dim):
    # Train autoencoder
    autoencoder = Autoencoder(latent_dim, train.shape[1])
    autoencoder.compile(optimizer='adam', loss=losses.MeanSquaredError())
    callback = EarlyStopping(monitor='val_loss', patience=3) 
    autoencoder.fit(
        train, 
        train, 
        epochs=500, 
        callbacks=[callback],
        validation_split=0.25,
        shuffle=True
    )

    # Train flow
    encoded_train = autoencoder.encoder(train).numpy()
    flow = NormalizingFlow(latent_dim)
    flow.compile(optimizer='adam', loss=lambda y, rv_y: -rv_y.log_prob(y))
    callback = EarlyStopping(monitor='val_loss', patience=3) 
    flow.fit(
        np.zeros((len(encoded_train), 0)), 
        encoded_train, 
        epochs=500,
        callbacks=[callback],
        validation_split=0.25,
        shuffle=True
    )

    # Calculate scores
    trained_dist = flow.dist(np.zeros(0,))
    encoded_test = autoencoder.encoder(test).numpy()
    log_probs = trained_dist.log_prob(encoded_test).numpy()
    novelty_scores = np.negative(log_probs)
    
    return novelty_scores


class Autoencoder(Model):
    def __init__(self, latent_dim, input_dim):
        super(Autoencoder, self).__init__()
        self.encoder = keras.Sequential(
            [
                layers.Dense(latent_dim, activation='relu')
            ]
        )
        self.decoder = keras.Sequential(
            [
                layers.Dense(input_dim, activation='sigmoid')
            ]
        )

    def call(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class NormalizingFlow(Model):
    def __init__(self, latent_dim):
        super(NormalizingFlow, self).__init__()
        self.dist = keras.Sequential(
            [
                layers.InputLayer(input_shape=(0,), dtype=tf.float32),
                tfpl.DistributionLambda(lambda t: 
                    distributions.MultivariateNormalDiag(
                        loc=tf.zeros(tf.concat(
                            [tf.shape(t)[:-1], [latent_dim]], axis=0)))),
                tfpl.AutoregressiveTransform(bijectors.AutoregressiveNetwork(
                    params=2, hidden_units=[10, 10], activation='relu')), 
            ]
        )
    
    def call(self, x):
        return self.dist(x)
