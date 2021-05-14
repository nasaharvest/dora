#!/usr/bin/env python
# Given a sol range, read in all AEGIS target images and rank them by novelty
# according to DEMUD. Optionally, use a range of prior sol's targets to
# initialize the DEMUD model. See copyright notice at the end.
#
# Kiri Wagstaff
# April 16, 2020
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

try:
    import cosmic_demud
    from cosmic_demud.dataset import Dataset
except ImportError:
    print('This script requires the COSMIC_DEMUD python library.')
    print('Please follow these steps:')
    print('git clone git@github-fn.jpl.nasa.gov:COSMIC/COSMIC_DEMUD.git')
    print('cd COSMIC_DEMUD')
    print('git checkout feature-config-files')
    print('python setup.py install (with --user if desired)')
    sys.exit(1)


class DEMUDRanking(Ranking):
    def __init__(self):
        super(DEMUDRanking, self).__init__('demud')

    def _demud(self, files, rank_data, prior_data, k, enable_explanation=True):

        # Create a DEMUD data set
        ds = Dataset('', name='novelty')
        ds.data = rank_data.T
        n_items = rank_data.shape[0]
        for i in range(n_items):
            ds.labels.append(files[i])

        if prior_data is not None:
            ds.initdata = np.array(prior_data).T

        # Suppress stdout for DEMUD calls
        stdout_ = sys.stdout
        sys.stdout = open('/dev/null', 'w')

        # Run DEMUD and get selections back
        # 'sels': list of item indices, in order of selection
        demud_results = cosmic_demud.demud(
            ds, k=k, nsel=n_items, inititem=-1, plotresults=False
        )

        # Restore the previous stdout
        sys.stdout = stdout_

        results = dict()
        results.setdefault('ind', [])
        results.setdefault('img_id', [])
        results.setdefault('sel_ind', demud_results['sels'])
        results.setdefault('scores', demud_results['scores'])
        results.setdefault('explanations', [])
        for ind, selection in enumerate(demud_results['sels']):
            results['ind'].append(ind)
            results['img_id'].append(files[selection])

            if enable_explanation:
                # TODO: This is placeholder. Need to be replaced with real
                # TODO: explanations!
                results['explanations'].append(np.ones((64, 64)))

        results_file_suffix = 'k-%d' % k

        return results, results_file_suffix

    def _rank_internal(self, data_dir, prior_dir, start_sol, end_sol, seed, k,
                       min_prior, max_prior):
        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        # Allow specification of separate dir for prior sol targets
        # If not specified, use the original data_dir
        if prior_dir is None:
            prior_dir = data_dir

        # Read in the image data to be ranked
        files = get_image_file_list(data_dir, start_sol, end_sol)
        imdata = load_images(data_dir, files)

        init_imdata = None
        if min_prior < 0 or max_prior < 0 or max_prior < min_prior:
            warn_msg = ('Invalid min_prior (%d) or max_prior (%d); ignored.'
                        % (min_prior, max_prior))
            warnings.warn(warn_msg)
        else:
            init_files = get_image_file_list(prior_dir, min_prior, max_prior)
            init_imdata = load_images(prior_dir, init_files)

        return self._demud(files, imdata, init_imdata, k,
                           enable_explanation=False)

    def _simulate_rank_internal(self, files, rank_data, prior_data, config,
                                seed, k):
        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        if not config.use_prior:
            prior_data = None

        return self._demud(files, rank_data, prior_data, k,
                           config.enable_explanation)


def start(start_sol, end_sol, data_dir, prior_dir, out_dir, k, min_prior, max_prior, seed):

    # Allow specification of separate dir for prior sol targets
    # If not specified, use the original data_dir
    if prior_dir is None:
        prior_dir = data_dir

    demud_params = {
        'k': k,
        'min_prior': min_prior,
        'max_prior': max_prior
    }

    demud_ranking = DEMUDRanking()

    try:
        demud_ranking.run(data_dir, prior_dir, start_sol, end_sol, out_dir, seed,
                          **demud_params)
    except RuntimeError as e:
        print(e)
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='DEMUD ranking algorithm')
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
