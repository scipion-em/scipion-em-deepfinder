from os.path import abspath

import pyworkflow.viewer as pwviewer
from tomo.objects import SetOfTomograms, Tomogram, TomoMask, SetOfTomoMasks

from deepfinder.protocols import DeepFinderSegment, DeepFinderGenerateTrainingTargetsSpheres
from tomo.protocols import ProtImportTomograms

from deepfinder import Plugin

class DeepFinderViewer(pwviewer.Viewer):
    _label = 'Ortho-slice volume explorer'
    _targets = [
        Tomogram,
        TomoMask,
        SetOfTomograms,
        SetOfTomoMasks,
        #ProtImportTomograms,
        #DeepFinderGenerateTrainingTargetsSpheres,
        #DeepFinderSegment
    ]

    def _visualize(self, obj, **kwargs):
        env = Plugin.getEnviron()
        view = []
        cls = type(obj)

        # if issubclass(cls, tomo.objects.Tomogram):
        #     view = DeepFinderTomoView(obj)
        if issubclass(cls, SetOfTomograms) or issubclass(cls, Tomogram)\
                or issubclass(cls, SetOfTomoMasks) or issubclass(cls, TomoMask):
            view = DeepFinderSetOfTomogramsView(obj)

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

        view._env = env
        return [view]

# class DeepFinderTomoView(pwviewer.CommandView):
#     """ Wrapper to visualize different type of objects with the DeepFinderDisplay """
#
#     def __init__(self, obj, **kwargs):
#         fname = obj.getFileName()
#         #deepfinder_args = '-t ' + fname
#         #Plugin.runDeepFinder(self, 'display', deepfinder_args)
#         pwviewer.CommandView.__init__(self, Plugin.getDeepFinderCmd('display') + ' -t' + fname)

class DeepFinderSetOfTomogramsView(pwviewer.CommandView):
    """ Wrapper to visualize set of tomograms with DeepFinderDisplay """

    def __init__(self, set, **kwargs):
        for item in set:
            fname = abspath(item.getFileName())
            #deepfinder_args = '-t ' + fname
            #Plugin.runDeepFinder(self, 'display', deepfinder_args) # /!\ Can cause OOM if too many items
            pwviewer.CommandView.__init__(self, Plugin.getDeepFinderCmd('display') + ' -t' + fname)


