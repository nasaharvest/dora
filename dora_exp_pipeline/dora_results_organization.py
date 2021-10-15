# Results organization module
#
# Steven Lu
# June 3, 2021

import os
import sys
sys.path.append("/Users/youlu/Desktop/dora/work/causal_graph/fges-py")
import SEMScore
import fges
import knowledge
import networkx as nx
from six import add_metaclass
from abc import ABCMeta, abstractmethod
import matplotlib.pyplot as plt
import numpy as np
import rasterio as rio
from sklearn.cluster import KMeans
from sklearn_som.som import SOM

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

    def run(self, data_ids, dts_scores, dts_sels, data_to_fit, data_to_score,
            outlier_alg_name, out_dir, logger, seed, top_n, **params):
        self._run(data_ids, dts_scores, dts_sels, data_to_fit, data_to_score,
                  outlier_alg_name, out_dir, logger, seed, top_n,
                  **params)

    @abstractmethod
    def _run(self, data_ids, dts_scores, dts_sels, data_to_fit, data_to_score,
             outlier_alg_name, logger, seed, top_n, **params):
        raise RuntimeError('This function must be implemented in a child class')


class SaveScoresCSV(ResultsOrganization):
    def __init__(self):
        super(SaveScoresCSV, self).__init__('save_scores')

    def _run(self, data_ids, dts_scores, dts_sels, data_to_fit, data_to_score,
             outlier_alg_name, out_dir, logger, seed, top_n):
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

    def _run(self, data_ids, dts_scores, dts_sels, data_to_fit, data_to_score,
             outlier_alg_name, out_dir, logger, seed, top_n, validation_dir):
        if(not(os.path.exists(out_dir))):
            os.makedirs(out_dir)

        # Outliers will be 1s and inliers will be 0s.
        labels = self._get_validation_labels(validation_dir)

        x = list(range(1, len(dts_sels)+1))
        y = []
        numOutliers = 0

        for i in range(len(dts_sels)):
            if(labels[dts_sels[i]] == 1):
                numOutliers += 1
            y.append(numOutliers)

        fig, axes = plt.subplots()
        area = sum(y)/sum([i for i in range(len(labels))])

        plt.plot(x, y, label="{} (MDR: {:.2f})".format(outlier_alg_name, area))
        plt.plot(x, x, label='Oracle', linestyle='--', color='k')
        plt.title('Known Outliers vs. Selected Outliers')
        plt.xlabel('Number of Outliers Selected')
        plt.ylabel('Number of Known Outliers')
        plt.legend()
        axes.set_xlim(1, x[-1])
        axes.set_ylim(1, y[-1])
        plt.savefig(f'{out_dir}/comparison_plot_{outlier_alg_name}.png')

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

    def _run(self, data_ids, dts_scores, dts_sels, data_to_fit, data_to_score,
             outlier_alg_name, out_dir, logger, seed, top_n, n_clusters,
             causal_graph):
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

        if causal_graph:
            generate_causal_graphs(data_to_fit, data_to_cluster, groups,
                                   out_dir, logger, seed)


kmeans_cluster = KmeansCluster()
register_org_method(kmeans_cluster)


class SOMCluster(ResultsOrganization):
    def __init__(self):
        super(SOMCluster, self).__init__('som')

    def _run(self, data_ids, dts_scores, dts_sels, data_to_fit, data_to_score,
             outlier_alg_name, out_dir, logger, seed, top_n, n_clusters,
             causal_graph):
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
            if logger:
                logger.text(f'Created output directory: {out_dir}')

        out_file = open(f'{out_dir}/SOM-{outlier_alg_name}.csv', 'w')

        data_to_cluster = []
        for dts_ind in dts_sels:
            data_to_cluster.append(data_to_score[dts_ind])
        data_to_cluster = np.array(data_to_cluster, dtype=float)

        som = SOM(m=n_clusters, n=1, dim=len(data_to_cluster[0]))
        som.fit(data_to_cluster)
        groups = som.predict(data_to_cluster)

        for ind, (s_ind, dts_id, group) in enumerate(zip(dts_sels, data_ids,
                                                         groups)):
            out_file.write(f'{ind}, {s_ind}, {dts_id}, {group}\n')

        out_file.close()

        if causal_graph:
            generate_causal_graphs(data_to_fit, data_to_cluster, groups,
                                   out_dir, logger, seed)


som_cluster = SOMCluster()
register_org_method(som_cluster)


class NodeBlock:
    """
    members is a list of node names
    order is a single integer. Low-->high is left-->right
    """
    def __init__(self, members=None, order=None):
        self.members = members
        self.order = order


def generate_causal_graphs(data_to_fit, data_to_cluster, cluster_groups,
                           out_dir, logger, seed):
    causal_tags = ['feature-%d' % col for col in range(len(data_to_cluster[0]))]
    causal_tags = causal_tags + ['cluster']

    if len(causal_tags) > 20:
        if logger:
            logger.text('Can not generate causal graphs for data sets with '
                        'more than 20 features.')

    unique_groups = np.unique(cluster_groups)
    data_to_fit = np.append(data_to_fit, np.zeros((len(data_to_fit), 1)),
                            axis=1)
    for group_label in unique_groups:
        in_group = cluster_groups == group_label
        outliers = data_to_cluster[in_group]
        outliers = np.append(outliers, np.ones((len(outliers), 1)), axis=1)
        data = np.vstack((data_to_fit, outliers))

        # Define knowledge that forbids any connections from features to cluster
        ken = knowledge.Knowledge()
        block1 = ['feature-%d' % col for col in range(len(data_to_cluster[0]))]
        block2 = ['cluster']
        for i, i_label in enumerate(causal_tags):
            for j, j_label in enumerate(causal_tags):
                if (i_label in block1) & (j_label in block2):
                    ken.set_forbidden(i, j)

        # Generate causal graphs
        variables = list(range(len(data[0])))
        score = SEMScore.SEMBicScore(2, dataset=data)
        cs = fges.FGES(variables, score, knowledge=ken)
        cs.search()
        graph = cs.graph

        # Assign names to graph nodes
        node_labels = dict()
        for idx, tag in enumerate(causal_tags):
            node_labels.update({idx: tag})
        graph = nx.relabel_nodes(graph, node_labels)

        # Save graph
        out_file = '%s/causal_graph_cluster_%d' % (out_dir, group_label)
        pos = nx.circular_layout(graph, scale=2, dim=2)
        nx.draw(graph, with_labels=True, pos=pos)

        plt.savefig(out_file)
        plt.clf()


class ReshapeRaster(ResultsOrganization):
    def __init__(self):
        super(ReshapeRaster, self).__init__('reshape_raster')

    def _run(self, data_ids, dts_scores, dts_sels, data_to_fit, data_to_score,
             outlier_alg_name, out_dir, logger, seed, top_n,
             raster_path, data_format, patch_size, colormap):
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
            if logger:
                logger.text(f'Created output directory: {out_dir}')

        # Read the raster metadata
        with rio.open(raster_path) as src:
            height = src.meta['height']
            width = src.meta['width']

        # Reshape scores to original raster dimensions
        if data_format == 'pixels':
            # Check that top_n wasn't specified to be a subset of the pixels
            if top_n != (height*width):
                raise RuntimeError('Cannot use top_n with ReshapeRaster')
            # Reorder scores to be in original index order, not sorted by score
            scores = [s for _, s in sorted(zip(data_ids, dts_scores),
                                           key=lambda pair: pair[0])]
            scores = np.reshape(np.array(scores), [height, width])
        elif data_format == 'patches':
            # Check that top_n wasn't specified to be a subset of the pixels
            if top_n != ((height-(patch_size-1))*(width-(patch_size-1))):
                raise RuntimeError('Cannot use top_n with ReshapeRaster')
            scores = np.zeros([height, width])
            for ex, idx in enumerate(data_ids):
                # get the patch center coordinates
                i, j = idx.split('-')
                i = int(i)
                j = int(j)
                # fill in the score for that index
                scores[i, j] = dts_scores[ex]
        else:
            raise RuntimeError("data_format must be 'pixels' or 'patches'")

        # Save as a preview image
        fig, ax = plt.subplots(1)
        plt.imshow(scores, cmap=colormap)
        plt.savefig(f'{out_dir}/scores_image_{outlier_alg_name}.png')

        # Save as raster
        with rio.open(raster_path) as src:
            profile = src.profile
            profile.update(
                count=1,
                dtype=scores.dtype)
            with rio.open(f'{out_dir}/scores_raster_{outlier_alg_name}.tif',
                          'w',
                          **profile) as dst:
                dst.write(scores, 1)


reshape_raster = ReshapeRaster()
register_org_method(reshape_raster)


class SaveHistogram(ResultsOrganization):
    def __init__(self):
        super(SaveHistogram, self).__init__('histogram')

    def _run(self, data_ids, dts_scores, dts_sels, data_to_fit, data_to_score,
             alg_name, out_dir, logger, seed, bins):
        if(not(os.path.exists(out_dir))):
            os.makedirs(out_dir)

        scores = sorted(dts_scores)
        fig, axs = plt.subplots()
        # numBins = int((scores[-1]-scores[0])/increment)+1
        # print(scores[0], scores[-1], increment, numBins)

        yVals, bins, patches = axs.hist(scores, bins, density=True, alpha=0.5)

        plt.title('Histogram of Anomaly Scores')
        plt.xlabel('Score')
        plt.ylabel('Frequency')
        plt.savefig(f'{out_dir}/histogram_bar_graph-{alg_name}.png')


save_histogram = SaveHistogram()
register_org_method(save_histogram)

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
