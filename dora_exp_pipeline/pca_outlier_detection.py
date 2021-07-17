import numpy as np
from copy import deepcopy
from sklearn.decomposition import PCA
from dora_exp_pipeline.outlier_detection import OutlierDetection


class PCAOutlierDetection(OutlierDetection):
    def __init__(self):
        super(PCAOutlierDetection, self).__init__('pca')

    def _rank_internal(self, data_to_fit, data_to_score, data_to_score_ids,
                       top_n, seed, k):
        if data_to_fit is None:
            data_to_fit = deepcopy(data_to_score)

        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        # Check that the number of PCA components <= number of features
        if k > data_to_fit.shape[1]:
            raise RuntimeError(f'The number of principal components (k = {k}) '
                               f'must be < number of features '
                               f'({data_to_fit.shape[1]})')

        # Rank targets
        scores = train_and_run_PCA(data_to_fit, data_to_score, k, seed)
        selection_indices = np.argsort(scores)[::-1]

        results = dict()
        results.setdefault('scores', list())
        results.setdefault('sel_ind', list())
        results.setdefault('dts_ids', list())
        for ind in selection_indices[:top_n]:
            results['scores'].append(scores[ind])
            results['sel_ind'].append(ind)
            results['dts_ids'].append(data_to_score_ids[ind])

        return results


def train_and_run_PCA(train, test, k, seed):
    # initialize the PCA model (deterministically)
    pca = PCA(n_components=k, random_state=seed)

    # fit the PCA model
    pca.fit(train)

    return compute_score(test, pca)


def compute_score(images, pca):
    scores = np.ndarray(images.shape[0])

    for i in range(images.shape[0]):
        # compute the L2 norm between input and reconstruction
        recon = pca.inverse_transform(pca.transform([images[i]]))
        sub = images[i] - recon
        scores[i] = np.linalg.norm(sub, ord=2, axis=1)

    return scores


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
