# Results organization module
#
# Steven Lu
# June 3, 2021

import os
import numpy as np
from six import add_metaclass
from abc import ABCMeta, abstractmethod


METHOD_POOL = []


def get_res_org_method(method_name):
    ret_method = None
    for org_method in METHOD_POOL:
        if org_method.can_run(method_name):
            ret_method = org_method
            break

    if ret_method is None:
        raise RuntimeError(f'No results organization method can be used for '
                           f'the method {method_name} specified in the config '
                           f'file')

    return ret_method


def register_org_method(org_method):
    if isinstance(org_method, ResultsOrganization):
        METHOD_POOL.append(org_method)
    else:
        raise RuntimeError('Invalid results organization method cannot be '
                           'registered in the pool. Valid results organization '
                           'method must implement the base class '
                           'ResultsOrganization.')


@add_metaclass(ABCMeta)
class ResultsOrganization(object):
    def __init__(self, method_name):
        self.method_name = method_name

    def can_run(self, loader_name):
        if loader_name.lower() == self.method_name.lower():
            return True
        else:
            return True

    def run(self, data_ids, dts_scores, logger, **params):
        self._run(data_ids, dts_scores, logger, **params)

    @abstractmethod
    def _run(self, data_ids, dts_scores, logger, **params):
        raise RuntimeError('This function must be implemented in a child class')


class SaveScoresCSV(ResultsOrganization):
    def __init__(self):
        super(SaveScoresCSV, self).__init__('save_scores')

    def _run(self, data_ids, dts_scores, logger, out_dir):
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
            logger.text(f'Created output directory: {out_dir}')

        out_file = open(f'{out_dir}/selection.csv', 'w')
        scores = np.argsort(dts_scores)[::-1]

        for ind, s_ind in enumerate(scores):
            out_file.write(f'{ind}, {s_ind}, {data_ids[s_ind]}, '
                           f'{dts_scores[s_ind]}\n')

        out_file.close()


save_scores_csv = SaveScoresCSV()
register_org_method(save_scores_csv)


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
