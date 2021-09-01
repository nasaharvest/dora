# The base class of all outlier detection algorithms.
#
# Steven Lu
# May 21, 2021

import os
import numpy as np
from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from dora_exp_pipeline.util import LogUtil
from dora_exp_pipeline.dora_results_organization import get_res_org_method


def register_od_alg(ranking_alg):
    if isinstance(ranking_alg, OutlierDetection):
        OutlierDetection.algorithm_pool.append(ranking_alg)
    else:
        raise RuntimeError('Invalid ranking algorithm cannot be registered in '
                           'the ranking algorithm pool. Valid ranking '
                           'algorithm must implement the base class Ranking.')


def get_alg_by_name(alg_name):
    ret_ranking_alg = None
    for ranking_alg in OutlierDetection.algorithm_pool:
        if ranking_alg.can_run(alg_name):
            ret_ranking_alg = ranking_alg
            break

    if ret_ranking_alg is None:
        raise RuntimeError('No ranking algorithm can be used for %s specified '
                           'in the configuration file.' % alg_name)

    return ret_ranking_alg


@add_metaclass(ABCMeta)
class OutlierDetection(object):

    algorithm_pool = []

    def __init__(self, ranking_alg_name):
        self._ranking_alg_name = ranking_alg_name

    def can_run(self, ranking_alg_name):
        if self._ranking_alg_name == ranking_alg_name:
            return True
        else:
            return False

    def run(self, dtf: np.ndarray, dts: np.ndarray, dts_ids: list, out_dir: str,
            results_org_dict: dict, top_n: int, logger: LogUtil, seed: int,
            **kwargs) -> None:
        # Don't try to convert strings (i.e. filenames) to float32
        if dts.dtype.type is not np.str_:
            if dtf is not None:
                dtf = dtf.astype(np.float32)
            dts = dts.astype(np.float32)

        if top_n is None:
            top_n = len(dts)

        if top_n > len(dts):
            raise RuntimeError('top_n must be greater than or equal to the '
                               'number of items in data_to_score')

        # Run outlier detection algorithm
        results = self._rank_internal(dtf, dts, dts_ids, top_n, seed, **kwargs)

        # Create algorithm specific sub directory
        kwargs_string = OutlierDetection.dict_to_str(kwargs)
        sub_dir = os.path.join(out_dir, self._ranking_alg_name + kwargs_string)
        if not os.path.exists(sub_dir):
            os.mkdir(sub_dir)
            if logger:
                logger.text(f'Created sub directory for outlier detection '
                            f'algorithm {self._ranking_alg_name} at '
                            f'{os.path.abspath(sub_dir)}')

        # Run results organization methods
        for res_org_name, res_org_params in results_org_dict.items():
            res_org_method = get_res_org_method(res_org_name)
            res_org_method.run(results['dts_ids'], results['scores'],
                               results['sel_ind'], dts, self._ranking_alg_name,
                               sub_dir, logger, seed, top_n, **res_org_params)

    @staticmethod
    def dict_to_str(params_dict: dict()) -> str:
        """ Convert a dictionary of parameters to a string representation. Note
        that if the input dictionary contains nested data structures (e.g.,
        list, dict), this method will fail.
        """
        ret_string = ''
        for k, v in params_dict.items():
            ret_string += '-%s=%s' % (k, str(v).replace('/', ''))

        return ret_string

    @abstractmethod
    def _rank_internal(self, data_to_fit, data_to_score, data_ids, top_n, seed,
                       **kwargs):
        raise RuntimeError('This function must be implemented in the child '
                           'class.')


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
