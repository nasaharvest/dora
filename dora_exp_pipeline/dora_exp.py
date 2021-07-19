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
from dora_exp_pipeline.dora_config import DoraConfig
from dora_exp_pipeline.dora_data_loader import get_data_loader_by_name
from dora_exp_pipeline.outlier_detection import register_od_alg
from dora_exp_pipeline.demud_outlier_detection import DEMUDOutlierDetection
from dora_exp_pipeline.iforest_outlier_detection import IForestOutlierDetection
from dora_exp_pipeline.pca_outlier_detection import PCAOutlierDetection
from dora_exp_pipeline.lrx_outlier_detection import LocalRXOutlierDetection
from dora_exp_pipeline.rx_outlier_detection import RXOutlierDetection
from dora_exp_pipeline.random_outlier_detection import RandomOutlierDetection
from dora_exp_pipeline.negative_sampling_outlier_detection import \
    NegativeSamplingOutlierDetection
from dora_exp_pipeline.util import LogUtil
from dora_exp_pipeline.dora_feature import extract_feature
from dora_exp_pipeline.outlier_detection import get_alg_by_name


def register_od_algs():
    # Register DEMUD outlier detection algorithm in the pool
    demud_outlier_detection = DEMUDOutlierDetection()
    register_od_alg(demud_outlier_detection)

    # Register Isolation Forest outlier detection algorithm in the pool
    iforest_outlier_detection = IForestOutlierDetection()
    register_od_alg(iforest_outlier_detection)

    # Register PCA outlier detection algorithm in the pool
    pca_outlier_detection = PCAOutlierDetection()
    register_od_alg(pca_outlier_detection)

    # Register LRX outlier detection algorithm in the pool
    lrx_outlier_detection = LocalRXOutlierDetection()
    register_od_alg(lrx_outlier_detection)

    # Register RX outlier detection algorithm in the pool
    rx_outlier_detection = RXOutlierDetection()
    register_od_alg(rx_outlier_detection)

    # Register Random outlier detection algorithm in the pool
    random_outlier_detection = RandomOutlierDetection()
    register_od_alg(random_outlier_detection)

    # Register Negative Sampling outlier detection algorithm in the pool
    negative_sampling_outlier_detection = NegativeSamplingOutlierDetection()
    register_od_alg(negative_sampling_outlier_detection)


def start(config_file: str, out_dir: str, log_file=None, seed=1234):
    if not os.path.exists(config_file):
        print('[ERROR] Configuration file not found: %s' %
              os.path.abspath(config_file))
        sys.exit(1)

    logger = None
    if log_file is not None:
        logger = LogUtil('dora_exp', log_file)

    config = DoraConfig(config_file, logger)
    if out_dir is not None:
        config.out_dir = out_dir
        if logger:
            logger.text('Argument out_dir is specified in the command line '
                        'interface, and it will overwrite the out_dir in the '
                        'config file.')
            logger.text(f'out_dir used is {os.path.abspath(config.out_dir)}')

    if not os.path.exists(config.out_dir):
        os.mkdir(config.out_dir)
        if logger:
            logger.text(f'Created out_dir: '
                        f'{os.path.abspath(config.out_dir)}')

    # Register all ranking algorithms supported
    register_od_algs()

    # Get data loader
    data_loader = get_data_loader_by_name(config.data_type)
    if logger:
        logger.text(f'Use data loader: {config.data_type}')

    # Read data_to_fit (dtf)
    dtf_dict = data_loader.load(config.data_to_fit, config.outlier_detection)

    # Read data_to_score (dts)
    dts_dict = data_loader.load(config.data_to_score, config.outlier_detection)

    # Feature extraction
    dtf_features = extract_feature(dtf_dict, config.features)
    dts_features = extract_feature(dts_dict, config.features)

    # Outlier detection
    for alg_name, alg_params in config.outlier_detection.items():
        outlier_alg = get_alg_by_name(alg_name)
        outlier_alg.run(dtf_features, dts_features, dts_dict['id'],
                        config.out_dir, config.results, config.top_n, logger,
                        seed, **alg_params)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='The DORA Experiment Pipeline')

    parser.add_argument('config_file', type=str,
                        help='Path to the configuration file')
    parser.add_argument('-o', '--out_dir', type=str,
                        help='Output directory. If specified, it will overwrite'
                             ' the out_dir option in the config file.')
    parser.add_argument('-l', '--log_file', type=str,
                        help='Log file. This is optional. If enabled, a log '
                             'file will be saved. ')
    parser.add_argument('--seed', type=int, default=1234,
                        help='Integer used to seed the random generator '
                             'for the DORA experiment pipeline. Default is '
                             '1234.')

    args = parser.parse_args()
    start(**vars(args))


if __name__ == '__main__':
    main()


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
