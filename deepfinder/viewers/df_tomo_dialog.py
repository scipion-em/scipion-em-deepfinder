import threading
from os.path import abspath

from deepfinder import Plugin
from pyworkflow.gui import ListDialog
from pyworkflow.utils import runJob
from tomo.objects import TomoMask


class DFTomoDialog(ListDialog):
    """
    This class extend from ListDialog to allow calling
    an Eman subprocess from a list of Tomograms.
    """

    def __init__(self, parent, title, provider, itemDoubleClick=True, **kwargs):
        self.provider = provider
        self.proc = None
        self._itemDoubleClick = itemDoubleClick
        ListDialog.__init__(self, parent, title, provider,
                            message=None,
                            allowSelect=False,
                            cancelButton=True,
                            **kwargs)

    def body(self, bodyFrame):
        super().body(bodyFrame)
        if self._itemDoubleClick:
            self.tree.itemDoubleClick = self.doubleClickOnTomogram

    def doubleClickOnTomogram(self, e=None):
        tomo = e
        self.proc = threading.Thread(target=self.launchDFViewerForTomogram, args=(tomo,))
        self.proc.start()

    @staticmethod
    def launchDFViewerForTomogram(tomo):
        if type(tomo) == TomoMask:
            fname = tomo.getVolName()
            maskName = tomo.getFileName()
            args = f'-t {abspath(fname)} -l {abspath(maskName)}'
        else:
            fname = tomo.getFileName()
            args = f'-t {abspath(fname)}'

        program = Plugin.getDeepFinderCmd('display')
        runJob(None, program, args, env=Plugin.getEnviron())
