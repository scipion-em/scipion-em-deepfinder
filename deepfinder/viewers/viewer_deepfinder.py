from os.path import abspath
import pyworkflow.viewer as pwviewer
from tomo.objects import SetOfTomograms, Tomogram, TomoMask, SetOfTomoMasks
from deepfinder import Plugin


class DeepFinderViewer(pwviewer.Viewer):
    _label = 'Ortho-slice volume explorer'
    _targets = [
        SetOfTomograms,
        SetOfTomoMasks
    ]

    def _visualize(self, obj, **kwargs):
        env = Plugin.getEnviron()
        view = []
        cls = type(obj)

        if issubclass(cls, SetOfTomoMasks) or issubclass(cls, TomoMask):
            view = DeepFinderSetOfTomoMasksView(obj)
        elif issubclass(cls, SetOfTomograms) or issubclass(cls, Tomogram):
            view = DeepFinderSetOfTomogramsView(obj)

        view._env = env
        return [view]


class DeepFinderSetOfTomogramsView(pwviewer.CommandView):
    """ Wrapper to visualize set of tomograms with DeepFinderDisplay """

    def __init__(self, set, **kwargs):
        for item in set: # /!\ Can cause OOM if too many items
            fname = abspath(item.getFileName())
            pwviewer.CommandView.__init__(self, Plugin.getDeepFinderCmd('display') + ' -t' + fname)


class DeepFinderSetOfTomoMasksView(pwviewer.CommandView):
    """ Wrapper to visualize set of TomoMasks with DeepFinderDisplay """

    def __init__(self, set, **kwargs):
        for item in set: # /!\ Can cause OOM if too many items
            fn_mask = abspath(item.getFileName())
            fn_tomo = abspath(item.getVolName())
            pwviewer.CommandView.__init__(self, Plugin.getDeepFinderCmd('display') + ' -t' + fn_tomo + ' -l' + fn_mask)


