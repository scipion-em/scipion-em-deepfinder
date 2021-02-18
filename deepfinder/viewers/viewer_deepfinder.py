import pyworkflow.viewer as pwviewer
import tomo.objects
from deepfinder.protocols import DeepFinderSegment, DeepFinderGenerateTrainingTargetsSpheres
from tomo.protocols import ProtImportTomograms

class DeepFinderViewer(pwviewer.Viewer):
    _label = 'Ortho-slice volume explorer'
    _targets = [
        tomo.objects.Tomogram,
        tomo.objects.TomoMask,
        tomo.objects.SetOfTomograms,
        tomo.objects.SetOfTomoMasks,
        ProtImportTomograms,
        DeepFinderGenerateTrainingTargetsSpheres,
        DeepFinderSegment
    ]

    def _visualize(self, obj, **kwargs):

        # deepfinder_args = ''
        # if self.tomogram.get() != None:
        #     fname = self.tomogram.get().getFileName()
        #     deepfinder_args += '-t ' + fname
        # if self.segmentation.get() != None:
        #     for seg in self.segmentation.get().iterItems():
        #         fname = seg.getFileName()
        #         deepfinder_args += ' -l ' + fname
        #
        #         fname_tomo = str(seg.getTomoName())
        #         if fname_tomo != '':  # if a tomo is linked to segmentation, also display tomo
        #             deepfinder_args += ' -t ' + fname_tomo

        pass
