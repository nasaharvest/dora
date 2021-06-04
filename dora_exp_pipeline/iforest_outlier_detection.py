import numpy as np
from sklearn.ensemble import IsolationForest
from dora_exp_pipeline.outlier_detection import OutlierDetection


class IForestOutlierDetection(OutlierDetection):
    def __init__(self):
        super(IForestOutlierDetection, self).__init__('iforest')

    def _rank_internal(self, data_to_fit, data_to_score, seed):
        return train_and_run_ISO(data_to_fit, data_to_score, seed)


def train_and_run_ISO(train, test, seed):
    random_state = np.random.RandomState(seed)

    # initialize isolation forest
    clf_iso = IsolationForest(max_samples=train.shape[0], contamination=0.1,
                              random_state=random_state, behaviour='new')

    # train isolation forest
    clf_iso.fit(train)

    # novelty scores of the test items
    scores_iso = clf_iso.decision_function(test)

    return scores_iso


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
