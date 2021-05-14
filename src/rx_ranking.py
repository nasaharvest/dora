#!/usr/bin/env python
# Given a sol range, read in all AEGIS target images and rank them by novelty
# using Reed-Xiaoli (RX) algorithm. Optionally, use a range of prior sol's
# targets to initialize the RX model. See copyright notice at the end.
#
# Author (TODO)
# Date Created (TODO)
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


class RXRanking(Ranking):
    def __init__(self):
        super(RXRanking, self).__init__('rx')

    def _rank_internal(self, data_dir, prior_dir, start_sol, end_sol, seed,
                       min_prior, max_prior):

        # Allow specification of separate dir for prior sol targets
        # If not specified, use the original data_dir
        if prior_dir is None:
            prior_dir = data_dir

        # catalog available images to read in
        f_images_tst = get_image_file_list(data_dir, start_sol, end_sol)

        if min_prior < 0 or max_prior < 0 or max_prior < min_prior:
            f_images_trn = f_images_tst
            warnings.warn('Invalid min_prior (%d) or max_prior (%d). Test data '
                          'will be used to compute mean and covariance matrix' %
                          (min_prior, max_prior))
        else:
            f_images_trn = get_image_file_list(prior_dir, min_prior, max_prior)

        # get the image data
        data_trn = load_images(prior_dir, f_images_trn)
        data_tst = load_images(data_dir, f_images_tst)

        # Rank targets
        return self._rank_targets(data_trn, data_tst, f_images_tst,
                                  enable_explanation=False)

    def _simulate_rank_internal(self, files, rank_data, prior_data, config,
                                seed):
        if config.use_prior:
            data_trn = prior_data
        else:
            warnings.warn('use_prior flag is turned off in the config file. '
                          'Test data will be used to compute mean and '
                          'covariance matrix.')

            data_trn = rank_data

        # Rank targets
        return self._rank_targets(data_trn, rank_data, files,
                                  config.enable_explanation)

    def _rank_targets(self, data_train, data_test, files,
                      enable_explanation=False):
        # get RX scores, then sort in descending order
        scores_tst, exp_tst = get_RX_scores(data_train, data_test,
                                            enable_explanation)
        indices_srt_by_scores = np.argsort(scores_tst)[::-1]

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
                results['explanations'].append(exp_tst[idx])

        return results, ''


def compute_bg(train_images):
    # compute mean image
    mu = np.mean(train_images, axis=0)
    # compute the covariance matrix for training images
    if train_images.shape[0] < train_images.shape[1]:
        warnings.warn('There are fewer image samples than features. '
                      'Covariance matrix may be singular.')
    cov = np.cov(np.transpose(train_images))
    cov = np.linalg.inv(cov)

    return mu, cov


def compute_score(images, mu, cov, enable_explanation=False):
    rows, cols = images.shape
    scores = np.ndarray(rows)

    explanations = None
    if enable_explanation:
        im_height, im_width = int(np.sqrt(cols)), int(np.sqrt(cols))
        explanations = np.ndarray((rows, im_height, im_width))

    for i in range(rows):
        # compute the L2 norm between input and reconstruction
        sub = images[i] - mu
        rx_score = np.dot(np.dot(sub, cov), sub.T)
        scores[i] = rx_score

        if enable_explanation:
            rx_exp = np.reshape(sub, (im_height, im_width))
            rx_exp = np.interp(rx_exp, (rx_exp.min(), rx_exp.max()), (0, 255))
            explanations[i] = rx_exp

    if np.any(scores < 0):
        warnings.warn('Some RX scores are negative.')

    return scores, explanations


def get_RX_scores(train, test, enable_explanation=False):
    mu, cov = compute_bg(train)

    return compute_score(test, mu, cov, enable_explanation)


def start(start_sol, end_sol, data_dir, prior_dir, out_dir, min_prior, max_prior, seed):
    rx_params = {
        'min_prior': min_prior,
        'max_prior': max_prior
    }

    rx_ranking = RXRanking()

    try:
        rx_ranking.run(data_dir, prior_dir, start_sol, end_sol, out_dir, seed,
                       **rx_params)
    except RuntimeError as e:
        print(e)
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Reed-Xiaoli (RX) ranking algorithm')
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
                        help='Integer used to seed the random generator. This '
                             'argument is not used in this script.')

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
