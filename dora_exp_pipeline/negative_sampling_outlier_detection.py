#!/usr/bin/env python
# This script implements the negative sampling method proposed in the following
# paper:
# John Sipple, "Interpretable, Multidimensional, Multimodal Anomaly Detection
# with Negative Sampling for Detection of Device Failure", 37th ICML, 2020.
#
# See copyright notice at the end.
#
# Steven Lu
# February 5th, 2021
#

import numpy as np
from copy import deepcopy
from dora_exp_pipeline.outlier_detection import OutlierDetection
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier


class NegativeSamplingOutlierDetection(OutlierDetection):
    def __init__(self):
        super(NegativeSamplingOutlierDetection, self).__init__(
            'negative_sampling')

    def _rank_internal(self, data_to_fit, data_to_score, data_to_score_ids,
                       top_n, seed, percent_increase):
        if percent_increase < 0 or percent_increase > 100:
            raise RuntimeError('percent_increase parameter must be a number '
                               'between 0 and 100.')

        scores = self._rank_targets(data_to_fit, data_to_score,
                                    percent_increase, seed)
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

    def _rank_targets(self, positive_train, data_test, percent_increase, seed):
        if positive_train is None:
            positive_train = deepcopy(data_test)

        random_state = np.random.RandomState(seed)

        # Create negative examples from positive examples
        negative_train = generate_negative_example(positive_train,
                                                   percent_increase,
                                                   random_state)

        # Create labels
        positive_label = np.ones(len(positive_train))
        negative_label = np.zeros(len(negative_train))

        # Concatenate positive and negative examples and labels
        x = np.concatenate((positive_train, negative_train), axis=0)
        y = np.concatenate((positive_label, negative_label), axis=0)

        # Grid search to find best parameters for random forest classifier
        params = [{
            'n_estimators': list(range(50, 101, 10)),
            'max_depth': list(range(2, 7, 1))
        }]

        kfold = KFold(n_splits=5, shuffle=True, random_state=random_state)
        clf = GridSearchCV(RandomForestClassifier(random_state=random_state),
                           params, cv=kfold, scoring='accuracy', n_jobs=1,
                           error_score='raise')
        clf.fit(x, y)
        n_estimators = clf.best_params_['n_estimators']
        max_depth = clf.best_params_['max_depth']

        # Train a random forest classifier with the best parameters found in
        # grid search
        rf_clf = RandomForestClassifier(n_estimators=n_estimators,
                                        max_depth=max_depth,
                                        random_state=random_state)
        rf_clf.fit(x, y)

        # Make predictions for test data
        probs = rf_clf.predict_proba(data_test)

        # Keeping only the probabilities for negative (novel) class, and use
        # them as novelty scores to rank selections
        scores = probs[:, 0].flatten()

        return scores


def generate_negative_example(data_train, percent_increase, random_state):
    rows, cols = data_train.shape
    negative_train = np.zeros((rows, cols), dtype=np.float32)

    for dim in range(cols):
        min_value = np.min(data_train[:, dim]) * (1 - percent_increase / 100.0)
        max_value = np.max(data_train[:, dim]) * (1 + percent_increase / 100.0)

        negative_train[:, dim] = random_state.uniform(min_value, max_value,
                                                      rows)

    return negative_train


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
