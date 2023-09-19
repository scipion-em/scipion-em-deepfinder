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
from enum import Enum
from os.path import abspath
from pyworkflow.gui import askYesNo
from pyworkflow.object import String, Integer
from pyworkflow.protocol import IntParam
from pyworkflow.utils import removeBaseExt, Message
from tomo.constants import BOTTOM_LEFT_CORNER
from tomo.protocols import ProtTomoPicking
from tomo.objects import Coordinate3D, SetOfCoordinates3D
import deepfinder.convert as cv
from deepfinder.constants import *
from deepfinder.viewers.particle_annotator_tomo_viewer import ParticleAnnotatorDialog
from deepfinder.viewers.particle_annotator_tree import ParticleAnnotatorProvider


class DFAnnotateOutputs(Enum):
    coordinates = SetOfCoordinates3D


class DeepFinderAnnotations(ProtTomoPicking):
    """This protocol allows you to annotate macromolecules in your tomograms, using a visual tool."""

    _label = 'annotate particles'
    _possibleOutputs = DFAnnotateOutputs

    def __init__(self, **args):
        ProtTomoPicking.__init__(self, **args)
        self.annotationSummary = String()
        self._objectsToGo = Integer()
        self._provider = None

    # --------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        ProtTomoPicking._defineParams(self, form)
        from pyworkflow.protocol import LEVEL_ADVANCED
        form.addParam('boxSize', IntParam, label="Box size", expertLevel=LEVEL_ADVANCED,
                      help='Default box size for the output.', default=50)

    # --------------------------- INSERT steps functions ----------------------
    def _insertAllSteps(self):
        self._initialize()
        self._insertFunctionStep(self.launchAnnotationStep, interactive=True)

    # --------------------------- STEPS functions -----------------------------
    def launchAnnotationStep(self):
        """ This generates 1 objl.xml file per tomogram and stores it in EXTRA"""

        # There are still some objects which haven't been annotated --> launch GUI
        self._getAnnotationStatus()
        if self._objectsToGo.get() > 0:
            ParticleAnnotatorDialog(None, self._getExtraPath(), provider=self._provider, prot=self)

        # All the objetcs have been annotated --> create output objects
        # Open dialog to request confirmation to create output
        import tkinter as tk
        frame = tk.Frame()
        if askYesNo(Message.TITLE_SAVE_OUTPUT, Message.LABEL_SAVE_OUTPUT, frame):
            doneTomos = [tomo for tomo in self._tomoList if self._provider.getObjectInfo(tomo)['values'][0] > 0]
            self._genOutput3DCoords(doneTomos)

        self._getAnnotationStatus()
        self._store()

    def _genOutput3DCoords(self, annotatedTomos):
        setTomograms = self.inputTomograms.get()
        coord3DSet = self._createSetOfCoordinates3D(setTomograms)
        coord3DSet.setSamplingRate(setTomograms.getSamplingRate())
        coord3DSet.setBoxSize(self.boxSize.get())

        coordCounter = 0
        annotationSummary = ''
        for tomo in annotatedTomos:
            tomoName = tomo.getFileName()
            # Read objl:
            fname_objl = 'objl_annot_' + removeBaseExt(tomoName) + '.xml'
            objl_tomo = cv.objl_read(abspath(self._getExtraPath(fname_objl)))

            # Generate string for protocol summary:
            msg = 'Tomogram ' + tomoName + ': a total of ' + \
                  str(len(objl_tomo)) + ' objects has been annotated.'
            annotationSummary += msg
            lbl_list = cv.objl_get_labels(objl_tomo)
            for lbl in lbl_list:
                objl_class = cv.objl_get_class(objl_tomo, lbl)
                msg = '\nClass ' + str(lbl) + ': ' + str(len(objl_class)) + ' objects'
                annotationSummary += msg
            annotationSummary += '\n'

            for idx in range(len(objl_tomo)):
                x = objl_tomo[idx][DF_COORD_X]
                y = objl_tomo[idx][DF_COORD_Y]
                z = objl_tomo[idx][DF_COORD_Z]
                lbl = objl_tomo[idx][DF_LABEL]

                coord = Coordinate3D()
                coord.setObjId(coordCounter + 1)
                coord.setVolume(tomo)
                coord.setPosition(x, y, z, BOTTOM_LEFT_CORNER)
                coord.setVolId(tomo.getObjId())
                coord.setGroupId(lbl)

                coord3DSet.append(coord)
                coordCounter += 1

        self._defineOutputs(**{self._possibleOutputs.coordinates.name: coord3DSet})
        self._defineSourceRelation(setTomograms, coord3DSet)

    # --------------------------- DEFINE info functions ----------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []
        objects2go = self._objectsToGo.get()
        if objects2go is not None:
            if objects2go > 0:
                summary.append('*%i* remaining tomograms to be annotated.' % objects2go)
            else:
                summary.append('All tomograms have been already annotated.')
        if self.annotationSummary.get():
            summary.append(self.annotationSummary.get())

        return summary

    # --------------------------- UTIL functions -----------------------------------

    def _initialize(self):
        self._tomoList = [tomo.clone() for tomo in self.inputTomograms.get().iterItems()]
        self._provider = ParticleAnnotatorProvider(self._tomoList, self._getExtraPath(), 'partAnnotator')
        self._getAnnotationStatus()

    def _getAnnotationStatus(self):
        """Check if all the tomo masks have been annotated and store current status in a text file"""
        doneTomes = [self._provider.getObjectInfo(tomo)['values'][0] > 0 for tomo in self._tomoList]
        self._objectsToGo.set(len(self._tomoList) - sum(doneTomes))
