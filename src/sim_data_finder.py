# This script provides functionalities to find data of interest. See copyright
# notice at the end.
#
# Steven Lu, June 26 2020

import os
import glob
import json
import pyaegis
from six import add_metaclass
from abc import ABCMeta, abstractmethod


# The pool of data finders. Data finders can be registered into this pool using
# register_data_finder() function.
FINDER_POOL = []


# Function to retrieve a data finder
def get_data_finder_by_name(finder_name):
    ret_data_finder = None
    for data_finder in FINDER_POOL:
        if data_finder.can_find(finder_name):
            ret_data_finder = data_finder
            break

    if ret_data_finder is None:
        raise RuntimeError('No data finder can be used for the type data '
                           'specified in the configuration file: %s' %
                           finder_name)

    return ret_data_finder


# Function to register a data finder object into the data finder pool
# Note only valid data finder object can be registered. Valid data finder
# objects are the ones who implemented the base class DataFinder.
def register_data_finder(data_finder):
    if isinstance(data_finder, DataFinder):
        FINDER_POOL.append(data_finder)
    else:
        raise RuntimeError('Invalid data finder cannot be registered in the '
                           'data finder pool. Valid data finder must implement'
                           'the base class DataFinder')


@add_metaclass(ABCMeta)
class DataFinder(object):
    def __init__(self, finder_name):
        self.finder_name = finder_name

    def can_find(self, finder_name):
        if finder_name.lower() == self.finder_name.lower():
            return True
        else:
            return False

    # This is the function callers should use to get a list of all data between
    # start_sol and end_sol.
    def get_data_files(self, data_root, start_sol, end_sol, test_image=None,
                       source_file=None):
        if not os.path.exists(data_root):
            raise RuntimeError('Data root directory not found: %s' %
                               os.path.abspath(data_root))

        if start_sol > end_sol:
            raise RuntimeError('start sol (%d) must be smaller than end sol '
                               '(%d)' % (start_sol, end_sol))

        data_list = self._retrieve_data_files(data_root, start_sol, end_sol,
                                              test_image, source_file)

        if not isinstance(data_list, list):
            raise RuntimeError('The return type of the data finder named %s '
                               'must be a Python list.' % self.finder_name)

        return data_list

    # Sub-class must implement this function to retrieve all data between
    # start_sol and end_sol (inclusive). This function must return a 1d Python
    # list. Data in end_sol should be included.
    # See MSLNavcamEDRFullRasterFinder class as an example implementation.
    @abstractmethod
    def _retrieve_data_files(self, data_root, start_sol, end_sol, test_image,
                             source_file):
        raise RuntimeError('Development error. This function should never be '
                           'called directly.')


# Class for MSL Navcam EDR full raster data finder.
# Note this class is implemented using the following assumptions:
# 1. Official naming convention of Navcam data described in the MSL Software
#    Interface Specification.
# https://pds-imaging.jpl.nasa.gov/data/msl/MSLNAV_0XXX/DOCUMENT/MSL_CAMERA_SIS_latest.PDF
# 2. MSL Navcam data archive structure at the PDS Imaging Node.
class MSLNavcamEDRFullRasterFinder(DataFinder):
    def __init__(self):
        super(MSLNavcamEDRFullRasterFinder, self).__init__('navcam')

    def _retrieve_data_files(self, data_root, start_sol, end_sol, test_image,
                             aegis_file):
        data_dir = os.path.join(data_root, 'MSLNAV_0XXX/DATA/')
        if not os.path.exists(data_dir):
            raise RuntimeError('MSL Navcam EDR data directory not found: %s' %
                               os.path.abspath(data_dir))

        if not os.path.exists(aegis_file):
            raise RuntimeError('AEGIS file not found: %s' %
                               os.path.abspath(aegis_file))

        # +1 to include data in end_sol
        sol_range = range(start_sol, end_sol + 1)
        data_list = []

        with open(aegis_file, 'r') as f:
            cand_by_sols = json.load(f)

        for candidate in cand_by_sols:
            # Make sure the fields we need to use exist in the aegis file
            for k in ['sol', 'navcam_source_id', 'filters', 'targets']:
                if k not in candidate.keys():
                    raise RuntimeError(
                        'The field %s not found in one of the candidate in '
                        'the aegis file.' % k
                    )

            sol = int(candidate['sol'])
            # Skip sols outside of the range
            if sol not in sol_range:
                continue

            navcam_id = candidate['navcam_source_id']
            if test_image is not None and navcam_id != test_image:
                continue

            filters = [pyaegis.AegisFilterProfile(**f)
                       for f in candidate['filters']]
            targets = []
            for target in candidate['targets']:
                if 'filtered' in target.keys() and not target['filtered'] > 0:
                    targets.append(target)
                elif 'filtered' not in target.keys():
                    targets.append(target)
            
            filt_targets = filter(lambda t: all(f.apply(t) for f in filters),
                                  targets)

            sol_dir = os.path.join(data_dir, 'SOL%05d' % sol)
            sol_file = os.path.join(sol_dir, '%s.IMG' % navcam_id)

            # If the version of the file provided in the aegis file doesn't
            # exist in the PDS archive, then we will first see if there are
            # other versions of the file exists. If there are multiple
            # files exist, then we pick the one with the highest version.
            # If nothing exists, a runtime error will be thrown.
            if not os.path.exists(sol_file):
                other_versions = glob.glob('%s/%s*.IMG' % (sol_dir,
                                                           navcam_id[:-1]))
                if len(other_versions) == 0:
                    raise RuntimeError('Navcam %s not found.' % navcam_id)
                elif len(other_versions) == 1:
                    sol_file = other_versions[0]
                else:
                    other_versions.sort()
                    sol_file = other_versions[-1]

            data_list.append({
                'sol': sol,
                'file_path': sol_file,
                'targets': filt_targets
            })

        return data_list


# Register the MSL Navcam EDR full raster finder into data finder's pool
msl_navcam_edr_full_raster_finder = MSLNavcamEDRFullRasterFinder()
register_data_finder(msl_navcam_edr_full_raster_finder)


# Class for MSL Mastcam EDR data finder
class MSLMastcamEDRFinder(DataFinder):
    def __init__(self):
        super(MSLMastcamEDRFinder, self).__init__('mastcam')

    def _retrieve_data_files(self, data_root, start_sol, end_sol, test_image,
                             aegis_file):
        if not os.path.exists(data_root):
            raise RuntimeError('MSL Mastcam EDR data directory not found: %s' %
                               os.path.exists(data_root))

        if not os.path.exists(aegis_file):
            raise RuntimeError('Mastcam AEGIS file not found: %s' %
                               os.path.abspath(aegis_file))

        # +1 to include data in end_sol
        sol_range = range(start_sol, end_sol + 1)
        data_list = []

        with open(aegis_file, 'r') as f:
            cand_by_sols = json.load(f)

        for candidate in cand_by_sols:
            # Make sure the fields we need to use exist in the aegis file
            for k in ['sol', 'mastcam_source_id', 'filters', 'targets']:
                if k not in candidate.keys():
                    raise RuntimeError(
                        'The field %s not found in one of the candidate in '
                        'the aegis file.' % k
                    )

            sol = int(candidate['sol'])
            if sol not in sol_range:
                continue

            mastcam_id = candidate['mastcam_source_id']
            if test_image is not None and mastcam_id != test_image:
                continue

            filters = [pyaegis.AegisFilterProfile(**f)
                       for f in candidate['filters']]

            targets = []
            for target in candidate['targets']:
                if 'filtered' in target.keys() and not target['filtered'] > 0:
                    targets.append(target)
                elif 'filtered' not in target.keys():
                    targets.append(target)

            filt_targets = filter(lambda t: all(f.apply(t) for f in filters),
                                  targets)



            sol_dir = os.path.join(data_root, 'sol%04d' % sol)
            sol_file = os.path.join(sol_dir, '%s.png' % mastcam_id)

            data_list.append({
                'sol': sol,
                'file_path': sol_file,
                'targets': filt_targets
            })

        return data_list


# Register the MSL Mastcam EDR finder into data finder's pool
msl_mastcam_edr_finder = MSLMastcamEDRFinder()
register_data_finder(msl_mastcam_edr_finder)


# Class for MSL Mastcam multispectral EDR data finder
class MSLMastcamMultispectralEDRFinder(DataFinder):
    def __init__(self):
        super(MSLMastcamMultispectralEDRFinder, self).__init__('mastcam '
                                                               'multispectral')

    def _retrieve_data_files(self, data_root, start_sol, end_sol, test_image,
                             source_file):
        if not os.path.exists(data_root):
            raise RuntimeError('MSL Mastcam multispectral EDR data directory '
                               'not found: %s' % os.path.abspath(data_root))

        if not os.path.exists(source_file):
            raise RuntimeError('MSL Mastcam multispectral json source file not '
                               'found: %s' % os.path.abspath(source_file))

        # +1 to include data in end_sol
        sol_range = range(start_sol, end_sol + 1)
        data_list = []

        with open(source_file, 'r') as f:
            cand_by_sols = json.load(f)

        for candidate in cand_by_sols:
            # Make sure the fields we need to use exist in the aegis file
            for k in ['sol', 'mastcam_source_id', 'filters', 'targets']:
                if k not in candidate.keys():
                    raise RuntimeError(
                        'The field %s not found in one of the candidate in '
                        'the json file.' % k
                    )

            filters = [pyaegis.AegisFilterProfile(**f)
                       for f in candidate['filters']]
            sol = int(candidate['sol'])
            if sol not in sol_range:
                continue

            # The mastcam source id in the json file is the id for the RGB
            # image. Here we would take the first 13 characters as the unique
            # identifier to find the single band images.
            mastcam_id = candidate['mastcam_source_id']
            mastcam_id = mastcam_id[:13]
            if test_image is not None and mastcam_id != test_image:
                continue

            targets = []
            for target in candidate['targets']:
                if 'filtered' in target.keys() and not target['filtered'] > 0:
                    targets.append(target)
                elif 'filtered' not in target.keys():
                    targets.append(target)

            filt_targets = filter(lambda t: all(f.apply(t) for f in filters),
                                  targets)

            sol_dir = os.path.join(data_root, 'sol%04d' % sol)
            sol_files = glob.glob('%s/%s*D01.png' % (sol_dir, mastcam_id))
            sol_files.sort()

            data_list.append({
                'sol': sol,
                'file_path': sol_files,
                'targets': filt_targets
            })

        return data_list


# Register the MSL Mastcam multispectral EDR finder into the data finder's pool
msl_mastcam_multispectral_edr_finder = MSLMastcamMultispectralEDRFinder()
register_data_finder(msl_mastcam_multispectral_edr_finder)


# Class for MSL Mastcam grayscale EDR data finder
class MSLMastcamGrayscaleEDRFinder(MSLMastcamEDRFinder):
    def __init__(self):
        super(MSLMastcamEDRFinder, self).__init__('mastcam grayscale')


# Register the MSL Mastcam grayscale EDR finder into the data finder's pool
msl_mastcam_grayscale_finder = MSLMastcamGrayscaleEDRFinder()
register_data_finder(msl_mastcam_grayscale_finder)


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
