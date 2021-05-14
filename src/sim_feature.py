# This script provides functionalities for feature extraction. See copyright
# notice at the end.
#
# Steven Lu, June 29, 2020

import os
import numpy as np
from scipy.stats import skew
from scipy.stats import kurtosis
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


def extract_1d_features(im_data, attributes, features_1d):
    ret_features = dict()
    ret_features.setdefault('name', [])
    ret_features.setdefault('value', [])

    for feature_name, feature_param in features_1d.items():
        extractor = get_feature_extractor_by_name(feature_name)
        feature_param['attributes'] = attributes
        feature = extractor.extract(im_data, **feature_param)

        if isinstance(feature.value, (list, np.ndarray)):
            for ind, value in enumerate(feature.value):
                ret_features['name'].append('%s%d' % (feature.name, ind))
                ret_features['value'].append(value)
        else:
            ret_features['name'].append(feature.name)
            ret_features['value'].append(feature.value)

    return ret_features


def extract_2d_features(im_data, attributes, features_2d):
    ret_features = dict()

    for feature_name, feature_param in features_2d.items():
        extractor = get_feature_extractor_by_name(feature_name)
        feature_param['attributes'] = attributes
        feature = extractor.extract(im_data, **feature_param)

        if not isinstance(feature.value, np.ndarray):
            raise RuntimeError('Error in feature extractor %s. For 2d feature '
                               'extractors, only numpy array is accepted.' %
                               feature_name)

        ret_features['name'] = feature.name
        ret_features['value'] = feature.value

    return ret_features


class Feature(object):
    def __init__(self, name, value):
        # This can be a string or a 1d list of string values
        self.name = name

        # This can be a scalar or a 1d list of scalar values
        self.value = value


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
    # `im_data must` be a 2d numpy array, and `kwargs` must be a 2d dictionary.
    @abstractmethod
    def extract(self, im_data, **kwargs):
        raise RuntimeError('This function must be implemented by sub-class.')


# Feature extractor for extracting raw pixel values and then flatten the pixels
# into a vector.
class FlattenedPixelValuesExtractor(FeatureExtractor):
    """
    >>> fpf = FlattenedPixelValuesExtractor()
    >>> f = fpf.extract(imzero)
    >>> f.value
    array([0, 0, 0, 0], dtype=uint8)
    >>> f = fpf.extract(imcheck)
    >>> f.value
    array([  0, 255, 255,   0], dtype=uint8)
    >>> f = fpf.extract(imzero_rgb)
    >>> f.value
    array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=uint8)
    >>> f = fpf.extract(imcheck_rgb)
    >>> f.value
    array([  0, 255, 255,   0,   0, 255, 255,   0,   0, 255, 255,   0],
          dtype=uint8)
    >>> f = fpf.extract(immulti)
    >>> f.value
    array([  0, 255, 255,   0,   0, 255, 255,   0,   0, 255, 255,   0,   0,
           255, 255,   0], dtype=uint8)
    """
    def __init__(self):
        super(FlattenedPixelValuesExtractor, self).__init__('flattened_pixel_values')

    def extract(self, im_data, **kwargs):
        dimension = im_data.shape
        height = dimension[0]
        width = dimension[1]
        band = None

        do_multi_bands = False
        if len(dimension) > 2:
            do_multi_bands = True
            band = dimension[2]

        do_resizing = False
        if 'width' in kwargs.keys():
            width = int(kwargs['width'])
            do_resizing = True

        if 'height' in kwargs.keys():
            height = int(kwargs['height'])
            do_resizing = True

        ret_data = im_data
        if do_resizing:
            # Note - the resize function preserves the number of bands, so
            # there is no need to specify the number of bands in (height, width)
            # tuple.
            ret_data = transform.resize(
                im_data, (height, width), anti_aliasing=True,
                preserve_range=True
            )

        if do_multi_bands:
            flattened_data = list()
            for b in range(band):
                flattened_data.extend(ret_data[:, :, b].flatten().tolist())

            ret_data = np.array(flattened_data)
        else:
            ret_data = ret_data.flatten()

        return Feature('flattened_pixel', ret_data.astype(np.uint8))


# Register flattened pixel values extractor into the feature extractor pool
flattened_pixel_values_extractor = FlattenedPixelValuesExtractor()
register_extractor(flattened_pixel_values_extractor)


# Use raw pixel values as features. The image's original dimensionality with be
# preserved.
class RawPixelValuesExtractor(FeatureExtractor):
    """
    >>> rpf = RawPixelValuesExtractor()
    >>> f = rpf.extract(imzero)
    >>> f.value
    array([[0, 0],
           [0, 0]], dtype=uint8)
    >>> f = rpf.extract(imzero, width=2, height=2)
    >>> f.value
    array([[0, 0],
           [0, 0]], dtype=uint8)
    >>> f = rpf.extract(imcheck)
    >>> f.value
    array([[  0, 255],
           [255,   0]], dtype=uint8)
    >>> f = rpf.extract(imcheck, width=2, height=2)
    >>> f.value
    array([[  0, 254],
           [254,   0]], dtype=uint8)
    >>> f = rpf.extract(imzero_rgb)
    >>> f.value
    array([[[0, 0, 0],
            [0, 0, 0]],
    <BLANKLINE>
           [[0, 0, 0],
            [0, 0, 0]]], dtype=uint8)
    >>> f = rpf.extract(imzero_rgb, width=2, height=2)
    >>> f.value
    array([[[0, 0, 0],
            [0, 0, 0]],
    <BLANKLINE>
           [[0, 0, 0],
            [0, 0, 0]]], dtype=uint8)
    >>> f = rpf.extract(imcheck_rgb)
    >>> f.value
    array([[[  0,   0,   0],
            [255, 255, 255]],
    <BLANKLINE>
           [[255, 255, 255],
            [  0,   0,   0]]], dtype=uint8)
    >>> f = rpf.extract(imcheck_rgb, width=2, height=2)
    >>> f.value
    array([[[  0,   0,   0],
            [254, 254, 254]],
    <BLANKLINE>
           [[254, 254, 254],
            [  0,   0,   0]]], dtype=uint8)
    >>> f = rpf.extract(immulti)
    >>> f.value
    array([[[  0,   0,   0,   0],
            [255, 255, 255, 255]],
    <BLANKLINE>
           [[255, 255, 255, 255],
            [  0,   0,   0,   0]]], dtype=uint8)
    >>> f = rpf.extract(immulti, width=2, height=2)
    >>> f.value
    array([[[  0,   0,   0,   0],
            [254, 254, 254, 254]],
    <BLANKLINE>
           [[254, 254, 254, 254],
            [  0,   0,   0,   0]]], dtype=uint8)
    """
    def __init__(self):
        super(RawPixelValuesExtractor, self).__init__('raw_pixel_values')

    def extract(self, im_data, **kwargs):
        dimension = im_data.shape
        height = dimension[0]
        width = dimension[1]

        do_resizing = False
        if 'width' in kwargs.keys():
            width = int(kwargs['width'])
            do_resizing = True

        if 'height' in kwargs.keys():
            height = int(kwargs['height'])
            do_resizing = True

        ret_data = im_data
        if do_resizing:
            ret_data = transform.resize(
                im_data, (height, width), anti_aliasing=True,
                preserve_range=True
            )

        return Feature('raw_pixel', ret_data.astype(np.uint8))


# Register raw pixel values extractor into the feature extractor pool
raw_pixel_values_extractor = RawPixelValuesExtractor()
register_extractor(raw_pixel_values_extractor)


# Feature extractor to extract the mean value
class MeanExtractor(FeatureExtractor):
    """
    >>> mf = MeanExtractor()
    >>> f = mf.extract(imzero)
    >>> f.value
    0.0
    >>> f = mf.extract(imcheck)
    >>> f.value
    127.5
    >>> f = mf.extract(imzero_rgb)
    >>> f.value
    array([0., 0., 0.], dtype=float32)
    >>> f = mf.extract(imcheck_rgb)
    >>> f.value
    array([127.5, 127.5, 127.5], dtype=float32)
    >>> f = mf.extract(immulti)
    >>> f.value
    array([127.5, 127.5, 127.5, 127.5], dtype=float32)
    """
    def __init__(self):
        super(MeanExtractor, self).__init__('mean')

    def extract(self, im_data, **kwargs):
        dimension = im_data.shape
        if len(dimension) > 2:
            mean_list = []
            for b in range(dimension[2]):
                single_band_data = im_data[:, :, b].flatten()
                mean_list.append(np.mean(single_band_data))

            return Feature('mean', np.array(mean_list, dtype=np.float32))
        else:
            flattened_im_data = im_data.flatten()

            return Feature('mean', float(np.mean(flattened_im_data)))


# Register mean extractor into the feature extractor pool
mean_extractor = MeanExtractor()
register_extractor(mean_extractor)


# Feature extractor to extract standard deviation
class StdExtractor(FeatureExtractor):
    """
    >>> sf = StdExtractor()
    >>> f = sf.extract(imzero)
    >>> f.value
    0.0
    >>> f = sf.extract(imcheck)
    >>> f.value
    127.5
    >>> f = sf.extract(imzero_rgb)
    >>> f.value
    array([0., 0., 0.], dtype=float32)
    >>> f = sf.extract(imcheck_rgb)
    >>> f.value
    array([127.5, 127.5, 127.5], dtype=float32)
    >>> f = sf.extract(immulti)
    >>> f.value
    array([127.5, 127.5, 127.5, 127.5], dtype=float32)
    """
    def __init__(self):
        super(StdExtractor, self).__init__('std')

    def extract(self, im_data, **kwargs):
        dimension = im_data.shape
        if len(dimension) > 2:
            std_list = []
            for b in range(dimension[2]):
                single_band_data = im_data[:, :, b].flatten()
                std_list.append(np.std(single_band_data, ddof=0))

            return Feature('std', np.array(std_list, dtype=np.float32))
        else:
            flattened_im_data = im_data.flatten()

            return Feature('std', float(np.std(flattened_im_data, ddof=0)))


# Register std extractor into the feature extractor pool
std_extractor = StdExtractor()
register_extractor(std_extractor)


# Feature extractor to extract median value
class MedianExtractor(FeatureExtractor):
    """
    >>> mf = MedianExtractor()
    >>> f = mf.extract(imzero)
    >>> f.value
    0.0
    >>> f = mf.extract(imcheck)
    >>> f.value
    127.5
    >>> f = mf.extract(imzero_rgb)
    >>> f.value
    array([0., 0., 0.], dtype=float32)
    >>> f = mf.extract(imcheck_rgb)
    >>> f.value
    array([127.5, 127.5, 127.5], dtype=float32)
    >>> f = mf.extract(immulti)
    >>> f.value
    array([127.5, 127.5, 127.5, 127.5], dtype=float32)
    """
    def __init__(self):
        super(MedianExtractor, self).__init__('median')

    def extract(self, im_data, **kwargs):
        dimension = im_data.shape
        if len(dimension) > 2:
            median_list = []
            for b in range(dimension[2]):
                single_band_data = im_data[:, :, b].flatten()
                median_list.append(np.median(single_band_data))

            return Feature('median', np.array(median_list, dtype=np.float32))
        else:
            flattened_im_data = im_data.flatten()

            return Feature('median', float(np.median(flattened_im_data)))


# Register median extractor into the feature extractor pool
median_extractor = MedianExtractor()
register_extractor(median_extractor)


# Feature extractor to compute the skewness of a data set
class SkewExtractor(FeatureExtractor):
    """
    >>> sf = SkewExtractor()
    >>> f = sf.extract(imzero)
    >>> f.value
    0.0
    >>> f = sf.extract(imcheck)
    >>> f.value
    0.0
    >>> f = sf.extract(imzero_rgb)
    >>> f.value
    array([0., 0., 0.], dtype=float32)
    >>> f = sf.extract(imcheck_rgb)
    >>> f.value
    array([0., 0., 0.], dtype=float32)
    >>> f = sf.extract(immulti)
    >>> f.value
    array([0., 0., 0., 0.], dtype=float32)
    """
    def __init__(self):
        super(SkewExtractor, self).__init__('skew')

    def extract(self, im_data, **kwargs):
        dimension = im_data.shape
        if len(dimension) > 2:
            skew_list = []
            for b in range(dimension[2]):
                single_band_data = im_data[:, :, b].flatten()
                skew_list.append(skew(single_band_data))

            return Feature('skew', np.array(skew_list, dtype=np.float32))
        else:
            flattened_im_data = im_data.flatten()

            return Feature('skew', float(skew(flattened_im_data)))


# Register skew extractor into the feature extractor pool
skew_extractor = SkewExtractor()
register_extractor(skew_extractor)


# Feature extractor to compute the kurtosis of a data set
class KurtosisExtractor(FeatureExtractor):
    """
    >>> kf = KurtosisExtractor()
    >>> f = kf.extract(imzero)
    >>> f.value
    -3.0
    >>> f = kf.extract(imcheck)
    >>> f.value
    -2.0
    >>> f = kf.extract(imzero_rgb)
    >>> f.value
    array([-3., -3., -3.], dtype=float32)
    >>> f = kf.extract(imcheck_rgb)
    >>> f.value
    array([-2., -2., -2.], dtype=float32)
    >>> f = kf.extract(immulti)
    >>> f.value
    array([-2., -2., -2., -2.], dtype=float32)
    """
    def __init__(self):
        super(KurtosisExtractor, self).__init__('kurtosis')

    def extract(self, im_data, **kwargs):
        dimension = im_data.shape
        if len(dimension) > 2:
            kurtosis_list = []
            for b in range(dimension[2]):
                single_band_data = im_data[:, :, b].flatten()
                kurtosis_list.append(kurtosis(single_band_data))

            return Feature('Kurtosis', np.array(kurtosis_list, dtype=np.float32))
        else:
            flattened_im_data = im_data.flatten()

            return Feature('kurtosis', float(kurtosis(flattened_im_data)))


# Register kurtosis extractor into the feature extractor pool
kurtosis_extractor = KurtosisExtractor()
register_extractor(kurtosis_extractor)


# Feature extractor to compute the min value of a data set
class MinExtractor(FeatureExtractor):
    """
    >>> mf = MinExtractor()
    >>> f = mf.extract(imzero)
    >>> f.value
    0.0
    >>> f = mf.extract(imcheck)
    >>> f.value
    0.0
    >>> f = mf.extract(imzero_rgb)
    >>> f.value
    array([0., 0., 0.], dtype=float32)
    >>> f = mf.extract(imcheck_rgb)
    >>> f.value
    array([0., 0., 0.], dtype=float32)
    >>> f = mf.extract(immulti)
    >>> f.value
    array([0., 0., 0., 0.], dtype=float32)
    """
    def __init__(self):
        super(MinExtractor, self).__init__('min')

    def extract(self, im_data, **kwargs):
        dimension = im_data.shape
        if len(dimension) > 2:
            min_list = []
            for b in range(dimension[2]):
                single_band_data = im_data[:, :, b].flatten()
                min_list.append(np.amin(single_band_data))

            return Feature('min', np.array(min_list, dtype=np.float32))
        else:
            flattened_im_data = im_data.flatten()

            return Feature('min', float(np.amin(flattened_im_data)))


# Register min extractor into the feature extractor pool
min_extractor = MinExtractor()
register_extractor(min_extractor)


# Feature extractor to compute the max value of a data set
class MaxExtractor(FeatureExtractor):
    """
    >>> mf = MaxExtractor()
    >>> f = mf.extract(imzero)
    >>> f.value
    0.0
    >>> f = mf.extract(imcheck)
    >>> f.value
    255.0
    >>> f = mf.extract(imzero_rgb)
    >>> f.value
    array([0., 0., 0.], dtype=float32)
    >>> f = mf.extract(imcheck_rgb)
    >>> f.value
    array([255., 255., 255.], dtype=float32)
    >>> f = mf.extract(immulti)
    >>> f.value
    array([255., 255., 255., 255.], dtype=float32)
    """
    def __init__(self):
        super(MaxExtractor, self).__init__('max')

    def extract(self, im_data, **kwargs):
        dimension = im_data.shape
        if len(dimension) > 2:
            max_list = []
            for b in range(dimension[2]):
                single_band_data = im_data[:, :, b].flatten()
                max_list.append(np.amax(single_band_data))

            return Feature('max', np.array(max_list, dtype=np.float32))
        else:
            flattened_im_data = im_data.flatten()

            return Feature('max', float(np.amax(flattened_im_data)))


# Register max extractor into the feature extractor pool
max_register = MaxExtractor()
register_extractor(max_register)


# Feature extractor to extract aegis features using saved json file
class AegisExtractor(FeatureExtractor):
    """
    >>> ae = AegisExtractor()
    >>> attributes = {
    ...     "area": 1051.0,
    ...     "dist_from_rmi": 3.618575096130371,
    ...     "dist_from_rover": 4.030208110809326,
    ...     "eccentricity": 0.7630206942558289,
    ...     "ellipse_cx": 324.038330078125,
    ...     "ellipse_cy": 145.1396026611328,
    ...     "ellipse_semimajor": 23.23233985900879,
    ...     "ellipse_semiminor": 15.0167818069458,
    ...     "inscribed_cx": 320.0,
    ...     "inscribed_cy": 160.0,
    ...     "inscribed_dist": 10.0,
    ...     "intensity_mean": 50.65081024169922,
    ...     "intensity_std": 24.144956588745117,
    ...     "orientation": -1.0333062410354614,
    ...     "perimeter": 327.0,
    ...     "ruggedness": 0.6485540270805359,
    ...     "site_x": 8.203387260437012,
    ...     "site_y": -13.021047592163086,
    ...     "site_z": -0.056236401200294495,
    ...     "size_3d": 0.008180571720004082
    ... }
    >>> complete_feature_names = ['area', 'dist_from_rmi', 'dist_from_rover',
    ...        'eccentricity', 'ellipse_cx', 'ellipse_cy', 'ellipse_semimajor',
    ...        'ellipse_semiminor', 'inscribed_cx', 'inscribed_cy',
    ...        'inscribed_dist', 'intensity_mean', 'intensity_std',
    ...        'orientation', 'perimeter', 'ruggedness', 'site_x', 'site_y',
    ...        'site_z', 'size_3d']
    >>> f = ae.extract(imzero, **{'attributes': attributes,
    ...                           'feature_names': complete_feature_names})
    >>> f.value
    [1051.0, 3.618575096130371, 4.030208110809326, 0.7630206942558289, \
324.038330078125, 145.1396026611328, 23.23233985900879, 15.0167818069458, \
320.0, 160.0, 10.0, 50.65081024169922, 24.144956588745117, \
-1.0333062410354614, 327.0, 0.6485540270805359, 8.203387260437012, \
-13.021047592163086, -0.056236401200294495, 0.008180571720004082]
    >>> f = ae.extract(imzero_rgb, **{'attributes': attributes,
    ...                               'feature_names': complete_feature_names})
    >>> f.value
    [1051.0, 3.618575096130371, 4.030208110809326, 0.7630206942558289, \
324.038330078125, 145.1396026611328, 23.23233985900879, 15.0167818069458, \
320.0, 160.0, 10.0, 50.65081024169922, 24.144956588745117, \
-1.0333062410354614, 327.0, 0.6485540270805359, 8.203387260437012, \
-13.021047592163086, -0.056236401200294495, 0.008180571720004082]
    >>> selective_feature_names = ['area', 'orientation', 'ruggedness']
    >>> f = ae.extract(imzero, **{'attributes': attributes,
    ...                           'feature_names': selective_feature_names})
    >>> f.value
    [1051.0, -1.0333062410354614, 0.6485540270805359]
    >>> f = ae.extract(imzero_rgb, **{'attributes': attributes,
    ...                               'feature_names': selective_feature_names})
    >>> f.value
    [1051.0, -1.0333062410354614, 0.6485540270805359]
    >>> invalid_feature_names = ['steven']
    >>> f = ae.extract(imzero, **{'attributes': attributes,
    ...                           'feature_names': invalid_feature_names})
    Traceback (most recent call last):
    RuntimeError: Invalid AEGIS feature name. Verify the aegis feature in the config file.
    """
    def __init__(self):
        super(AegisExtractor, self).__init__('aegis')

    def extract(self, im_data, **kwargs):
        attributes = kwargs['attributes']
        feature_names = kwargs['feature_names']
        feature_values = []

        for fn in feature_names:
            if fn not in attributes.keys():
                raise RuntimeError('Invalid AEGIS feature name. Verify the '
                                   'aegis feature in the config file.')

            feature_values.append(attributes[fn])

        return Feature('aegis_feature', feature_values)


# Register AEGIS extractor into the feature extractor pool
aegis_extractor = AegisExtractor()
register_extractor(aegis_extractor)


# Define main entry point to run doctests
if __name__ == "__main__":
    import doctest

    (num_failed, num_tests) = doctest.testmod(
        # extraglobs define global variables that all doctests can use,
        # to avoid redefining them in each test block
        extraglobs={
            # all-zeros 2x2 image
            'imzero': np.array([[0, 0], [0, 0]]),

            # 'checkerboard' 2x2 image
            'imcheck': np.array([[0, 255], [255, 0]]),

            # all-zeros 2x2x3 image
            'imzero_rgb': np.array([[[0, 0, 0], [0, 0, 0]],
                                    [[0, 0, 0], [0, 0, 0]]]),

            # 'checkboard' 2x2x3 image
            'imcheck_rgb': np.array([[[0, 0, 0], [255, 255, 255]],
                                     [[255, 255, 255], [0, 0, 0]]]),
            # multispectral 2x2x4 image
            'immulti': np.array([[[0, 0, 0, 0], [255, 255, 255, 255]],
                                 [[255, 255, 255, 255], [0, 0, 0, 0]]])
        })

    filename = os.path.basename(__file__)

    if num_failed == 0:
        print("%-20s All %3d tests passed!" % (filename, num_tests))
    # Doctest itself prints a message if any tests failed


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
