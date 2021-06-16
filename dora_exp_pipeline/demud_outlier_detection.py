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
from dora_exp_pipeline.outlier_detection import OutlierDetection

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


class DEMUDOutlierDetection(OutlierDetection):
    def __init__(self):
        super(DEMUDOutlierDetection, self).__init__('demud')

    def _demud(self, data_to_fit, data_to_score, k):
        # Create a DEMUD data set
        ds = Dataset('', name='novelty')
        ds.data = data_to_score.T
        n_items = data_to_score.shape[0]
        for i in range(n_items):
            ds.labels.append(i)

        ds.initdata = data_to_fit.T

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

        return demud_results['scores']

    def _rank_internal(self, data_to_fit, data_to_score, seed, k):
        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        return self._demud(data_to_fit, data_to_score, k)


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
