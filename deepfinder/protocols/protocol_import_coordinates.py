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
from os.path import basename

from pyworkflow import BETA
from pyworkflow.object import String
from tomo.constants import BOTTOM_LEFT_CORNER

from tomo.objects import SetOfCoordinates3D, Coordinate3D
from tomo.protocols.protocol_base import ProtTomoImportFiles

import pyworkflow.protocol.params as params

import deepfinder.convert as cv


class ImportCoordinates3D(ProtTomoImportFiles):
    """Protocol to import a DeepFinder object list as a set of 3D coordinates in Scipion"""

    _outputClassName = 'SetOfCoordinates3D'
    _label = 'import coordinates'
    _devStatus = BETA

    def _defineParams(self, form):
        ProtTomoImportFiles._defineImportParams(self, form)

        form.addParam('importTomograms', params.PointerParam,
                      pointerClass='SetOfTomograms',
                      label='Input tomograms',
                      help='Select the tomograms/tomogram for which you '
                           'want to import coordinates. The file names of the tomogram and '
                           'coordinate files must be the same.')

    def _insertAllSteps(self):
        self._insertFunctionStep('importCoordinatesStep')

    # --------------------------- STEPS functions -----------------------------
    def importCoordinatesStep(self):
        importTomograms = self.importTomograms.get()
        suffix = self._getOutputSuffix(SetOfCoordinates3D)
        coord3DSet = self._createSetOfCoordinates3D(importTomograms, suffix)

        coord3DSet.setPrecedents(importTomograms)
        coordCounter = 1
        for tomoInd, tomo in enumerate(importTomograms.iterItems()):
            tomoName = basename(os.path.splitext(tomo.getFileName())[0])
            for coordFile, fileId in self.iterFiles():
                fileName = basename(os.path.splitext(coordFile)[0])

                if tomo is not None and tomoName == fileName:
                    objl = cv.objl_read(coordFile)

                    for idx in range(len(objl)):
                        x = objl[idx]['x']
                        y = objl[idx]['y']
                        z = objl[idx]['z']
                        lbl = objl[idx]['label']

                        coord = Coordinate3D()
                        coord.setVolume(tomo)
                        coord.setObjId(coordCounter)
                        coord.setPosition(x, y, z, BOTTOM_LEFT_CORNER)
                        coord.setVolId(tomoInd + 1)
                        coord._dfLabel = String(str(lbl))

                        coord3DSet.append(coord)
                        coordCounter += 1

        coord3DSet.setSamplingRate(importTomograms.getSamplingRate())

        self._defineOutputs(outputCoordinates=coord3DSet)
        self._defineSourceRelation(self.importTomograms, coord3DSet)
