#!/usr/bin/env python
# This is entry script for the novelty targeting onboard simulator. Please see
# the README file for how to use it.
# https://github.jpl.nasa.gov/wkiri/novelty-targeting/blob/master/README.md
#
# See copyright notice at the end.
#
# Steven Lu
# June 26, 2020

import os
import sys
import json
from sim_config import SimulatorConfig
from sim_data_loader import get_data_loader_by_name
from sim_data_finder import get_data_finder_by_name
from sim_feature import z_score_normalize
from ranking import get_ranking_alg_by_name
from ranking import register_ranking_alg
from aegis_ranking import AEGISRanking
from demud_ranking import DEMUDRanking
from iforest_ranking import IForestRanking
from pca_ranking import PCARanking
from lrx_ranking import LocalRXRanking
from rx_ranking import RXRanking
from random_ranking import RandomRanking
from negative_sampling_ranking import NegativeSamplingRanking
from util import load_crop_features
from util import LogUtil


def register_ranking_algs():
    # Create ranking algorithms
    aegis_ranking = AEGISRanking()
    demud_ranking = DEMUDRanking()
    iforest_ranking = IForestRanking()
    pca_ranking = PCARanking()
    lrx_ranking = LocalRXRanking()
    rx_ranking = RXRanking()
    random_ranking = RandomRanking()
    negative_sampling_ranking = NegativeSamplingRanking()

    # Register ranking algorithms
    register_ranking_alg(aegis_ranking)
    register_ranking_alg(demud_ranking)
    register_ranking_alg(iforest_ranking)
    register_ranking_alg(pca_ranking)
    register_ranking_alg(lrx_ranking)
    register_ranking_alg(rx_ranking)
    register_ranking_alg(random_ranking)
    register_ranking_alg(negative_sampling_ranking)


def start(config_file, out_dir=None, start_sol=None, end_sol=None,
          test_image=None, min_prior=None, max_prior=None, log_file=None,
          disable_dir_checks=False, seed=1234, save_features=False):

    if not os.path.exists(config_file):
        print '[ERROR] Configuration file not found: %s' % \
              os.path.abspath(config_file)
        sys.exit(1)

    logger = None
    if log_file is not None:
        logger = LogUtil('simulator', log_file)

    config = SimulatorConfig(config_file, out_dir, logger,
                             disable_dir_checks=disable_dir_checks)

    if out_dir is not None and log_file is not None:
        logger.text('Overwriting out_dir defined in the config file. '
                    'out_dir used is %s' % os.path.abspath(config.out_dir))

    if start_sol is not None:
        config.start_sol = start_sol
        if log_file is not None:
            logger.text('Overwriting start_sol defined in the config file. '
                        'start_sol used is %d' % config.start_sol)

    if end_sol is not None:
        config.end_sol = end_sol
        if log_file is not None:
            logger.text('Overwriting end_sol defined in the config file. '
                        'end_sol used is %d' % config.end_sol)

    if test_image is not None:
        config.test_image = test_image
        if log_file is not None:
            logger.text('Overwriting test_image defined in the config file. '
                        'test_image used is %s' % config.test_image)

    if min_prior is not None:
        config.min_prior = min_prior
        config.use_prior = True
        if log_file is not None:
            logger.text('Overwriting min_prior defined in the config file. '
                        'min_prior used is %d' % config.min_prior)

    if max_prior is not None:
        config.max_prior = max_prior
        config.use_prior = True
        if log_file is not None:
            logger.text('Overwriting max_prior defined in the config file. '
                        'max_prior used is %d' % config.max_prior)

    # Register all ranking algorithms supported
    register_ranking_algs()

    # Initialize data finder based on input data type (navcam v.s. mastcam)
    data_finder = get_data_finder_by_name(config.data_type)
    if logger is not None:
        logger.text('Use data finder: %s' % config.data_type)

    # Get data loader
    data_loader = get_data_loader_by_name(config.data_type)
    if logger is not None:
        logger.text('Use data loader: %s' % config.data_type)

    # Get a list of images to be ranked
    rank_list = data_finder.get_data_files(
        config.data_root, config.start_sol, config.end_sol, config.test_image,
        config.source_file)
    if logger is not None:
        for rank_img in rank_list:
            logger.text('Identified %d targets to rank in image %s' %
                        (len(rank_img['targets']), rank_img['file_path']))
            for ind, target in enumerate(rank_img['targets']):
                logger.text('%d. Target ID: %d' % (ind + 1, target['id']))

    # Get a list of images to be used as prior knowledge
    prior_list = []
    if config.use_prior:
        prior_list = data_finder.get_data_files(
            config.data_root, config.min_prior, config.max_prior, None,
            config.source_file)

        if logger is not None:
            counter = 0
            for prior_img in prior_list:
                logger.text('Identified %d targets to use as prior knowledge '
                            'in image %s' % (len(prior_img['targets']),
                                             prior_img['file_path']))
                for ind, target in enumerate(prior_img['targets']):
                    counter += 1
                    logger.text('%d. Target ID: %d' % (ind + 1, target['id']))
            logger.text('Total number of prior targets used: %d' % counter)

    # Loading whole image, cropping out targets, and then feature extraction
    rank_dict = load_crop_features(rank_list, data_loader, config.features,
                                   config.crop_shape, config.min_crop_area)
    if logger is not None:
        logger.text('Feature extraction done for targets to be ranked.')

    prior_dict = load_crop_features(prior_list, data_loader, config.features,
                                    config.crop_shape, config.min_crop_area)
    if logger is not None:
        logger.text('Feature extraction done for prior targets.')

    # Normalization
    if config.enable_normalization:
        if config.use_prior:
            # If prior data is available, we use it to calculate mean and
            # standard deviation.
            prior_dict['data'], rank_dict['data'] = z_score_normalize(
                prior_dict['data'], rank_dict['data']
            )

            if logger is not None:
                logger.text('Prior data and rank data are normalized using the '
                            'mean and standard deviation calculated from prior '
                            'data.')
        else:
            # If prior data isn't available, we use rank data to calculate mean
            # and standard deviation.
            _, rank_dict['data'] = z_score_normalize(
                rank_dict['data'], rank_dict['data']
            )

            if logger is not None:
                logger.text('Prior data is not available. Rank data is '
                            'normalized using the mean and standard deviation '
                            'calculated from itself.')

    if logger is not None:
        logger.text('Random seed used for ranking algorithm: %d' % seed)

    for alg_name, params in config.ranking_methods.items():
        if logger is not None:
            logger.text('Ranking targets using: %s %s' % (alg_name,
                                                          json.dumps(params)))
        ranking_alg = get_ranking_alg_by_name(alg_name)
        ranking_alg.simulator_run(
            rank_dict, prior_dict, config, logger, seed, save_features, **params
        )


def main():
    import argparse
    parser = argparse.ArgumentParser(description='onboard simulator')

    parser.add_argument('config_file', type=str,
                        help='Path to the configuration file')
    parser.add_argument('-o', '--out_dir', type=str,
                        help='The output directory of an experiment run. If it '
                             'is specified, it will overwrite the out_dir '
                             'defined in the config file.')
    parser.add_argument('-s', '--start_sol', type=int,
                        help='Minimum (starting) sol. This is an optional '
                             'argument. If it is specified, it will overwrite '
                             'the start_sol defined in the config file.')
    parser.add_argument('-e', '--end_sol', type=int,
                        help="Maximum (ending) sol. This is an optional "
                             "argument. If it is specified, it will overwrite "
                             "the end_sol defined in the config file.")
    parser.add_argument('-t', '--test_image', type=str, default=None,
                        help='Optional argument. If provided, it will overwrite'
                             ' the test_image option specified in the config '
                             'file. See more details at one of the example '
                             'config files.')
    parser.add_argument('-p', '--min_prior', type=int,
                        help="Minimum prior sol. This is an optional argument. "
                             "If it is specified, it will overwrite the "
                             "min_prior defined in the config file.")
    parser.add_argument('-q', '--max_prior', type=int,
                        help="Maximum prior sol. This is an optional argument. "
                             "If it is specified, it will overwrite the "
                             "max_prior defined in the config file.")
    parser.add_argument('-l', '--log_file', type=str,
                        help='Log file. This is optional. If enabled, a log '
                             'file will be saved. ')
    parser.add_argument('--seed', type=int, default=1234,
                        help='Integer used to seed the random generator '
                             'in the simulator. Default is 1234.')
    parser.add_argument('--save_features', action='store_true',
                        help='If this option is enabled, the extract features '
                             'will be saved in CSV file(s) in the directory '
                             'specified by out_dir')

    args = parser.parse_args()
    start(**vars(args))


if __name__ == '__main__':
    main()


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
