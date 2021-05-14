#!/usr/bin/env python
# Given a sol range, read in all AEGIS target images and rank them by novelty
# using principal component analysis (PCA) algorithm. Optionally, use a range
# of prior sol's targets to initialize the PCA model.  See copyright notice at
# the end.
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
from ranking import Ranking
from util import load_images
from util import DEFAULT_DATA_DIR
from util import get_image_file_list
from sklearn.decomposition import PCA


class PCARanking(Ranking):
    def __init__(self):
        super(PCARanking, self).__init__('pca')

    def _rank_internal(self, data_dir, prior_dir, start_sol, end_sol, seed, k,
                       min_prior, max_prior):
        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        # Allow specification of separate dir for prior sol targets
        # If not specified, use the original data_dir
        if prior_dir == None:
            prior_dir = data_dir

        # catalog available images to read in
        f_images_tst = get_image_file_list(data_dir, start_sol, end_sol)

        if min_prior < 0 or max_prior < 0 or max_prior < min_prior:
            f_images_trn = f_images_tst
            warnings.warn('Invalid min_prior (%d) or max_prior (%d). Test data '
                          'will be used to initialize the PCA model' %
                          (min_prior, max_prior))
        else:
            f_images_trn = get_image_file_list(prior_dir, min_prior, max_prior)

        # get the image data
        data_trn = load_images(prior_dir, f_images_trn)
        data_tst = load_images(data_dir, f_images_tst)

        # Rank targets
        return self._rank_targets(data_trn, data_tst, f_images_tst, k,
                                  enable_explanation=False)

    def _simulate_rank_internal(self, files, rank_data, prior_data, config,
                                seed, k):
        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        if config.use_prior:
            data_trn = prior_data
        else:
            warnings.warn('use_prior flag is turned off in the config file. '
                          'Test data will be used to initialize the PCA model.')

            data_trn = rank_data

        # check that the number of PCA components <= number of features
        if k > data_trn.shape[1]:
            raise RuntimeError('The number of principal components (k = %d) must '
                               'be < number of features (%d)' % (k, data_trn.shape[1]))

        # Rank targets
        return self._rank_targets(data_trn, rank_data, files, k,
                                  config.enable_explanation)

    def _rank_targets(self, data_train, data_test, files, k,
                      enable_explanation=False):
        # get PCA reconstruction scores, and sort in descending order
        scores_tst, exp_tst = train_and_run_PCA(data_train, data_test, k,
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

        results_file_suffix = 'k-%d' % k

        return results, results_file_suffix


def train_and_run_PCA(train, test, k, enable_explanation=False):

    # initialize the PCA model (deterministically)
    pca = PCA(n_components=k, random_state=0)

    # fit the PCA model
    pca.fit(train)

    return compute_score(test, pca, enable_explanation)


def compute_score(images, pca, enable_explanation=False):
    rows, cols = images.shape
    scores = np.ndarray(images.shape[0])

    residuals = None
    if enable_explanation:
        im_height, im_width = int(np.sqrt(cols)), int(np.sqrt(cols))
        residuals = np.ndarray((rows, im_height, im_width))
    else:
        residuals = np.ndarray((rows, 0, 0))

    for i in range(images.shape[0]):
        # compute the L2 norm between input and reconstruction
        recon = pca.inverse_transform(pca.transform([images[i]]))
        sub = images[i] - recon
        scores[i] = np.linalg.norm(sub, ord=2, axis=1)

        if enable_explanation:
            resid = np.reshape(sub, (im_height, im_width))
            resid = np.interp(resid, (resid.min(), resid.max()), (0, 255))
            residuals[i] = resid

    return scores, residuals


def start(start_sol, end_sol, data_dir, prior_dir, out_dir, k, min_prior, max_prior, seed):
    pca_params = {
        'k': k,
        'min_prior': min_prior,
        'max_prior': max_prior
    }

    pca_ranking = PCARanking()

    try:
        pca_ranking.run(data_dir, prior_dir, start_sol, end_sol, out_dir, seed,
                        **pca_params)
    except RuntimeError as e:
        print e
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='PCA ranking algorithm')
    parser.add_argument('-s', '--start_sol', type=int, default=1343,
                        help='minimum (starting) sol (default 1343)')
    parser.add_argument('-e', '--end_sol', type=int, default=1343,
                        help='maximum (ending) sol (default 1343)')
    parser.add_argument('-d', '--data_dir', default=DEFAULT_DATA_DIR,
                        help='target image data directory (default: %(default)s)')
    parser.add_argument('-pd', '--prior_dir', default=None,
                        help='prior sols target image data directory (default: same as data_dir)')
    parser.add_argument('-o', '--out_dir', default='.',
                        help='output directory (default: .)')
    parser.add_argument('-k', type=int, default=10,
                        help='k (number of principal components, default 10)')
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