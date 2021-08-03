# This script provides functionalities for feature extraction. See copyright
# notice at the end.
#
# Steven Lu, June 29, 2020

import numpy as np
from tqdm import tqdm
from skimage import transform
from six import add_metaclass
from abc import ABCMeta, abstractmethod
from sklearn.preprocessing import StandardScaler


EXTRACTOR_POOL = []


# Function to register a feature extractor into feature extractor pool.
def register_extractor(extractor_obj):
    if isinstance(extractor_obj, FeatureExtractor):
        EXTRACTOR_POOL.append(extractor_obj)
    else:
        raise RuntimeError('Invalid feature extractor cannot be registered in '
                           'the feature extractor pool. Valid feature '
                           'extractor must implement the base class '
                           'FeatureExtractor')


# z-score normalization
def z_score_normalize(prior_data, rank_data):
    if len(prior_data) == 0:
        raise RuntimeError('The prior data used to calculate mean and standard '
                           'deviation cannot be empty.')

    if len(rank_data) == 0:
        raise RuntimeError('The rank data to be normalized cannot be empty.')

    scaler = StandardScaler()
    scaler.fit(prior_data)
    ret_prior_data = scaler.transform(prior_data)
    ret_rank_data = scaler.transform(rank_data)

    return ret_prior_data, ret_rank_data


# Function to get the feature extractor by name
def get_feature_extractor_by_name(feature_name):
    ret_feature_extractor = None
    for feature_extractor in EXTRACTOR_POOL:
        if feature_extractor.can_extract(feature_name):
            ret_feature_extractor = feature_extractor
            break

    if ret_feature_extractor is None:
        raise RuntimeError('No feature extractor can be used for feature %s' %
                           feature_name)

    return ret_feature_extractor


def extract_feature(data_dict, features_dict):
    if data_dict is None:
        return None

    ret_features = np.empty((len(data_dict['data']), 0))

    for method_name, method_params in tqdm(features_dict.items(),
                                           desc='Feature extraction'):
        extractor = get_feature_extractor_by_name(method_name)
        features = extractor.extract(data_dict['data'], **method_params)

        ret_features = np.concatenate((ret_features, features), axis=1)

    return ret_features


@add_metaclass(ABCMeta)
class FeatureExtractor(object):
    def __init__(self, extractor_name):
        self.name = extractor_name

    def can_extract(self, feature_name):
        if feature_name.lower() == self.name.lower():
            return True
        else:
            return False

    # Sub-class must implement this function to extract features.
    # `data` must be a list of numpy arrays, and `kwargs` must be a dictionary.
    @abstractmethod
    def extract(self, data, **kwargs):
        raise RuntimeError('This function must be implemented by sub-class.')


# Feature extractor for extracting raw pixel values and then flatten the pixels
# into a vector.
class FlattenedPixelValuesExtractor(FeatureExtractor):
    def __init__(self):
        super(FlattenedPixelValuesExtractor, self).__init__(
            'flattened_pixel_values')

    def extract(self, data_cube, **kwargs):
        do_resizing = False
        if 'width' in kwargs.keys():
            width = int(kwargs['width'])
            do_resizing = True

        if 'height' in kwargs.keys():
            height = int(kwargs['height'])
            do_resizing = True

        # Get data dimension from the first item in the data cube
        if len(data_cube[0].shape) == 2:  # grayscale
            rows, cols = data_cube[0].shape
            channels = 1
        elif len(data_cube[0].shape) == 3:  # color
            rows, cols, channels = data_cube[0].shape

        if do_resizing:
            ret_features = np.zeros((len(data_cube),
                                    height * width * channels),
                                    dtype=np.uint8)
        else:
            ret_features = np.zeros((len(data_cube),
                                    rows * cols * channels),
                                    dtype=np.uint8)

        for ind, data in enumerate(data_cube):
            if do_resizing:
                ret_features[ind, :] = transform.resize(
                    data, (height, width), anti_aliasing=True,
                    preserve_range=True
                ).flatten()
            else:
                ret_features[ind, :] = data.flatten()

        return ret_features


# Register flattened pixel values extractor into the feature extractor pool
flattened_pixel_values_extractor = FlattenedPixelValuesExtractor()
register_extractor(flattened_pixel_values_extractor)


# Feature extractor for passing along the raw values.
class RawValuesExtractor(FeatureExtractor):
    def __init__(self):
        super(RawValuesExtractor, self).__init__(
            'raw_values')

    def extract(self, data_cube, **kwargs):
        return np.array(data_cube)


# Register flattened pixel values extractor into the feature extractor pool
raw_values_extractor = RawValuesExtractor()
register_extractor(raw_values_extractor)


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
