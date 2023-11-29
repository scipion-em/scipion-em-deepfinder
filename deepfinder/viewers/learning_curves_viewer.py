from matplotlib import pyplot as plt
import pyworkflow.viewer as pwviewer
from pwem.viewers import ImageView
from deepfinder.protocols.protocol_train import DeepFinderTrain


class DeepFinderLCurvesViewer(pwviewer.Viewer):
    _label = 'Learning Curves Viewer'
    _targets = [DeepFinderTrain]

    def _visualize(self, obj, **kwargs):
        view = DFImageView(self.protocol._getExtraPath('net_train_history_plot.png'))
        view._tkParent = self.getTkRoot()
        return [view]


class DFImageView(ImageView):

    def show(self):
        image_file = self.getImagePath()
        plt.figure(num='DeepFinder Learning Curves')
        image = plt.imread(image_file)
        plt.imshow(image)
        plt.axis('off')
        plt.tight_layout()  # Decrease the padding
        plt.show()
