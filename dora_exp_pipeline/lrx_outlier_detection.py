#!/usr/bin/env python
# See copyright notice at the end.
#
# Author: Hannah Kerner
# Date created: July 13, 2021
#
# Modification history:
# Steven Lu, July 13, 2021, updated to be compatible with DORA pipeline.

import numpy as np
from dora_exp_pipeline.outlier_detection import OutlierDetection


class LocalRXOutlierDetection(OutlierDetection):
    def __init__(self):
        super(LocalRXOutlierDetection, self).__init__('lrx')

    def _rank_internal(self, data_to_fit, data_to_score, data_to_score_ids,
                       seed, inner_window, outer_window, bands=1):
        if inner_window > outer_window:
            raise RuntimeError('inner_window cannot be bigger than outer_window'
                               ' for %s method.' % self._ranking_alg_name)

        scores, vis = get_LRX_scores(data_to_score, inner_window, outer_window,
                                     bands)

        selection_indices = np.argsort(scores)[::-1]

        results = dict()
        results.setdefault('scores', list())
        results.setdefault('sel_ind', list())
        results.setdefault('dts_ids', list())
        for ind in selection_indices:
            results['scores'].append(scores[ind])
            results['sel_ind'].append(ind)
            results['dts_ids'].append(data_to_score_ids[ind])

        return results


# Local RX (LRX)
def get_LRX_scores(images, w_inner, w_outer, bands):
    # LRX can only be used with `flattened_pixel_values` feature.
    # Images has shape N x M where N is number of images and
    # M is flattened image dimension. Divide by bands to get
    # image dimensions.
    rows, cols = images.shape
    im_height, im_width = int(np.sqrt(cols/bands)), int(np.sqrt(cols/bands))

    # Read in image data from BSQ format (bands, rows, cols),
    # then reshape to (rows, cols, bands)
    images = np.reshape(images, [rows, bands, im_height, im_width])
    images = np.transpose(images, (0, 2, 3, 1))

    # empty array to store the pixel-wise scores
    scores = np.zeros([rows, im_height, im_width])
    s = int(w_outer/2)
    # for each image, compute the LRX score in each pixel
    for idx in range(images.shape[0]):
        im = images[idx]
        for i in range(s, im.shape[0]-s):
            for j in range(s, im.shape[1]-s):
                scores[idx, i, j] = lrx(im[i - s: i + s + 1, j - s: j + s + 1],
                                        w_inner)
    return np.mean(scores[:, s:-s, s:-s], axis=(1, 2)), scores


def lrx(patch, w_in):
    s = patch.shape[0]
    c = int(s / 2)
    w_s = int(w_in / 2)
    mask = np.zeros(patch.shape)
    mask[c - w_s: c + w_s + 1, c - w_s: c + w_s + 1] = 1
    pa = np.ma.masked_array(patch, mask)
    # Check if the number of features (spectral bands) is > 1
    # and reshape to N (samples i.e. pixels) x M (features)
    if len(pa.shape) == 2:
        pa = pa.flatten()
    elif len(pa.shape) == 3:
        pa = np.reshape(pa, [pa.shape[0]*pa.shape[1], pa.shape[2]])
    # Calculate the mean of all pixels in the patch
    mu = np.ma.mean(pa, axis=0)
    cov = np.ma.cov(np.transpose(pa))

    # If covariance matrix is 1 x 1, reshape to a 2-d array
    if len(cov.shape) == 0:
        cov = np.array([[cov]])

    try:
        cov = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        # Duplicate columns will result in singular matrix
        # Return score of 0 in this case
        return 0
    sub = patch[c, c] - mu
    rx_score = np.dot(np.dot(sub, cov), sub.T)
    return rx_score


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
