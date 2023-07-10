from pyworkflow.gui import TreeProvider
from pyworkflow.utils import removeBaseExt
from tomo.objects import SetOfTomograms, SetOfTomoMasks


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
