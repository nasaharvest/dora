# The base class of all ranking algorithms.
# The purpose of having a base class is to verify the input and output
# format/shape of each ranking algorithm to make sure they comply with the
# standards pre-defined.
#
# Steven Lu
# May 13, 2020

import os
import numpy as np
from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from util import save_results
from util import verify_common_input_args
from util import save_features_csv


RANKING_ALG_POOL = []


def register_ranking_alg(ranking_alg):
    if isinstance(ranking_alg, Ranking):
        RANKING_ALG_POOL.append(ranking_alg)
    else:
        raise RuntimeError('Invalid ranking algorithm cannot be registered in '
                           'the ranking algorithm pool. Valid ranking '
                           'algorithm must implement the base class Ranking.')


def get_ranking_alg_by_name(alg_name):
    ret_ranking_alg = None
    for ranking_alg in RANKING_ALG_POOL:
        if ranking_alg.can_run(alg_name):
            ret_ranking_alg = ranking_alg
            break

    if ret_ranking_alg is None:
        raise RuntimeError('No ranking algorithm can be used for %s specified '
                           'in the configuration file.' % alg_name)

    return ret_ranking_alg


@add_metaclass(ABCMeta)
class Ranking(object):
    def __init__(self, ranking_alg_name):
        self._ranking_alg_name = ranking_alg_name

    def can_run(self, ranking_alg_name):
        if self._ranking_alg_name == ranking_alg_name:
            return True
        else:
            return False

    def run(self, data_dir, prior_dir, start_sol, end_sol, out_dir, seed,
            **kwargs):
        # Verify common input arguments. If any of the arguments is invalid,
        # runtime error will be thrown.
        verify_common_input_args(data_dir, prior_dir, start_sol, end_sol)

        # Run ranking algorithm
        results, fn_suffix = self._rank_internal(data_dir, prior_dir, start_sol,
                                                 end_sol, seed, **kwargs)

        # Verify the results type. Must be a dictionary contains the keywords
        # 'ind', 'img_id', 'sel_ind', 'scores'.
        if not isinstance(results, dict):
            raise RuntimeError('Unexpected results type for algorithm %s. '
                               'The results type must be dict.' %
                               self._ranking_alg_name)

        if 'ind' not in results.keys() or 'img_id' not in results.keys() or \
             'sel_ind' not in results.keys() or 'scores' not in results.keys() or \
             'explanations' not in results.keys():
            raise RuntimeError("Unexpected results format: %s" %
                               self._ranking_alg_name)

        # Save results in a csv file.
        if len(fn_suffix) == 0:
            results_fn = 'selections.csv'
        else:
            results_fn = 'selections-%s.csv' % fn_suffix

        save_results(results, out_dir, file_name=results_fn,
                     enable_explanation=False)

    def simulator_run(self, rank_dict, prior_dict, config, logger, seed,
                      save_features, **kwargs):
        for k in rank_dict.keys():
            if k not in ['file_names', 'data']:
                raise RuntimeError('Keyword %s not found.' % k)
        for k in prior_dict.keys():
            if k not in ['file_names', 'data']:
                raise RuntimeError('Keyword %s not found.' % k)

        file_names = rank_dict['file_names']
        file_names.sort()
        rank_data = rank_dict['data'].astype(np.float32)
        prior_data = prior_dict['data'].astype(np.float32)

        # Run ranking algorithm
        results, fn_suffix = self._simulate_rank_internal(
            file_names, rank_data, prior_data, config, seed, **kwargs
        )

        if save_features:
            rank_csv = os.path.join(config.out_dir, '%d_%d_testing.csv' %
                                    (config.start_sol, config.end_sol))
            save_features_csv(rank_dict, rank_csv)

            prior_csv = os.path.join(config.out_dir, '%d_%d_training.csv' %
                                     (config.min_prior, config.max_prior))
            save_features_csv(prior_dict, prior_csv)

        # Verify the results type. Must be a dictionary contains the keywords
        # 'ind', 'img_id', 'sel_ind', 'scores'.
        if not isinstance(results, dict):
            raise RuntimeError('Unexpected results type for algorithm %s. '
                               'The results type must be dict.' %
                               self._ranking_alg_name)

        if 'ind' not in results.keys() or 'img_id' not in results.keys() or \
             'sel_ind' not in results.keys() or 'scores' not in results.keys() or \
             'explanations' not in results.keys():
            raise RuntimeError("Unexpected results format: %s" %
                               self._ranking_alg_name)

        # Save results in a csv file.
        if len(fn_suffix) == 0:
            alg_subdir_name = self._ranking_alg_name
            results_fn = 'selections.csv'
        else:
            alg_subdir_name = '%s-%s' % (self._ranking_alg_name, fn_suffix)
            results_fn = 'selections-%s.csv' % fn_suffix

        save_results(
            results, os.path.join(config.out_dir, alg_subdir_name),
            file_name=results_fn, logger=logger,
            enable_explanation=config.enable_explanation
        )

    @abstractmethod
    def _rank_internal(self, data_dir, prior_dir, start_sol, end_sol, seed,
                       **kwargs):
        raise RuntimeError('This function must be implemented in the child '
                           'class.')

    @abstractmethod
    def _simulate_rank_internal(self, file_names, rank_data, prior_data, config,
                                seed, **kwargs):
        raise RuntimeError('This function must be implemented in the child '
                           'class.')


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
