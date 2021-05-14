#!/usr/bin/env python
# Given a sol range, read in all AEGIS target images and rank them by novelty
# using Isolation Forest algorithm. See copyright notice at the end.
#
# Author (TODO)
# Date created (TODO)
#
# Modification history:
# Steven Lu, May 13, 2020, refactored the code to extract common functionalities
#                          out to util.py.

import sys
import warnings
import numpy as np
from src.ranking import Ranking
from src.util import load_images
from src.util import DEFAULT_DATA_DIR
from src.util import get_image_file_list
from sklearn.ensemble import IsolationForest


class IForestRanking(Ranking):
    def __init__(self):
        super(IForestRanking, self).__init__('iforest')

    def _rank_internal(self, data_dir, prior_dir, start_sol, end_sol, seed,
                       min_prior, max_prior):
        if min_prior < 0 or max_prior < 0 or max_prior < min_prior:
            raise RuntimeError('Invalid min_prior (%d) or max_prior (%d).' %
                               (min_prior, max_prior))

        # Allow specification of separate dir for prior sol targets
        # If not specified, use the original data_dir
        if prior_dir is None:
            prior_dir = data_dir

        # catalog available images to read in
        f_images_trn = get_image_file_list(prior_dir, min_prior, max_prior)
        f_images_tst = get_image_file_list(data_dir, start_sol, end_sol)

        # get the image data
        data_trn = load_images(prior_dir, f_images_trn)
        data_tst = load_images(data_dir, f_images_tst)

        # Rank targets
        return self._rank_targets(data_trn, data_tst, f_images_tst, seed,
                                  enable_explanation=False)

    def _simulate_rank_internal(self, files, rank_data, prior_data, config,
                                seed):
        if config.use_prior:
            data_trn = prior_data
        else:
            warnings.warn('use_prior flag is turned off in the config file. '
                          'Test data will be used as prior data for isolation '
                          'forest ranking method.')

            data_trn = rank_data

        # Rank targets
        return self._rank_targets(data_trn, rank_data, files, seed,
                                  enable_explanation=False)

    def _rank_targets(self, data_train, data_test, files, seed,
                      enable_explanation=False):
        # run the isolation forest
        scores_tst = train_and_run_ISO(data_train, data_test, seed)
        indices_srt_by_scores = np.argsort(scores_tst)

        # prepare results to return
        results = dict()
        results.setdefault('ind', [])
        results.setdefault('sel_ind', [])
        results.setdefault('img_id', [])
        results.setdefault('scores', [])
        results.setdefault('explanations', [])
        for i, idx in enumerate(indices_srt_by_scores):
            results['ind'].append(i)
            results['sel_ind'].append(idx)
            results['img_id'].append(files[idx])
            results['scores'].append(scores_tst[idx])

            if enable_explanation:
                results['explanations'].append(np.ones((64, 64)))

        results_file_suffix = 'seed-%d' % seed

        return results, results_file_suffix


def train_and_run_ISO(train, test, seed):
    random_state = np.random.RandomState(seed)

    # initialize isolation forest
    clf_iso = IsolationForest(max_samples=train.shape[0], contamination=0.1,
                              random_state=random_state, behaviour='new')

    # train isolation forest
    clf_iso.fit(train)

    # novelty scores of the test items
    scores_iso = clf_iso.decision_function(test)

    return scores_iso


def start(start_sol, end_sol, data_dir, prior_dir, out_dir, min_prior, max_prior, seed):
    iforest_params = {
        'min_prior': min_prior,
        'max_prior': max_prior
    }

    iforest_ranking = IForestRanking()

    try:
        iforest_ranking.run(data_dir, prior_dir, start_sol, end_sol, out_dir, seed,
                            **iforest_params)
    except RuntimeError as e:
        print(e)
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Isolation forest ranking algorithm')
    parser.add_argument('-s', '--start_sol', type=int, default=1343,
                        help='minimum (starting) sol (default 1343)')
    parser.add_argument('-e', '--end_sol', type=int, default=1343,
                        help='maximum (ending) sol (default 1343)')
    parser.add_argument('-d', '--data_dir', default=DEFAULT_DATA_DIR,
                        help='target image data directory '
                             '(default: %(default)s)')
    parser.add_argument('-pd', '--prior_dir', default=None,
                        help='prior sols target image data directory '
                             '(default: same as data_dir)')
    parser.add_argument('-o', '--out_dir', default='.',
                        help='output directory (default: .)')
    parser.add_argument('-p', '--min_prior', type=int, default=-1,
                        help='minimum prior sol (default -1)')
    parser.add_argument('-q', '--max_prior', type=int, default=-1,
                        help='maximum prior  sol (default -1)')
    parser.add_argument('--seed', type=int, default=1234,
                        help='Integer used to seed the random generator. '
                             'Default is 1234.')
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
