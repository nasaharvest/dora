# Results organization module
#
# Steven Lu
# June 3, 2021

import os
import numpy as np
from six import add_metaclass
from abc import ABCMeta, abstractmethod
import matplotlib.pyplot as plt


METHOD_POOL = []


def get_res_org_method(method_name):
    ret_method = None
    for org_method in METHOD_POOL:
        if org_method.can_run(method_name):
            ret_method = org_method
            break

    if ret_method is None:
        raise RuntimeError(f'No results organization method can be used for '
                           f'the method {method_name} specified in the config '
                           f'file')

    return ret_method


def register_org_method(org_method):
    if isinstance(org_method, ResultsOrganization):
        METHOD_POOL.append(org_method)
    else:
        raise RuntimeError('Invalid results organization method cannot be '
                           'registered in the pool. Valid results organization '
                           'method must implement the base class '
                           'ResultsOrganization.')


@add_metaclass(ABCMeta)
class ResultsOrganization(object):
    def __init__(self, method_name):
        self.method_name = method_name

    def can_run(self, loader_name):
        if loader_name.lower() == self.method_name.lower():
            return True
        else:
            return False

    def run(self, data_ids, dts_scores, logger, alg_name, **params):
        self._run(data_ids, dts_scores, logger, alg_name, **params)

    @abstractmethod
    def _run(self, data_ids, dts_scores, logger, **params):
        raise RuntimeError('This function must be implemented in a child class')


class SaveScoresCSV(ResultsOrganization):
    def __init__(self):
        super(SaveScoresCSV, self).__init__('save_scores')

    def _run(self, data_ids, dts_scores, logger, alg_name, out_dir):
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
            logger.text(f'Created output directory: {out_dir}')

        out_file = open(f'{out_dir}/{alg_name}/selection.csv', 'w')
        scores = np.argsort(dts_scores)[::-1]
        
        for ind, s_ind in enumerate(scores):
            out_file.write(f'{ind}, {s_ind}, {data_ids[s_ind]}, '
                           f'{dts_scores[s_ind]}\n')

        out_file.close()

class SaveComparisonPlot(ResultsOrganization):
    def __init__(self):
        super(SaveComparisonPlot, self).__init__('comparison_plot')

    def _run(self, data_ids, dts_scores, logger, alg_name, validation_dir, out_dir):
        # Outliers will be 1s and inliers will be 0s. 
        labels = self._get_validation_labels(validation_dir)
        scores = np.argsort(dts_scores)[::-1]

        x = list(range(1, len(scores)+1))
        y = []
        numOutliers = 0
        
        for i in range(len(scores)):
            if(labels[scores[i]] == 1):
                numOutliers += 1
            y.append(numOutliers)

        fig, axes = plt.subplots()
        
        plt.plot(x, y, label=alg_name)
        plt.title('Correct Outliers vs Selected Outliers')
        plt.xlabel('Number of Outliers Selected')
        plt.ylabel('Number of True Outliers')
        plt.legend()
        axes.set_xlim(1, y[-1])
        axes.set_ylim(1, y[-1])
        plt.savefig(f'{out_dir}/comparison_plot_{alg_name}.png')

    def _get_validation_labels(self, validation_dir):
        with open(validation_dir, 'r') as f:
            text = f.read().split("\n")[:-1]
            
        labels = {}
        for i in text:
            line = i.split(",")
            labels[int(line[0])] = int(line[1])

        return labels
        


save_scores_csv = SaveScoresCSV()
register_org_method(save_scores_csv)

save_comparison_plot = SaveComparisonPlot()
register_org_method(save_comparison_plot)


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
