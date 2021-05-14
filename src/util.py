# This script contains common functionalities shared across the ranking
# algorithms. See copyright notice at the end.
#
# Steven Lu
# May 13, 2020

import os
import csv
import shutil
import logging
import numpy as np
from PIL import Image
from src.sim_data_loader import im_crop
from src.sim_feature import extract_1d_features
from src.sim_feature import extract_2d_features

# Define constants
NAVCAM_DATA_DIR = '/proj/cif-novelty/data/navcam-rockster-targets-onboard-64x64/'
MASTCAM_DATA_DIR = '/proj/cif-novelty/data/mcam-test-rockster-targets-64x64/'
DEFAULT_DATA_DIR = NAVCAM_DATA_DIR
NAVCAM_TARGET_FILE = '/proj/cif-novelty/ref/aegis_executions_sol1343-sol2695.json'
MASTCAM_TARGET_FILE = '/proj/cif-novelty/ref/rockster_mcam_executions_sol1343-sol1505.json'
DEFAULT_TARGET_FILE = NAVCAM_TARGET_FILE


# Helper function for retrieving sol in integer format.
# This function expects the filename to be similar to the one below:
# SOL02578NLB_626356326EDR_F0771560CCAM02577M1-78.png
def get_sol_in_filename(filename, start_ind=3, end_ind=8):
    sol_str = filename[start_ind: end_ind]

    return int(sol_str)


# Helper function for determining if a given image should be included in the
# ranking algorithm or not.
def should_include(filename, start_sol, end_sol):
    return filename.endswith('.png') and \
           start_sol <= get_sol_in_filename(filename) <= end_sol


# Get all the files in a directory that match some rules
def get_image_file_list(data_dir, start_sol, end_sol):
    files = [f for f in os.listdir(data_dir)
             if should_include(f, start_sol, end_sol)]
    files.sort()

    if len(files) == 0:
        raise RuntimeError('No files found for sol range %d to %d' %
                           (start_sol, end_sol))

    return files


# Verify the input arguments common to all ranking algorithms (including random)
def verify_common_input_args(data_dir, prior_dir, start_sol, end_sol):
    if not os.path.exists(data_dir):
        raise RuntimeError('data_dir not found: %s' % os.path.abspath(data_dir))

    if not os.path.exists(prior_dir):
        raise RuntimeError('prior_dir not found: %s' % os.path.abspath(prior_dir))

    if start_sol < 0:
        raise RuntimeError('Start sol must be >= 0.')

    if end_sol < 0:
        raise RuntimeError('End sol must be >= 0.')

    if end_sol < start_sol:
        raise RuntimeError('Start sol must be greater than end sol.')


# Loading a directory of images into one float32 type numpy array.
# Note that each image will be flattened before appending to the numpy array.
def load_images(data_dir, files):
    imdata = []

    for f in files:
        file_path = os.path.join(data_dir, f)

        if not os.path.exists(file_path):
            raise RuntimeError('File not found: %s' %
                               os.path.abspath(file_path))

        imfile = Image.open(file_path)
        im = np.array(imfile)
        imfile.close()
        flattened_data = list()

        if len(im.shape) >= 3:
            band = im.shape[2]
            for b in range(band):
                flattened_data.extend(im[:, :, b].flatten().tolist())
        else:
            flattened_data = im.flatten()

        imdata.append(flattened_data)

    return np.array(imdata, dtype=np.float32)


# Remove all files/directories/symlinks in a directory
def remove_all(dir_path):
    for f in os.listdir(dir_path):
        file_path = os.path.join(dir_path, f)

        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


# Save ranking results in the following format:
# selection, index, class, score
def save_results(results, out_dir, file_name='selections.csv', logger=None,
                 enable_explanation=True):
    # Create sub directory
    os.mkdir(out_dir)
    if logger is not None:
        logger.text('Created sub dir: %s' % out_dir)

    # Output file path
    out_file = os.path.join(out_dir, file_name)

    # Save ranking results and the visualizations of explanations
    if enable_explanation:
        # Create explanations directory
        exp_dir = os.path.join(out_dir, 'explanations')
        if os.path.exists(exp_dir):
            shutil.rmtree(exp_dir)
        os.makedirs(exp_dir)

        save_results_with_explanation(results, out_file, exp_dir)
    else:
        save_results_without_explanation(results, out_file)

    if logger is not None:
        logger.text('Ranking results are saved to %s' %
                    os.path.abspath(out_file))


def save_results_with_explanation(results, out_file, exp_dir):
    with open(out_file, 'w') as f:
        f.write('# Selection, Index, Class, Score\n')

        for ind, sel_ind, img_id, score, exp in zip(results['ind'],
                                                    results['sel_ind'],
                                                    results['img_id'],
                                                    results['scores'],
                                                    results['explanations']):
            # Save ranking results
            f.write('%d,%d,%s,%.5e\n' % (ind, sel_ind, img_id, score))

            # Save visualization of explanation
            vis_name = '%d_%d_%s_%.3f.png' % \
                       (ind, sel_ind, os.path.splitext(img_id)[0], score)
            vis_exp = Image.fromarray(exp.astype(np.uint8))
            vis_exp.save('%s/%s' % (exp_dir, vis_name))


def save_results_without_explanation(results, out_file):
    with open(out_file, 'w') as f:
        f.write('# Selection, Index, Class, Score\n')

        for ind, sel_ind, img_id, score in zip(results['ind'],
                                               results['sel_ind'],
                                               results['img_id'],
                                               results['scores']):
            # Save ranking results
            f.write('%d,%d,%s,%.5e\n' % (ind, sel_ind, img_id, score))


def load_crop_features(data_list, data_loader, features, crop_shape,
                       min_crop_area):
    if 'one_dimensional' in features.keys() and \
        'two_dimensional' in features.keys():
        raise RuntimeError('Cannot mix 1d and 2d features together.')

    is_1d_features = True
    if 'two_dimensional' in features.keys():
        is_1d_features = False

    crop_dict = dict()
    crop_dict.setdefault('file_names', [])
    crop_dict.setdefault('data', [])
    for data_dict in data_list:
        # Load image
        im_data = data_loader.load(data_dict['file_path'])

        # Sort targets alphabetically so they match how run_exp.py works
        sorted_targets = sorted(data_dict['targets'],
                                key=lambda t: str(t['id']))
        for target in sorted_targets:
            crop_data = im_crop(im_data, target, crop_shape, min_crop_area)

            # The `crop_data` can be None if it is smaller than minimum
            # cropping area specified in the config file.
            if crop_data is None:
                continue

            if is_1d_features:
                crop_features = extract_1d_features(
                    crop_data, target['attributes'], features['one_dimensional']
                )
            else:
                crop_features = extract_2d_features(
                    crop_data, target['attributes'], features['two_dimensional']
                )

            if isinstance(data_dict['file_path'], list):
                # Special case for MSL Mastcam multispectral data
                base_filename = os.path.basename(data_dict['file_path'][0])
                crop_file_name = '%s-%d' % (base_filename[:13], target['id'])
            else:
                crop_file_name = 'SOL%05d%s-%d' % (
                    data_dict['sol'],
                    os.path.basename(data_dict['file_path']).split('.')[0],
                    target['id']
                )
            crop_dict['file_names'].append(crop_file_name)
            crop_dict['data'].append(crop_features['value'])
    crop_dict['data'] = np.array(crop_dict['data'])

    return crop_dict


def save_features_csv(data_dict, out_file):
    file_names = data_dict['file_names']
    data = data_dict['data'].astype(np.float32)

    results = []
    for file_name, feature_vector in zip(file_names, data):
        results.append([file_name] + feature_vector.tolist())

    with open(out_file, 'w+') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(results)


# Logger
class LogUtil(object):
    def __init__(self, logger_name, log_file, filemode='w'):
        fmt = logging.Formatter(fmt='%(asctime)-15s: %(message)s',
                                datefmt='[%Y-%m-%d %H:%M:%S]')
        handler = logging.FileHandler(log_file, mode=filemode)
        handler.setFormatter(fmt)
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        self.logger = logger

    def text(self, message):
        self.logger.info(message)


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
