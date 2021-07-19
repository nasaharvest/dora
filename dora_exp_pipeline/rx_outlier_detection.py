#!/usr/bin/env python
# Given a sol range, read in all AEGIS target images and rank them by novelty
# using Reed-Xiaoli (RX) algorithm. Optionally, use a range of prior sol's
# targets to initialize the RX model. See copyright notice at the end.
#
# Author (TODO)
# Date Created (TODO)
#
# Modification history:
# Steven Lu, May 13, 2020, refactored the code to extract common functionalities
#                          out to util.py.

import warnings
import numpy as np
from copy import deepcopy
from dora_exp_pipeline.outlier_detection import OutlierDetection


class RXOutlierDetection(OutlierDetection):
    def __init__(self):
        super(RXOutlierDetection, self).__init__('rx')

    def _rank_internal(self, data_to_fit, data_to_score, data_to_score_ids,
                       top_n, seed):
        if data_to_fit is None:
            data_to_fit = deepcopy(data_to_score)

        scores = get_RX_scores(data_to_fit, data_to_score)
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


def compute_bg(train_images):
    # compute mean image
    mu = np.mean(train_images, axis=0)
    # compute the covariance matrix for training images
    if train_images.shape[0] < train_images.shape[1]:
        warnings.warn('There are fewer image samples than features. '
                      'Covariance matrix may be singular.')
    cov = np.cov(np.transpose(train_images))
    # If covariance matrix is 1 x 1, reshape to a 2-d array
    if len(cov.shape) == 0:
        cov = np.array([[cov]])
    cov = np.linalg.inv(cov)

    return mu, cov


def compute_score(images, mu, cov):
    rows, cols = images.shape
    scores = np.ndarray(rows)

    for i in range(rows):
        # compute the L2 norm between input and reconstruction
        sub = images[i] - mu
        rx_score = np.dot(np.dot(sub, cov), sub.T)
        scores[i] = rx_score

    if np.any(scores < 0):
        warnings.warn('Some RX scores are negative.')

    return scores


def get_RX_scores(train, test):
    mu, cov = compute_bg(train)

    return compute_score(test, mu, cov)


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
