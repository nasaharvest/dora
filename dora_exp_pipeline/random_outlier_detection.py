#!/usr/bin/env python
# Given a sol range, randomly rank all AEGIS target images. See copyright notice
# at the end.
#
# Steven Lu
# May 1, 2020
#
# Modification history:
# Steven Lu, May 13, 2020, refactored the code to extract common functionalities
#                          out to util.py.

import sys
import numpy as np
from dora_exp_pipeline.outlier_detection import OutlierDetection
from dora_exp_pipeline.util import DEFAULT_DATA_DIR


class RandomOutlierDetection(OutlierDetection):
    def __init__(self):
        super(RandomOutlierDetection, self).__init__('random')

    def _random(self, files, seed, enable_explanation=True):
        # Random ranking
        indices = range(0, len(files))
        random_state = np.random.RandomState(seed)
        random_state.shuffle(indices)

        # Prepare results to return
        results = dict()
        results.setdefault('ind', [])
        results.setdefault('sel_ind', [])
        results.setdefault('img_id', [])
        results.setdefault('scores', [])
        results.setdefault('explanations', [])
        for i, ind in enumerate(indices):
            results['ind'].append(i)
            results['sel_ind'].append(ind)
            results['img_id'].append(files[ind])
            results['scores'].append(0.0)

            if enable_explanation:
                results['explanations'].append(np.ones((64, 64)))

        results_file_suffix = 'seed-%d' % seed

        return results, results_file_suffix

    def _rank_internal(self, files, rank_data, prior_data, config, seed):
        return self._random(files, seed, config.enable_explanation)


def start(start_sol, end_sol, data_dir, out_dir, seed):
    random_outlier_detection = RandomOutlierDetection()

    try:
        random_outlier_detection.run(data_dir, start_sol, end_sol, out_dir,
                                     seed)
    except RuntimeError as e:
        print(e)
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Random ranking algorithm')
    parser.add_argument('-s', '--start_sol', type=int, default=1343,
                        help='minimum (starting) sol (default 1343)')
    parser.add_argument('-e', '--end_sol', type=int, default=1343,
                        help='maximum (ending) sol (default 1343)')
    parser.add_argument('-d', '--data_dir', default=DEFAULT_DATA_DIR,
                        help='target image data directory '
                             '(default: %(default)s)')
    parser.add_argument('-o', '--out_dir', default='.',
                        help='output directory (default: .)')
    parser.add_argument('-r', '--seed', type=int, default=1234,
                        help='random seed to initialize the random number '
                             'generator. Default is 1234')

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
