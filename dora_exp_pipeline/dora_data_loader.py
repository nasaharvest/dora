# This script provides functionalities to load data. See copyright notice at
# the end.
#
# Steven Lu, June 29, 2019

import os
import glob
import csv
import numpy as np
import pandas as pd
import rasterio as rio
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

    def load(self, path: str):
        if path is None:
            return None

        data_dict = self._load(path)

        if not isinstance(data_dict, dict):
            raise RuntimeError(f'Unexpected return type: {type(data_dict)}')

        return data_dict

    @abstractmethod
    def _load(self, file_path: str) -> dict:
        raise RuntimeError('Development error. This function should never be '
                           'called directly.')


class ImageLoader(DataLoader):
    def __init__(self):
        super(ImageLoader, self).__init__('image')

    def _load(self, dir_path: str) -> dict:
        if not os.path.exists(dir_path):
            raise RuntimeError(f'Directory not found: '
                               f'{os.path.abspath(dir_path)}')

        data_dict = dict()
        data_dict.setdefault('id', [])
        data_dict.setdefault('data', [])
        file_list = glob.glob(os.path.join(dir_path, '*'))

        for f in file_list:
            file_id = os.path.basename(f)
            file_ext = os.path.splitext(file_id)[1]

            if file_ext.lower() == '.jpg' or file_ext.lower() == '.png':
                im_pil = Image.open(f)
                im_data = np.array(im_pil)
                im_pil.close()
            elif file_ext.lower() == '.img':
                im = PDS3Image.open(f)
                im_data = im.image
            else:
                raise RuntimeError(f'The format of the input is not '
                                   f'recognized: {os.path.abspath(f)}')

            data_dict['id'].append(file_id)
            data_dict['data'].append(im_data)

        return data_dict


image_loader = ImageLoader()
register_data_loader(image_loader)


class ImageDirectoryLoader(DataLoader):
    def __init__(self):
        super(ImageDirectoryLoader, self).__init__('image_dir')

    def _load(self, dir_path: str) -> dict:
        if not os.path.exists(dir_path):
            raise RuntimeError(f'Directory not found: '
                               f'{os.path.abspath(dir_path)}')

        # List of supported file types
        file_types = tuple(['.jpg', '.png', '.bmp', '.gif'])

        file_list = glob.glob('%s/*' % dir_path)
        file_ids = [os.path.basename(f) for f in file_list]

        is_supported = [filename.endswith(file_types) for filename in file_list]
        if not np.all(is_supported):
            raise RuntimeError(f'The image directory loader only supports '
                               f'{", ".join(file_types)}')

        # Add extra dimension to match format of other input data
        file_data = [[filename] for filename in file_list]
        data_dict = {
            'id': file_ids,
            'data': file_data
        }

        return data_dict


image_directory_loader = ImageDirectoryLoader()
register_data_loader(image_directory_loader)


class RasterLoader(DataLoader):
    def __init__(self):
        super(RasterLoader, self).__init__('raster')

    def _load(self, dir_path: str) -> dict:
        if not os.path.exists(dir_path):
            raise RuntimeError(f'Directory not found: '
                               f'{os.path.abspath(dir_path)}')

        # List of supported file types
        file_types = ['.tif']

        data_dict = dict()
        data_dict.setdefault('id', [])
        data_dict.setdefault('data', [])

        if dir_path.endswith('.tif'):
            # Load the raster
            with rio.open(dir_path) as src:
                img = src.read()
                # rasterio reads images in channels-first order
                # we want to put it in channels-last order
                img = np.moveaxis(img, 0, -1)
                # flatten the raster so we have an array of feature
                # vectors where each pixel is a feature vector
                img = np.reshape(img, [img.shape[0]*img.shape[1],
                                       img.shape[2]])
                print(img.shape)
                # set the ID to the index of the pixel
                data_dict['id'] = range(img.shape[0])
                data_dict['data'] = list(img)
        else:
            raise RuntimeError(f'File extension not supported. '
                               f'Valid file extensions: '
                               f'{file_types}')

        return data_dict


raster_loader = RasterLoader()
register_data_loader(raster_loader)


class CatalogLoader(DataLoader):
    def __init__(self):
        super(CatalogLoader, self).__init__('Catalog')

    def _load(self, dir_path: str) -> dict:
        if not os.path.exists(dir_path):
            raise RuntimeError(f'Directory not found: '
                               f'{os.path.abspath(dir_path)}')

        # List of supported file types
        file_types = ['.h5']

        data_dict = dict()
        data_dict.setdefault('id', [])
        data_dict.setdefault('data', [])

        # (e.g., .h5 dataframes, .npy)
        if dir_path.endswith('.h5'):
            # Load the .h5
            df = pd.read_hdf(dir_path)
            data_dict['id'] = df.index
            data_dict['data'] = df.values

        else:
            raise RuntimeError(f'File extension not supported. '
                               f'Valid file extensions: '
                               f'{file_types}')

        return data_dict


catalog_loader = CatalogLoader()
register_data_loader(catalog_loader)


class TimeSeriesLoader(DataLoader):
    def __init__(self):
        super(TimeSeriesLoader, self).__init__('Time series')

    def _load(self, dir_path: str) -> dict:
        if not os.path.exists(dir_path):
            raise RuntimeError(f'Directory not found: '
                               f'{os.path.abspath(dir_path)}')

        # List of supported file types
        file_types = ['.csv']

        data_dict = dict()
        data_dict.setdefault('id', [])
        data_dict.setdefault('data', [])

        # TODO: add support for other data types
        # (e.g., .h5 dataframes, .npy)
        if dir_path.endswith('.csv'):
            # Load the csv data
            with open(dir_path, 'r') as csv_file:
                csv_reader = csv.reader(csv_file, quoting=csv.QUOTE_NONNUMERIC)
                # Read each row into the data_dict
                for row in csv_reader:
                    # Assumes the first column is the ID
                    # and all other columns are time steps
                    data_dict['id'].append(row[0])
                    data_dict['data'].append(np.array(row[1:]))
        else:
            raise RuntimeError(f'File extension not supported. '
                               f'Valid file extensions: '
                               f'{file_types}')

        return data_dict


time_series_loader = TimeSeriesLoader()
register_data_loader(time_series_loader)


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
