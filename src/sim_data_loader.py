# This script provides functionalities to load data. See copyright notice at
# the end.
#
# Steven Lu, June 29, 2019

import os
import numpy as np
from PIL import Image
from six import add_metaclass
from planetaryimage import PDS3Image
from abc import ABCMeta, abstractmethod


# The pool of data loaders. Data loaders can be registered into this pool using
# register_data_loader() function.
LOADER_POOL = []


# Function to get the data loader by data type
def get_data_loader_by_name(loader_name):
    ret_data_loader = None
    for data_loader in LOADER_POOL:
        if data_loader.can_load(loader_name):
            ret_data_loader = data_loader
            break

    if ret_data_loader is None:
        raise RuntimeError('No data loader can be used for the data type '
                           'specified in the configuration file: %s' %
                           loader_name)

    return ret_data_loader


# Get the min/max x/y coordinates for a aegis target
def get_cropping_coords(aegis_target):
    trace = aegis_target['trace']

    min_x = min([x for (x, y) in trace])
    max_x = max([x for (x, y) in trace])
    min_y = min([y for (x, y) in trace])
    max_y = max([y for (x, y) in trace])

    return min_x, max_x, min_y, max_y


def im_crop(im_data, aegis_target, crop_shape, min_crop_area):
    min_x, max_x, min_y, max_y = get_cropping_coords(aegis_target)
    if (max_x - min_x) * (max_y - min_y) < min_crop_area:
        return None

    if crop_shape == 'square':
        return square_crop(im_data, min_x, max_x, min_y, max_y)
    else:
        return rectangle_crop(im_data, min_x, max_x, min_y, max_y)


# Function to crop out a rectangle from an image. This function will return
# None if the area of the cropped out region is smaller than `min_crop_area`.
# Note this function currently relies on the `trace` attributes in the aegis
# file.
def rectangle_crop(im_data, min_x, max_x, min_y, max_y):
    if len(im_data.shape) > 2:
        rectangle_data = im_data[min_y: max_y, min_x: max_x, :]
    else:
        rectangle_data = im_data[min_y: max_y, min_x: max_x]

    return rectangle_data


# Function to crop out a square from an image. This function will return
# None if the area of the cropped out region is smaller than `min_crop_area`.
# Note this function currently relies on the `trace` attributes in the aegis
# file.
def square_crop(im_data, min_x, max_x, min_y, max_y):
    dimension = im_data.shape
    im_width = dimension[0]
    im_height = dimension[1]
    w = (max_x - min_x) // 2
    h = (max_y - min_y) // 2
    cw = min_x + w
    ch = min_y + h
    side = max(w, h)

    # Check if square boundaries exceed image boundaries, and shift the center
    # coordinates if they do.
    if (cw - side) < 0:
        cw = cw + np.abs(0 - cw - side)
    elif (cw + side) > im_width:
        cw = cw - ((cw + side) - im_width)

    if (ch - side) < 0:
        ch = ch + np.abs(0 - ch - side)
    elif (ch + side) > im_height:
        ch = ch - ((ch + side) - im_height)

    square_data = im_data[ch - side: ch + side, cw - side: cw + side]

    return square_data


# Function to register a data loader object into the data loader pool.
# Note only valid data loader object can be registered. Valid data loader
# objects are the ones that implement the base class DataLoader.
def register_data_loader(data_loader):
    if isinstance(data_loader, DataLoader):
        LOADER_POOL.append(data_loader)
    else:
        raise RuntimeError('Invalid data loader cannot be registered in the '
                           'data loader pool. Valid data loader must implement'
                           'the base class DataLoader')


@add_metaclass(ABCMeta)
class DataLoader(object):
    def __init__(self, loader_name):
        self.loader_name = loader_name

    def can_load(self, loader_name):
        if loader_name.lower() == self.loader_name.lower():
            return True
        else:
            return False

    def load(self, file_path):
        im_data = self._load(file_path)

        # TODO: returned data should be verified. Depth (8-bit)? Dimensionality?
        return im_data

    @abstractmethod
    def _load(self, file_path):
        raise RuntimeError('Development error. This function should never be '
                           'called directly.')


class MSLNavcamEDRLoader(DataLoader):
    def __init__(self):
        super(MSLNavcamEDRLoader, self).__init__('navcam')

    def _load(self, file_path):
        if not os.path.exists(file_path):
            raise RuntimeError('File %s not found.' % os.path.abspath(file_path))

        try:
            im = PDS3Image.open(file_path)
        except:
            raise RuntimeError('Failed loading image %s using planetaryimage '
                               'package' % os.path.abspath(file_path))

        if im is None:
            raise RuntimeError('planetaryimage error. Failed loading image %s' %
                               os.path.abspath(file_path))

        # Convert from 12-bit to 8-bit
        im_data = np.uint8(np.floor(im.image * (255.0 / 4095.0)))

        return im_data


# Register MSL Navcam EDR loader
msl_navcam_edr_loader = MSLNavcamEDRLoader()
register_data_loader(msl_navcam_edr_loader)


class MSLMastcamEDRLoader(DataLoader):
    def __init__(self):
        super(MSLMastcamEDRLoader, self).__init__('mastcam')

    def _load(self, file_path):
        if not os.path.exists(file_path):
            raise RuntimeError('Mastcam image not found: %s' %
                               os.path.abspath(file_path))

        try:
            im_pil = Image.open(file_path)
            im_data = np.array(im_pil)
            im_pil.close()
        except Exception:
            raise RuntimeError('Failed loading Mastcam image: %s' %
                               os.path.abspath(file_path))

        return im_data


# Register MSL Mastcam EDR loader
msl_mastcam_edr_loader = MSLMastcamEDRLoader()
register_data_loader(msl_mastcam_edr_loader)


class MSLMastcamMultispectralEDRLoader(DataLoader):
    def __init__(self):
        super(MSLMastcamMultispectralEDRLoader, self).__init__('mastcam '
                                                               'multispectral')

    def _load(self, file_paths):
        multispectral_im = []

        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise RuntimeError('Mastcam multispectral image not found: %s' %
                                   os.path.abspath(file_path))

            try:
                im_pil = Image.open(file_path)
                im_data = np.array(im_pil)
                im_pil.close()
                multispectral_im.append(im_data)
            except Exception:
                raise RuntimeError('Failed loading Mastcam multispectral '
                                   'image: %s' % os.path.abspath(file_path))

        # shape = band x row x column
        multispectral_im = np.array(multispectral_im)

        # we want the shape to be row x column x band
        multispectral_im = np.moveaxis(multispectral_im, 0, 2)

        return multispectral_im


# Register MSL Mastcam multispectral EDR loader
msl_mastcam_multispectral_edr_loader = MSLMastcamMultispectralEDRLoader()
register_data_loader(msl_mastcam_multispectral_edr_loader)


class MSLMastcamGrayscaleEDRLoader(DataLoader):
    def __init__(self):
        super(MSLMastcamGrayscaleEDRLoader, self).__init__('mastcam grayscale')
    
    def _load(self, file_path):
        if not os.path.exists(file_path):
            raise RuntimeError('Mastcam image not found: %s' %
                               os.path.abspath(file_path))

        try:
            im_pil = Image.open(file_path).convert('L')
            im_data = np.array(im_pil)
            im_pil.close()
        except Exception:
            raise RuntimeError('Failed loading Mastcam image: %s' %
                               os.path.abspath(file_path))

        return im_data


# Register MSL Mastcam grayscale EDR loader
msl_mastcam_grayscale_edr_loader = MSLMastcamGrayscaleEDRLoader()
register_data_loader(msl_mastcam_grayscale_edr_loader)


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
