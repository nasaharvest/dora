#!/usr/bin/env python
# Apply DEMUD to rank items by reconstruction error
# using an incrementally growing model of previously selected items.
# See copyright notice at the end.
#
# Kiri Wagstaff
# May 25, 2021

import numpy as np
from dora_exp_pipeline.outlier_detection import OutlierDetection


class DEMUDOutlierDetection(OutlierDetection):
    def __init__(self):
        super(DEMUDOutlierDetection, self).__init__('demud')

    def _rank_internal(self, data_to_fit, data_to_score, data_to_score_ids,
                       top_n, seed, k):
        """
        >>> data_to_score = np.array([[1,2,3],[4,5,6],[7,8,9]])
        >>> data_to_fit = np.array([[0,7,2],[3,9,3],[4,7,4]])
        >>> #data_to_fit = np.array(())
        >>> k = 2
        >>> top_n = 2

        # --- Run local DEMUD
        >>> scores, sel_ind = DEMUDOutlierDetection.demud(data=data_to_score.T,\
                                                      initdata=data_to_fit.T,\
                                                      k=k, nsel=top_n)

        # If cosmic_demud is not installed, point to a checkout:
        >>> #import sys
        >>> #sys.path.append('/home/wkiri/Research/COSMIC/'\
                             'COSMIC_DEMUD/cosmic_demud')
        >>> #from demud import demud as cosmic_demud
        >>> #from dataset import Dataset

        # if cosmic_demud is installed in your environment:
        >>> import cosmic_demud
        >>> from cosmic_demud.demud import demud as cosmic_demud
        --- Loaded package version information ---
        >>> from cosmic_demud.dataset import Dataset

        # --- compare to COSMIC DEMUD ---
        # Create a DEMUD data set
        >>> ds = Dataset('', name='novelty')
        >>> ds.data = data_to_score.T
        >>> n_items = data_to_score.shape[0]
        >>> for i in range(n_items): ds.labels.append(str(i))

        >>> if data_to_fit is not None: \
               ds.initdata = np.array(data_to_fit).T

        # Suppress stdout for DEMUD calls
        >>> stdout_ = sys.stdout
        >>> sys.stdout = open('/dev/null', 'w')

        # Run DEMUD and get selections back
        # 'sels': list of item indices, in order of selection
        >>> demud_results = cosmic_demud(\
            ds, k=k, nsel=top_n, inititem=-1, plotresults=False\
        )
        >>> sys.stdout = stdout_

        >>> print(sel_ind == demud_results['sels'])
        True
        >>> print(scores == demud_results['scores'])
        True

        # print(sel_ind == demud_results['sels'], \
                sel_ind, demud_results['sels'])
        # print(scores == demud_results['scores'], \
                scores, demud_results['scores'])
        """

        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        if data_to_fit is None:
            data_to_fit = np.array(())

        # Note: DEMUD expects data in d x n order
        scores, sel_ind = DEMUDOutlierDetection.demud(data=data_to_score.T,
                                                      initdata=data_to_fit.T,
                                                      k=k, nsel=top_n)

        dts_ids = list()
        for ind in sel_ind:
            dts_ids.append(data_to_score_ids[ind])

        return {
            'scores': scores,
            'sel_ind': sel_ind,
            'dts_ids': dts_ids
        }

    # Simplified DEMUD algorithm:
    # Specify data as numpy array (d x n), initdata (d x n2) can be [],
    # k >= 1, nsel = number of items in 'data' to rank.
    # Note: does not support other initialization methods.
    # Returns a dictionary with:
    #   'sels' (data indices in descending score order)
    #   'scores' (score for each data item in original order)
    @classmethod
    def demud(cls, data, initdata, k, nsel):
        """
        >>> data = np.array([[0, 0], [-1, 1]]).T
        >>> demud_res = DEMUDOutlierDetection.demud(data, np.array([]), \
                                                    k=1, nsel=2)
        >>> demud_res[1]  # selections
        [1, 0]
        >>> demud_res[0]  # scores
        [1.6023737137301802e-31, 1.0]

        Example from CIF benchmarking tests - with prior data
        >>> initdata = np.array([[1, 1], [-1, -1]]).T
        >>> demud_res = DEMUDOutlierDetection.demud(data, initdata, k=1, nsel=2)
        >>> demud_res[1]
        [1, 0]
        >>> demud_res[0]
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
        U = []   # principal components
        S = np.array([1])
        mu = []  # data mean
        n = 0    # number selected

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
            ind, _, score, _ = DEMUDOutlierDetection.select_next(X, U, mu)
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

        # return res
        return res['scores'], res['sels']

    @classmethod
    def update_model(cls, X, U, S, k, n, mu):
        """update_model(X, U, S, k, n, mu):

        Update SVD model U, S (dimensionality k)
        by either adding items in X to it,
        or regenerating a new model from X,
        assuming U already models n items with mean mu.
        Technically we should have V as well, but it's not needed.

        Return new U, S, mu, n.
        """

        # Check arguments
        if len(X) == 0:
            print('Error: No data in X.')
            return None, None, None, -1

        # If there is no previous U, and we just got a single item in X,
        # then create a U the same size, first value 1 (rest 0),
        # and return it with mu.
        if len(U) == 0 and X.shape[1] == 1:
            mu = X
            U = np.zeros_like(mu)
            U[0] = 1
            S = np.array([0])
            n = 1
            return U, S, mu, n

        # Do a full SVD of mean-subtracted X
        mu = np.mean(X, axis=1).reshape(-1, 1)
        X = X - mu
        U, S, _ = np.linalg.svd(X, full_matrices=False)

        # Update n to number of new items in X
        n = X.shape[1]

        # Keep only the first k components
        S = S[0:k]
        U = U[:, 0:k]

        return U, S, mu, n

    @classmethod
    def select_next(cls, X, U, mu):
        """select_next(X, U, mu)

        Select the next most-interesting (max recon. error) item in X,
        given model U, singular values S,
        and mean mu for uninteresting items.

        Return the index of the selected item, its reconstruction,
        its reconstruction score, and all items' reconstruction scores.
        """

        # Check arguments
        if len(U) == 0:
            print('Empty DEMUD model: selecting item 0')
            return 0, X[:, 0], 0.0, np.zeros((len(X, )))

        if X.shape[1] < 1 or len(mu) == 0:
            print('Error: no data in X and/or mu')
            return None, None, -1, []

        if X.shape[0] != U.shape[0] or X.shape[0] != mu.shape[0]:
            print('Mismatch in dimensions; must have X mxn, U mxk, mu mx1.')
            return None, None, -1, []

        # Compute the score and projection for each item
        (scores, reproj) = DEMUDOutlierDetection.score_items(X, U, mu)

        # Select and return item with max reconstruction error
        m = scores.argmax()

        return m, reproj[:, m], scores[m], scores

    @classmethod
    def score_items(cls, X, U, mu):
        """score_items(X, U, mu)
        Calculate the score (reconstruction error) for every item in X,
        with respect to the SVD model in U and mean mu.

        Return an array of item reconstruction scores and their reprojections.
        """

        # Use U to model and then reconstruct the data in X.
        # 1. Project all data in X into space defined by U,
        #    then reconstruct it.
        # 1a. Subtract the mean and project onto U
        proj = np.dot(U.T, (X - mu))
        # 1b. Reconstruct by projecting back up and adding mean
        reproj = np.dot(U, proj) + mu
        # 1c. Compute the residual
        err = X - reproj

        # 2. Compute reconstruction error
        scores = np.sum(np.array(np.power(err, 2)), axis=0)

        return (scores, reproj)


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
