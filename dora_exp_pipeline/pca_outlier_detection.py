import numpy as np
from sklearn.decomposition import PCA
from dora_exp_pipeline.outlier_detection import OutlierDetection


class PCAOutlierDetection(OutlierDetection):
    def __init__(self):
        super(PCAOutlierDetection, self).__init__('pca')

    def _rank_internal(self, data_to_fit, data_to_score, seed, k):
        if k < 1:
            raise RuntimeError('The number of principal components (k) must '
                               'be >= 1')

        # Check that the number of PCA components <= number of features
        if k > data_to_fit.shape[1]:
            raise RuntimeError(f'The number of principal components (k = {k}) '
                               f'must be < number of features '
                               f'({data_to_fit.shape[1]})')

        # Rank targets
        return train_and_run_PCA(data_to_fit, data_to_score, k, seed)


def train_and_run_PCA(train, test, k, seed):
    # initialize the PCA model (deterministically)
    pca = PCA(n_components=k, random_state=seed)

    # fit the PCA model
    pca.fit(train)

    return compute_score(test, pca)


def compute_score(images, pca):
    scores = np.ndarray(images.shape[0])

    for i in range(images.shape[0]):
        # compute the L2 norm between input and reconstruction
        recon = pca.inverse_transform(pca.transform([images[i]]))
        sub = images[i] - recon
        scores[i] = np.linalg.norm(sub, ord=2, axis=1)

    return scores


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
