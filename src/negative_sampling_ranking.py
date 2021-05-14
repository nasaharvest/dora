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
from ranking import Ranking
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier


class NegativeSamplingRanking(Ranking):
    def __init__(self):
        super(NegativeSamplingRanking, self).__init__('negative_sampling')

    def _rank_internal(self, data_dir, prior_dir, start_sol, end_sol, seed,
                       percent_increase, min_prior, max_prior):
        raise RuntimeError('Negative sampling ranking is not implemented for '
                           'run_exp program')

    def _simulate_rank_internal(self, files, rank_data, prior_data, config,
                                seed, percent_increase):
        if percent_increase < 0 or percent_increase > 100:
            raise RuntimeError('percent_increase parameter must be a number '
                               'between 0 and 100.')

        if not config.use_prior:
            prior_data = None

        return self._rank_targets(prior_data, rank_data, files,
                                  percent_increase, config.enable_explanation)

    def _rank_targets(self, positive_train, data_test, files, percent_increase,
                      enable_explanation=False):
        # Create negative examples from positive examples
        negative_train = generate_negative_example(positive_train,
                                                   percent_increase)

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

        kfold = KFold(n_splits=5, shuffle=True)
        clf = GridSearchCV(RandomForestClassifier(), params, cv=kfold,
                           scoring='accuracy', n_jobs=1, iid=True,
                           error_score='raise')
        clf.fit(x, y)
        n_estimators = clf.best_params_['n_estimators']
        max_depth = clf.best_params_['max_depth']

        # Train a random forest classifier with the best parameters found in
        # grid search
        rf_clf = RandomForestClassifier(n_estimators=n_estimators,
                                        max_depth=max_depth)
        rf_clf.fit(x, y)

        # Make predictions for test data
        probs = rf_clf.predict_proba(data_test)

        # Keeping only the probabilities for negative (novel) class, and use
        # them as novelty scores to rank selections
        scores = probs[:, 0].flatten()
        indices_srt_by_scores = np.argsort(scores)[::-1]

        # prepare results to return
        results = dict()
        results.setdefault('ind', [])
        results.setdefault('sel_ind', [])
        results.setdefault('img_id', [])
        results.setdefault('scores', [])
        results.setdefault('explanations', [])
        for i, idx in enumerate(indices_srt_by_scores):
            results['ind'].append(i)
            results['sel_ind'].append(idx)
            results['img_id'].append(files[idx])
            results['scores'].append(scores[idx])

            if enable_explanation:
                results['explanations'].append(np.ones(64, 64))

        results_file_suffix = 'p-%d' % percent_increase

        return results, results_file_suffix


def generate_negative_example(data_train, percent_increase):
    rows, cols = data_train.shape
    negative_train = np.zeros((rows, cols), dtype=np.float32)

    for dim in range(cols):
        min_value = np.min(data_train[:, dim]) * (1 - percent_increase / 100.0)
        max_value = np.max(data_train[:, dim]) * (1 + percent_increase / 100.0)

        negative_train[:, dim] = np.random.uniform(min_value, max_value, rows)

    return negative_train


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