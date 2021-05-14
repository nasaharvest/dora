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
from src.ranking import Ranking
from src.util import DEFAULT_DATA_DIR
from src.util import get_image_file_list


class RandomRanking(Ranking):
    def __init__(self):
        super(RandomRanking, self).__init__('random')

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

    # prior_dir is ignored for this algorithm
    def _rank_internal(self, data_dir, prior_dir, start_sol, end_sol, seed):
        # Get the list of images falling in the sol range
        files = get_image_file_list(data_dir, start_sol, end_sol)

        return self._random(files, seed, enable_explanation=False)

    def _simulate_rank_internal(self, files, rank_data, prior_data, config, 
                                seed):
        return self._random(files, seed, config.enable_explanation)


def start(start_sol, end_sol, data_dir, out_dir, seed):
    random_ranking = RandomRanking()

    try:
        random_ranking.run(data_dir, start_sol, end_sol, out_dir, seed)
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
