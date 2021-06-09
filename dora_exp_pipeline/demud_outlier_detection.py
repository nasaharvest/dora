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
        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        res = {}
        res['sels'] = []
        res['scores'] = []

        # Initialize DEMUD model variables
        X = data
        U = [] # principal components
        S = np.array([1])
        mu = [] # data mean
        n = 0 # number selected

        # If initial data set is provided, use it to initialize the model
        if len(initdata) > 0:
            U, S, mu, n = DEMUDOutlierDetection.update_model(
                initdata, U, S, k, n=0, mu=[])
        else:
            # Otherwise do full SVD on data
            U, S, mu, n = DEMUDOutlierDetection.update_model(
                X, U, S, k, n=0, mu=[])

        # Iterative ranking and selection
        n_items = X.shape[1]
        orig_ind = np.arange(n_items)
        seen = initdata
        for i in range(nsel):
            # Select item with largest reconstruction error
            ind, r, score, scores = DEMUDOutlierDetection.select_next(
                X, U, mu)
            res['sels'] += [orig_ind[ind]]
            res['scores'] += [score]

            # Update model with new selection
            x = X[:, ind]
            if len(seen) == 0:
                seen = x.reshape(-1, 1)
            else:
                seen = np.hstack((seen, x.reshape(-1, 1)))
            U, S, mu, n = DEMUDOutlierDetection.update_model(
                seen, U, S, k, n, mu)

            # Remove this item from X
            keep = list(range(X.shape[1]))
            keep.remove(ind)
            X = X[:, keep]
            orig_ind = orig_ind[keep]

        return res


    @classmethod
    def update_model(DEMUDOutlierDetection, X, U, S, k, n, mu):
        """update_model(X, U, S, k, n, mu):

        Update SVD model U,S (dimensionality k)
        by either adding items in X to it,
        or regenerating a new model from X,
        assuming U already models n items with mean mu.
        Technically we should have V as well, but it's not needed.

        Return new U, S, mu, n, and percent variances.
        """

        return U, S, mu, n


    @classmethod
    def select_next(DEMUDOutlierDetection, X, U, mu):
        """select_next(X, U, mu)

        Select the next most-interesting (max recon. error) item in X,
        given model U, singular values S, 
        and mean mu for uninteresting items.

        Return the index of the selected item, its reconstruction,
        its reconstruction score, and all items' reconstruction scores.
        """

        return 0, X[:, 0], 0, np.zeros((len(X), 1))
    

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
