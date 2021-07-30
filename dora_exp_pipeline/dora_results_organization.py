# Results organization module
#
# Steven Lu
# June 3, 2021

import os
from six import add_metaclass
from abc import ABCMeta, abstractmethod
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans


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

    def run(self, data_ids, dts_scores, dts_sels, data_to_score,
            outlier_alg_name, out_dir, logger, seed, **params):
        self._run(data_ids, dts_scores, dts_sels, data_to_score,
                  outlier_alg_name, out_dir, logger, seed, **params)

    @abstractmethod
    def _run(self, data_ids, dts_scores, dts_sels, data_to_score,
             outlier_alg_name, logger, seed, **params):
        raise RuntimeError('This function must be implemented in a child class')


class SaveScoresCSV(ResultsOrganization):
    def __init__(self):
        super(SaveScoresCSV, self).__init__('save_scores')

    def _run(self, data_ids, dts_scores, dts_sels, data_to_score,
             outlier_alg_name, out_dir, logger, seed):
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
            if logger:
                logger.text(f'Created output directory: {out_dir}')

        out_file = open(f'{out_dir}/selections-{outlier_alg_name}.csv', 'w')

        for ind, (s_ind, dts_id, score) in enumerate(zip(dts_sels, data_ids,
                                                         dts_scores)):
            out_file.write(f'{ind}, {s_ind}, {dts_id}, {score}\n')

        out_file.close()


save_scores_csv = SaveScoresCSV()
register_org_method(save_scores_csv)


class SaveComparisonPlot(ResultsOrganization):
    def __init__(self):
        super(SaveComparisonPlot, self).__init__('comparison_plot')

    def _run(self, data_ids, dts_scores, dts_sels, data_to_score, alg_name,
             out_dir, logger, seed, validation_dir):
        if(not(os.path.exists(out_dir))):
            os.makedirs(out_dir)

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
        index = x.index(y[-1])
        area = np.trapz(y[:index+1], x[:index+1])

        plt.plot(x, y, label=alg_name)
        plt.plot([], [], ' ', label=f'Area: {area}')
        plt.title('Correct Outliers vs Selected Outliers')
        plt.xlabel('Number of Outliers Selected')
        plt.ylabel('Number of True Outliers')
        plt.legend()
        axes.set_xlim(1, x[-1])
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


save_comparison_plot = SaveComparisonPlot()
register_org_method(save_comparison_plot)


class KmeansCluster(ResultsOrganization):
    def __init__(self):
        super(KmeansCluster, self).__init__('kmeans')

    def _run(self, data_ids, dts_scores, dts_sels, data_to_score,
             outlier_alg_name, out_dir, logger, seed, n_clusters):
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
            if logger:
                logger.text(f'Created output directory: {out_dir}')

        out_file = open(f'{out_dir}/kmeans-{outlier_alg_name}.csv', 'w')

        data_to_cluster = []
        for dts_ind in dts_sels:
            data_to_cluster.append(data_to_score[dts_ind])
        data_to_cluster = np.array(data_to_cluster, dtype=float)

        if n_clusters > len(data_to_cluster):
            raise RuntimeError('Kmeans n_clusters is greater than the number '
                               'of items to cluster')

        kmeans = KMeans(n_clusters=n_clusters, random_state=seed)
        groups = kmeans.fit_predict(data_to_cluster)

        for ind, (s_ind, dts_id, group) in enumerate(zip(dts_sels, data_ids,
                                                         groups)):
            out_file.write(f'{ind}, {s_ind}, {dts_id}, {group}\n')

        out_file.close()


kmeans_cluster = KmeansCluster()
register_org_method(kmeans_cluster)


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
