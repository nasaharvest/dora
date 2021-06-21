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

import numpy as np
from dora_exp_pipeline.outlier_detection import OutlierDetection


class RandomOutlierDetection(OutlierDetection):
    def __init__(self):
        super(RandomOutlierDetection, self).__init__('random')

    def _random(self, data_to_fit, data_to_score, data_to_score_ids, seed):
        # Random ranking
        indices = list(range(0, data_to_score.shape[0]))
        random_state = np.random.RandomState(seed)
        random_state.shuffle(indices)

        dts_ids = []
        for ind in indices:
            dts_ids.append(data_to_score_ids[ind])

        # This interprets the indices as the scores so when
        # the scores are sorted later they will have the
        # random order.
        return {
            'scores': list(np.zeros(data_to_score.shape[0], dtype=float)),
            'sel_ind': indices,
            'dts_ids': dts_ids
        }

    def _rank_internal(self, data_to_fit, data_to_score, seed):
        return self._random(data_to_fit, data_to_score, seed)


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
