# DORA configuration manager - (1) parse config file; (2) verify parameters
# specified in the config file are valid. See copyright notice at the end.
#
# Steven Lu
# May 21, 2021

import os
import yaml


CONFIG_KEYWORDS = ['data_type', 'data_to_fit', 'data_to_score',
                   'zscore_normalization', 'features', 'outlier_detection',
                   'results']


class DoraConfig(object):
    def __init__(self, config_file: str, logger=None):
        if not os.path.exists(config_file):
            raise RuntimeError('Config file not found: %s' %
                               os.path.abspath(config_file))

        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        # Verify keywords in config file
        for key in config.keys():
            if key not in CONFIG_KEYWORDS:
                raise RuntimeError('Unrecognized keyword %s is provided in the '
                                   'config file' % key)

        # Verify required parameters are provided in the config file
        for r_key in CONFIG_KEYWORDS:
            if r_key not in config.keys():
                raise RuntimeError('Required keyword %s is not provided in the '
                                   'config file' % r_key)

        self.data_type = config['data_type']
        self.data_to_fit = config['data_to_fit']
        self.data_to_score = config['data_to_score']
        self.zscore_normalization = config['zscore_normalization']
        self.features = config['features']
        self.outlier_detection = config['outlier_detection']
        self.results = config['results']
        self.logger = logger

        # Log config settings
        self.log_configs(config_file)

        # Verify parameters in config file.
        self.verify_config_parameters()

    def log_configs(self, config_file):
        if self.logger is None:
            return

        self.logger.text(f'Configuration file: '
                         f'{os.path.abspath(config_file):<20}')
        self.logger.text(f'data_type: {self.data_type:<20}')
        self.logger.text(f'data_to_fit: {self.data_to_fit:<20}')
        self.logger.text(f'data_to_score: {self.data_to_score:<20}')
        self.logger.text(f'zscore_normalization: '
                         f'{self.zscore_normalization:<20}')
        self.logger.text(f'features: {self.features}')
        self.logger.text(f'outlier_detection: {self.outlier_detection}')
        self.logger.text(f'results: {self.results}')

    def verify_config_parameters(self):
        # Verify `data_type` field
        if not isinstance(self.data_type, str):
            raise RuntimeError(f'data_type field must be a string')

        # Verify `data_to_fit`
        if not isinstance(self.data_to_fit, str):
            raise RuntimeError(f'data_to_fit field must be a string')

        if not os.path.exists(self.data_to_fit):
            raise RuntimeError(f'data_to_fit not found: '
                               f'{os.path.abspath(self.data_to_fit)}')

        # Verify `data_to_score`
        if not isinstance(self.data_to_score, str):
            raise RuntimeError(f'data_to_score field must be a string')

        if (len(self.data_to_score) != 0 and
                not os.path.exists(self.data_to_score)):
            raise RuntimeError(f'data_to_score not found: '
                               f'{os.path.abspath(self.data_to_score)}')

        # Verify `features`
        if not isinstance(self.features, dict):
            raise RuntimeError(f'features field must be a dictionary')

        # Verify `outlier_detection`
        if not isinstance(self.outlier_detection, dict):
            raise RuntimeError(f'outlier_detection field must be a dictionary')

        # Verify `results`
        if not isinstance(self.results, dict):
            raise RuntimeError(f'results field must be a dictionary')


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
