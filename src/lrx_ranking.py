#!/usr/bin/env python
# See copyright notice at the end.
#
# Author (TODO)
# Date created (TODO)
#
# Modification history:
# Steven Lu, May 28, 2020, refactored the code to extract common functionalities
#                          out to util.py.

import sys
import numpy as np
from ranking import Ranking
from util import load_images
from util import DEFAULT_DATA_DIR
from util import get_image_file_list


class LocalRXRanking(Ranking):
    def __init__(self):
        super(LocalRXRanking, self).__init__('lrx')

    # prior_dir is ignored for this algorithm
    def _rank_internal(self, data_dir, prior_dir, start_sol, end_sol, seed,
                       inner_window, outer_window, bands=1):

        # catalog available images to read in
        f_images_tst = get_image_file_list(data_dir, start_sol, end_sol)

        # get the image data
        data_tst = load_images(data_dir, f_images_tst)

        # rank targets
        return self._rank_targets(data_tst, f_images_tst, inner_window,
                                  outer_window, bands, enable_explanation=False)

    def _simulate_rank_internal(self, files, rank_data, prior_data, config,
                                seed, inner_window, outer_window, bands=1):
        if inner_window > outer_window:
            raise RuntimeError('inner_window cannot be bigger than outer_window'
                               ' for %s method.' % self._ranking_alg_name)

        # LRX can only be used with `flattened_pixel_values` feature. In
        # addition, `width` and `height` parameters must be supplied and their
        # values must be the same.
        if 'one_dimensional' not in config.features.keys():
            raise RuntimeError(
                'Invalid feature dimensionality for LRX. LRX is currently '
                'implemented only for `one_dimensional` feature')
        features_1d = config.features['one_dimensional']
        features_keys = features_1d.keys()
        if 'flattened_pixel_values' not in features_keys or \
                        len(features_keys) > 1:
            raise RuntimeError(
                'LRX must be used with `flattened_pixel_values` feature alone.'
            )
        alg_params = features_1d['flattened_pixel_values'].keys()
        if 'width' not in alg_params:
            raise RuntimeError(
                'width parameter in flattened_pixel_values group must be '
                'supplied for LRX ranking method'
            )
        if 'height' not in alg_params:
            raise RuntimeError(
                'height parameter in flattened_pixel_values group must be '
                'supplied for LRX ranking method'
            )
        resize_width = features_1d['flattened_pixel_values']['width']
        resize_height = features_1d['flattened_pixel_values']['height']
        if resize_width != resize_height:
            raise RuntimeError(
                'width and height must be the same. LRX works only with square '
                'images'
            )

        # Rank targets
        return self._rank_targets(rank_data, files, inner_window, outer_window,
                                  bands, config.enable_explanation)

    def _rank_targets(self, data_test, files, inner_window, outer_window, bands,
                      enable_explanation=False):
        # get LRX scores and visualization (pixel-wise scores), then sort in
        # descending order
        scores_tst, vis = get_LRX_scores(data_test, inner_window, outer_window,
                                         bands)
        indices_srt_by_score = np.argsort(scores_tst)[::-1]

        # prepare results to return
        results = dict()
        results.setdefault('ind', range(indices_srt_by_score.shape[0]))
        results.setdefault('sel_ind', [])
        results.setdefault('img_id', [])
        results.setdefault('scores', [])
        results.setdefault('explanations', [])
        for i, idx in enumerate(indices_srt_by_score):
            results['sel_ind'].append(idx)
            results['img_id'].append(files[idx])
            results['scores'].append(scores_tst[idx])

            if enable_explanation:
                results['explanations'].append(
                    np.interp(vis[idx], (vis[idx].min(), vis[idx].max()),
                              (0, 255))
                )

        results_file_suffix = 'i%d-o%d-b%d' % (inner_window, outer_window,
                                               bands)

        return results, results_file_suffix


# Local RX (LRX)
def get_LRX_scores(images, w_inner, w_outer, bands):
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
    return np.mean(scores[:,s:-s,s:-s], axis=(1, 2)), scores


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


def start(start_sol, end_sol, data_dir, out_dir, inner_window, outer_window,
          bands, seed):
    lrx_params = {
        'inner_window': inner_window,
        'outer_window': outer_window,
        'bands': bands
    }

    lrx_ranking = LocalRXRanking()

    try:
        lrx_ranking.run(data_dir, start_sol, end_sol, out_dir, seed,
                        **lrx_params)
    except RuntimeError as e:
        print e
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Local RX ranking algorithm')
    parser.add_argument('-s', '--start_sol', type=int, default=1343,
                        help='minimum (starting) sol (default 1343)')
    parser.add_argument('-e', '--end_sol', type=int, default=1343,
                        help='maximum (ending) sol (default 1343)')
    parser.add_argument('-d', '--data_dir', default=DEFAULT_DATA_DIR,
                        help='target image data directory (default: %(default)s)')
    parser.add_argument('-o', '--out_dir', default='.',
                        help='output directory (default: .)')
    parser.add_argument('-i', '--inner_window', type=int, default=3,
                        help='size of inner window (default 3)')
    parser.add_argument('-u', '--outer_window', type=int, default=5,
                        help='size of outer window (default 5)')
    parser.add_argument('-b', '--bands', type=int, default=1, 
                        help='number of bands in input images (default 1)')
    parser.add_argument('--seed', type=int, default=1234,
                        help='Integer used to seed the random generator. This '
                             'argument is not used in this script.')
    args = parser.parse_args()
    start(**vars(args))


if __name__ == '__main__':
    main()


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