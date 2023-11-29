import threading
from os.path import abspath
import pyworkflow.viewer as pwviewer
from deepfinder import Plugin
from pyworkflow.gui import TreeProvider, ListDialog
from pyworkflow.utils import runJob
from tomo.objects import SetOfTomograms, SetOfTomoMasks, TomoMask


class DeepFinderViewer(pwviewer.Viewer):
    _label = 'Ortho-slice volume explorer'
    _environments = [pwviewer.DESKTOP_TKINTER, Plugin.getEnviron()]
    _targets = [
        SetOfTomograms,
        SetOfTomoMasks
    ]

    def _visualize(self, obj, **kwargs):
        env = Plugin.getEnviron()
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


class DFTomogramsTreeProvider(TreeProvider):
    """ Populate Tree from SetOfTomograms. """

    title = 'DeepFinder viewer'
    COL_TS = 'Tilt series'
    COL_INFO = 'Info'
    ORDER_DICT = {COL_TS: 'id'}

    def __init__(self, protocol, objs):
        super().__init__(self)
        # self.tomoList = tomoList
        self.protocol = protocol
        self.objs = objs
        if isinstance(objs, SetOfTomograms):
            self.COL_TS = 'Tomograms'
            self.title = 'Tomograms display'
        elif isinstance(objs, SetOfTomoMasks):
            self.COL_TS = 'Tomo masks (segmentations)'
            self.title = 'Tomo masks display'

    def getObjects(self):
        # Retrieve all objects of type className
        objects = []

        orderBy = self.ORDER_DICT.get(self.getSortingColumnName(), 'id')
        direction = 'ASC' if self.isSortingAscending() else 'DESC'

        for obj in self.objs.iterItems(orderBy=orderBy, direction=direction):
            item = obj.clone()
            item._allowsSelection = True
            item._parentObject = None
            objects.append(item)

        return objects

    def getColumns(self):
        return [(self.COL_TS, 200),
                (self.COL_INFO, 400)]

    def getObjectInfo(self, obj):
        return {'key': obj.getObjId(),
                'parent': None,
                'text': obj.getTsId(),
                'values': tuple([str(obj)])}


class DFTomoDialog(ListDialog):

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
