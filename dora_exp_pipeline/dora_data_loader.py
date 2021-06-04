# This script provides functionalities to load data. See copyright notice at
# the end.
#
# Steven Lu, June 29, 2019

import os
import glob
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

    def load(self, path: str) -> dict:
        data_dict = self._load(path)

        if not isinstance(data_dict, dict):
            raise RuntimeError(f'Unexpected return type: {type(data_dict)}')

        return data_dict

    @abstractmethod
    def _load(self, file_path: str) -> dict:
        raise RuntimeError('Development error. This function should never be '
                           'called directly.')


class GrayscaleImageLoader(DataLoader):
    def __init__(self):
        super(GrayscaleImageLoader, self).__init__('grayscale image')

    def _load(self, dir_path: str) -> dict:
        if not os.path.exists(dir_path):
            raise RuntimeError(f'Directory not found: '
                               f'{os.path.abspath(dir_path)}')

        data_dict = dict()
        data_dict.setdefault('id', [])
        data_dict.setdefault('data', [])
        file_list = glob.glob('%s/*' % dir_path)

        for f in file_list:
            file_id = os.path.basename(f)
            file_ext = os.path.splitext(file_id)[1]

            if file_ext.lower() == '.jpg' or file_ext.lower() == '.png':
                im_pil = Image.open(f)
                im_data = np.array(im_pil)
                im_pil.close()
            elif file_ext == '.img':
                im = PDS3Image.open(f)
                im_data = im.image
            else:
                raise RuntimeError(f'The format of the input is not '
                                   f'recognized: {os.path.abspath(f)}')

            if len(im_data.shape) >= 3:
                raise RuntimeError(f'The input is not a grayscale image: '
                                   f'{os.path.abspath(f)}')

            data_dict['id'].append(file_id)
            data_dict['data'].append(im_data)

        return data_dict


grayscale_image_loader = GrayscaleImageLoader()
register_data_loader(grayscale_image_loader)


class RGBImageLoader(DataLoader):
    def __init__(self):
        super(RGBImageLoader, self).__init__('RGB image')

    def _load(self, dir_path: str) -> dict:
        if not os.path.exists(dir_path):
            raise RuntimeError(f'Directory not found: '
                               f'{os.path.abspath(dir_path)}')

        data_dict = dict()
        data_dict.setdefault('id', [])
        data_dict.setdefault('data', [])
        file_list = glob.glob('%s/*' % dir_path)

        for f in file_list:
            file_id = os.path.basename(f)
            file_ext = os.path.splitext(file_id)[1]

            if file_ext == 'jpg' or file_ext == 'png':
                im_pil = Image.open(f)
                im_data = np.array(im_pil)
                im_pil.close()
            elif file_ext == '.img':
                im = PDS3Image.open(f)
                im_data = im.image
            else:
                raise RuntimeError(f'The format of the input is not '
                                   f'recognized: {os.path.abspath(f)}')

            if len(im_data.shape) != 3:
                raise RuntimeError(f'The input is not a RGB image: '
                                   f'{os.path.abspath(f)}')

            data_dict['id'].append(file_id)
            data_dict['data'].append(im_data)

        return data_dict


rgb_image_loader = RGBImageLoader()
register_data_loader(rgb_image_loader)


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
