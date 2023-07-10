from os.path import abspath

import pyworkflow.viewer as pwviewer
from deepfinder import Plugin
from deepfinder.viewers.df_tomo_dialog import DFTomoDialog
from deepfinder.viewers.tomograms_tree_provider import DFTomogramsTreeProvider
from tomo.objects import SetOfTomograms, SetOfTomoMasks, Tomogram, TomoMask


class DeepFinderViewer(pwviewer.Viewer):
    _label = 'Ortho-slice volume explorer'
    _environments = [pwviewer.DESKTOP_TKINTER, Plugin.getEnviron()]
    _targets = [
        SetOfTomograms,
        SetOfTomoMasks
    ]

    def _visualize(self, obj, **kwargs):
        env = Plugin.getEnviron()
        cls = type(obj)

        if issubclass(cls, Tomogram):
            view = DeepFinderSetOfTomogramsView(obj)
        elif issubclass(cls, TomoMask):
            view = DeepFinderSetOfTomoMasksView(obj)
        else:  # Set
            view = DeepFinderView(self.getTkRoot(), self.protocol, obj)

        view._env = env
        return [view]


class DeepFinderView(pwviewer.View):
    def __init__(self, parent, protocol, objs):
        self._tkParent = parent
        self._protocol = protocol
        self._provider = DFTomogramsTreeProvider(protocol, objs)

    def show(self):
        DFTomoDialog(self._tkParent, self._provider.title, self._provider)


class DeepFinderSetOfTomogramsView(pwviewer.CommandView):
    """ Wrapper to visualize set of tomograms with DeepFinderDisplay """

    def __init__(self, obj, **kwargs):
        fname = abspath(obj.getFileName())
        pwviewer.CommandView.__init__(self, Plugin.getDeepFinderCmd('display') + ' -t' + fname)


class DeepFinderSetOfTomoMasksView(pwviewer.CommandView):
    """ Wrapper to visualize set of TomoMasks with DeepFinderDisplay """

    def __init__(self, obj, **kwargs):
        fn_mask = abspath(obj.getFileName())
        fn_tomo = abspath(obj.getVolName())
        pwviewer.CommandView.__init__(self, Plugin.getDeepFinderCmd('display') + ' -t' + fn_tomo + ' -l' + fn_mask)
