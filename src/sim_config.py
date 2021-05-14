# Simulator configuration manager - (1) parse config file; (2) verify parameters
# specified in the config file are valid. See copyright notice at the end.
#
# Steven Lu, June 29, 2020

import os
import sys
import yaml
import json
from util import remove_all


CONFIG_KEYWORDS = ['data_type', 'data_root', 'start_sol', 'end_sol', 'out_dir',
                   'features', 'ranking_methods', 'source_file', 'min_prior',
                   'max_prior', 'use_prior', 'crop_shape', 'min_crop_area',
                   'enable_explanation', 'enable_normalization', 'test_image']
SUPPORTED_DATA_TYPE = ['navcam', 'mastcam', 'mastcam multispectral',
                       'mastcam grayscale']
SUPPORTED_CROP_SHAPE = ['square', 'rectangle']
SUPPORTED_FEATURES = ['pixel_values', 'mean', 'std', 'median', 'skew',
                      'kurtosis', 'min', 'max', 'aegis']
SUPPORTED_RANKING_METHODS = ['aegis', 'demud', 'iforest', 'lrx', 'pca', 'rx',
                             'random', 'negative_sampling']


class SimulatorConfig(object):
    def __init__(self, config_file, out_dir=None, logger=None,
                 disable_dir_checks=True):
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
        self.data_root = config['data_root']
        self.start_sol = config['start_sol']
        self.end_sol = config['end_sol']
        test_image = config['test_image']
        self.test_image = None if test_image == 'None' else test_image
        self.use_prior = config['use_prior']
        self.min_prior = config['min_prior']
        self.max_prior = config['max_prior']
        self.crop_shape = config['crop_shape']
        self.min_crop_area = config['min_crop_area']
        self.source_file = config['source_file']
        self.enable_explanation = config['enable_explanation']
        self.enable_normalization = config['enable_normalization']
        self.features = config['features']
        self.ranking_methods = config['ranking_methods']

        if out_dir is not None:
            self.out_dir = out_dir
        else:
            self.out_dir = config['out_dir']

        # Log config settings
        self.log_configs(config_file, logger)

        # Verify parameters in config file.
        self.verify_config_parameters(logger, disable_dir_checks)

    def log_configs(self, config_file, logger):
        if logger is None:
            return

        logger.text('Loading configuration file: %s' %
                    os.path.abspath(config_file))
        logger.text('data_type: %s' % self.data_type)
        logger.text('data_root: %s' % self.data_root)
        logger.text('start_sol: %d' % self.start_sol)
        logger.text('end_sol: %d' % self.end_sol)
        logger.text('test_image: %s' % self.test_image)
        logger.text('use_prior: %r' % self.use_prior)
        logger.text('min_prior: %d' % self.min_prior)
        logger.text('max_prior: %d' % self.max_prior)
        logger.text('crop_shape: %s' % self.crop_shape)
        logger.text('min_crop_area: %d' % self.min_crop_area)
        logger.text('source_file: %s' % self.source_file)
        logger.text('enable_explanation: %r' % self.enable_explanation)
        logger.text('enable_normalization: %r' % self.enable_normalization)
        logger.text('out_dir: %s' % self.out_dir)
        logger.text('features enabled:')
        for dim, methods in self.features.items():
            logger.text('feature dimensionality: %s' % dim)
            for method_name, method_params in methods.items():
                logger.text('%s: %s' % (method_name,
                                        json.dumps(method_params)))
        logger.text('ranking methods enabled:')
        for method_name, method_params in self.ranking_methods.items():
            logger.text('%s: %s' % (method_name, json.dumps(method_params)))

    def verify_config_parameters(self, logger, disable_dir_checks=True):
        # Verify `data_type` field
        if not isinstance(self.data_type, basestring):
            raise RuntimeError('data_type must be a string')

        if self.data_type.lower() not in SUPPORTED_DATA_TYPE:
            raise RuntimeError(
                'data_type not supported: %s. Supported data_type: %s'
                % (self.data_type, json.dumps(SUPPORTED_DATA_TYPE))
            )

        # Verify `data_root`
        if not isinstance(self.data_root, basestring):
            raise RuntimeError('data_root must be a string')

        if not os.path.exists(self.data_root):
            raise RuntimeError('data_root not found: %s' %
                               os.path.abspath(self.data_root))

        if not os.path.isdir(self.data_root):
            raise RuntimeError('data_root must be a directory: %s' %
                               os.path.abspath(self.data_root))

        # Verify `start_sol` and `end_sol`
        if not isinstance(self.start_sol, int):
            raise RuntimeError('start_sol must be an integer (int)')

        if not isinstance(self.end_sol, int):
            raise RuntimeError('end_sol must be an integer (int)')

        if self.start_sol > self.end_sol:
            raise RuntimeError('start_sol must be smaller than end_sol')

        # Verify `test_image`
        if self.test_image is not None and \
                not isinstance(self.test_image, basestring):
            raise RuntimeError('test_image must be a string')

        # Verify `use_prior`, 'min_prior', and `max_prior`
        if not isinstance(self.use_prior, bool):
            raise RuntimeError('use_prior must be boolean type.')

        if not isinstance(self.min_prior, int):
            raise RuntimeError('min_prior must be an integer (int)')

        if not isinstance(self.max_prior, int):
            raise RuntimeError('max_prior must be an integer (int)')

        if self.min_prior > self.max_prior:
            raise RuntimeError('min_prior must be smaller than max_prior')

        # Verify `crop_shape`
        if self.crop_shape not in SUPPORTED_CROP_SHAPE:
            raise RuntimeError('Unrecognized value for crop_shape: %s' %
                               self.crop_shape)

        # Verify `min_crop_area`
        if not isinstance(self.min_crop_area, int):
            raise RuntimeError('The value of min_crop_area must be an integer')

        # Verify `source_file`
        if not os.path.exists(self.source_file):
            raise RuntimeError('source_file not found: %s' %
                               os.path.abspath(self.source_file))

        # Verify `ranking_methods`
        if not isinstance(self.ranking_methods, dict):
            raise RuntimeError(
                'ranking_methods must be a dictionary (dict)')

        for key in self.ranking_methods.keys():
            if key not in SUPPORTED_RANKING_METHODS:
                raise RuntimeError(
                    'ranking method %s is not supported. Supported methods are '
                    '%s' % (key, json.dumps(SUPPORTED_RANKING_METHODS))
                )

            if not isinstance(self.ranking_methods[key], dict):
                raise RuntimeError(
                    'The input parameters for %s ranking method must be '
                    'defined in a dictionary (dict)' % key
                )

        if not disable_dir_checks:
            # Verify `out_dir`
            if not os.path.exists(self.out_dir):
                user_input = raw_input(
                    '[QUESTION] Output directory %s does not exist. Do you '
                    'want to create it? (y/n)' % os.path.abspath(self.out_dir)
                )

                if user_input.lower() == 'y':
                    os.makedirs(self.out_dir)
                    print '[INFO] Create output directory: %s' % \
                        os.path.abspath(self.out_dir)
                    if logger is not None:
                        logger.text('out_dir does not exist. Created out_dir: '
                                    '%s' % os.path.abspath(self.out_dir))
                elif user_input.lower() == 'n':
                    print '[INFO] Exit.'
                    if logger is not None:
                        logger.text('out_dir does not exist. Program exits '
                                    'based on user input.')
                    sys.exit(0)
                else:
                    raise RuntimeError('User input %s not understand.' %
                                       user_input)
            else:
                user_input = raw_input(
                    '[QUESTION] Output directory %s exists. Do you want to '
                    'delete all files and directories in the out_dir? (y/n)' %
                    os.path.abspath(self.out_dir)
                )

                if user_input.lower() == 'y':
                    remove_all(self.out_dir)
                    print '[INFO] All files and directories have been deleted.'

                    if logger is not None:
                        logger.text('out_dir exists. Results in out_dir will '
                                    'be overwritten')
                elif user_input.lower() == 'n':
                    print '[INFO] Exit.'
                    if logger is not None:
                        logger.text('out_dir exists. Program exits based on '
                                    'user input.')
                    sys.exit(0)
                else:
                    raise RuntimeError('User input %s not understand.' %
                                       user_input)

        # Verify `enable_explanation`
        if not isinstance(self.enable_explanation, bool):
            raise RuntimeError('enable_explanation must be a boolean type.')

        # This is hard coded logic. Currently, the explanation can be enabled
        # only when `flattened_pixel_values` feature is used alone.
        if self.enable_explanation:
            if 'one_dimensional' not in self.features.keys():
                raise RuntimeError(
                    'Invalid feature dimensionality. If enable_explanation is '
                    'True, only flattened_pixel_values feature in '
                    'one_dimensional group can be used'
                )

            if 'flattened_pixel_values' not in \
                self.features['one_dimensional'].keys():
                raise RuntimeError(
                    'If enable_explanation is True, only flattened_pixel_values'
                    ' feature in one_dimensional group can be used'
                )

            if len(self.features['one_dimensional'].keys()) > 1:
                raise RuntimeError(
                    'When enable_explanation is True, flattened_pixel_values '
                    'feature must be used alone'
                )

        # Verify `enable_normalization`
        if not isinstance(self.enable_normalization, bool):
            raise RuntimeError('enable_normalization must be a boolean type.')


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