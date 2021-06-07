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
import numpy as np
from dora_exp_pipeline.outlier_detection import OutlierDetection

class DEMUDOutlierDetection(OutlierDetection):
    def __init__(self):
        super(DEMUDOutlierDetection, self).__init__('demud')

    def _rank_internal(self, data_to_fit, data_to_score, seed, k):
        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        # nsel=-1 means to rank all items;
        # in a future update, the caller may want to limit this
        return DEMUDOutlierDetection.demud(data=data_to_score,
                                           initdata=data_to_fit,
                                           k=k, nsel=-1)

    # Simplified DEMUD algorithm:
    # Specify data as numpy array (d x n), initdata (d x n2) can be [],
    # k >= 1, nsel = number of items in 'data' to rank.
    # Note: does not support other initialization methods.
    # Returns a dictionary with:
    #   'sels' (data indices in descending score order)
    #   'scores' (score for each data item in original order)
    @classmethod
    def demud(DEMUDOutlierDetection, data, initdata, k, nsel):
        """
        >>> data = np.array([[0, 0], [-1, 1]]).T
        >>> demud_res = DEMUDOutlierDetection.demud(data, np.array([]), k=1, nsel=2)
        >>> demud_res['sels']
        [1, 0]
        >>> demud_res['scores']
        [1.6023737137301802e-31, 1.0]

        Example from CIF benchmarking tests - with prior data
        >>> initdata = np.array([[1, 1], [-1, -1]]).T
        >>> demud_res = DEMUDOutlierDetection.demud(data, initdata, k=1, nsel=2)
        >>> demud_res['sels']
        [1, 0]
        >>> demud_res['scores']
        [2.0, 0.2222222222222222]
        """

        # Check arguments

        res = {}

        # If initial data set is provided, use it to initialize the model
        
        # Otherwise do full SVD on data

        # Select item with largest reconstruction error

        # Iterative ranking and selection
        for i in range(nsel):
            # Select the next item
            # Update scores of remaining items
            pass
        
        res['sels'] = [0]
        res['scores'] = [0]

        return res


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
