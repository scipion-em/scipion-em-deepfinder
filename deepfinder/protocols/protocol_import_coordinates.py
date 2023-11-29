# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors: Emmanuel Moebel (emmanuel.moebel@inria.fr)
# *
# * Inria - Centre de Rennes Bretagne Atlantique, France
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'you@yourinstitution.email'
# *
# **************************************************************************
import os
from enum import Enum
from os.path import basename

from deepfinder.constants import *
from pyworkflow.protocol import LEVEL_ADVANCED
from pyworkflow.utils import removeBaseExt
from tomo.constants import BOTTOM_LEFT_CORNER
from tomo.objects import SetOfCoordinates3D, Coordinate3D
from tomo.protocols.protocol_base import ProtTomoImportFiles
import pyworkflow.protocol.params as params
import deepfinder.convert as cv


class DFImportCoordsOutputs(Enum):
    coordinates = SetOfCoordinates3D


class ImportCoordinates3D(ProtTomoImportFiles):
    """Protocol to import a DeepFinder object list as a set of 3D coordinates in Scipion"""

    _label = 'import DeepFinder coordinates'
    _possibleOutputs = DFImportCoordsOutputs

    def _defineParams(self, form):
        ProtTomoImportFiles._defineImportParams(self, form)

        form.addParam('importTomograms', params.PointerParam,
                      pointerClass='SetOfTomograms',
                      label='Input tomograms',
                      help='Select the tomograms/tomogram for which you '
                           'want to import coordinates. The file names of the tomogram and '
                           'coordinate files must be the same.')
        form.addParam('boxSize', params.IntParam,
                      label="Box size",
                      expertLevel=LEVEL_ADVANCED,
                      default=50,
                      help='Default box size for the output.')

    def _insertAllSteps(self):
        self._insertFunctionStep(self.importCoordinatesStep)

    # --------------------------- STEPS functions -----------------------------
    def importCoordinatesStep(self):
        importTomograms = self.importTomograms.get()
        boxSize = self.boxSize.get()
        coord3DSet = SetOfCoordinates3D.create(self._getPath(), template='coordinates.sqlite')
        coord3DSet.setPrecedents(importTomograms)
        coord3DSet.setBoxSize(boxSize)
        coord3DSet.setSamplingRate(importTomograms.getSamplingRate())
        coordCounter = 1
        for tomoInd, tomo in enumerate(importTomograms.iterItems()):
            tomoName = basename(os.path.splitext(tomo.getFileName())[0])
            for coordFile, fileId in self.iterFiles():
                fileName = removeBaseExt(coordFile)

                if tomo is not None and tomoName == fileName:
                    objl = cv.objl_read(coordFile)

                    for idx in range(len(objl)):
                        iobjl = objl[idx]
                        x = iobjl[DF_COORD_X]
                        y = iobjl[DF_COORD_Y]
                        z = iobjl[DF_COORD_Z]
                        lbl = iobjl[DF_LABEL]
                        score = iobjl.get(DF_SCORE, None)

                        coord = Coordinate3D()
                        coord.setVolume(tomo)
                        coord.setObjId(coordCounter)
                        coord.setPosition(x, y, z, BOTTOM_LEFT_CORNER)
                        coord.setVolId(tomoInd + 1)
                        coord.setBoxSize(boxSize)
                        coord.setGroupId(lbl)
                        coord.setScore(score)

                        coord3DSet.append(coord)
                        coordCounter += 1

        self._defineOutputs(**{self._possibleOutputs.coordinates.name: coord3DSet})
        self._defineSourceRelation(self.importTomograms, coord3DSet)
