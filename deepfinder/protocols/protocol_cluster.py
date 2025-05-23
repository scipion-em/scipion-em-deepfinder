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
from pyworkflow.object import String
from pyworkflow.protocol import params, PointerParam, STEPS_PARALLEL
from pyworkflow.utils import removeBaseExt, cyanStr
from pyworkflow.utils.properties import Message
from tomo.constants import BOTTOM_LEFT_CORNER
from tomo.objects import Coordinate3D, SetOfTomograms, SetOfCoordinates3D
from tomo.protocols import ProtTomoPicking
from deepfinder import Plugin
from deepfinder.constants import *
import deepfinder.convert as cv
from deepfinder.protocols import ProtDeepFinderBase
import os
from tomo.utils import getObjFromRelation
import logging
logger = logging.getLogger(__name__)


class DFClusterOutputs(Enum):
    coordinates = SetOfCoordinates3D


class DeepFinderCluster(ProtTomoPicking, ProtDeepFinderBase):
    """This protocol analyses segmentation maps and outputs particle coordinates and class."""

    _label = 'cluster'
    _possibleOutputs = DFClusterOutputs
    stepsExecutionMode = STEPS_PARALLEL

    def __init__(self, **args):
        super().__init__(**args)
        self.clusteringSummary = String()
        self.tomoMasksDict = None

    # --------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputSegmentations', PointerParam,
                      pointerClass='SetOfTomoMasks',
                      label="Segmentation maps",
                      important=True,
                      help='Please select the segmentation maps you would like to analyze.')
        form.addParam('cradius', params.IntParam,
                      default=5,
                      label='Clustering radius',
                      important=True,
                      help='Should correspond to average radius of target objects (in voxels)')
        form.addParallelSection(threads=4, mpi=1)

    # --------------------------- INSERT steps functions ----------------------
    def _insertAllSteps(self):
        self.__initialize()
        closeDeps = []
        ind = 0
        for tsId in self.tomoMasksDict.keys():
            pid = self._insertFunctionStep(self.launchClusteringStep, tsId,
                                           prerequisites=[],
                                           needsGPU=False)
            cOutId = self._insertFunctionStep(self.createOutputStep, tsId, ind,
                                           prerequisites=pid,
                                           needsGPU=False)
            closeDeps.append(cOutId)
            ind += 1
        self._insertFunctionStep(self._closeOutputSet,
                                 prerequisites=closeDeps,
                                 needsGPU=False)

    # --------------------------- STEPS functions -----------------------------
    def __initialize(self):
        self.tomoMasksDict = {tomoMask.getTsId(): tomoMask.clone() for tomoMask in self.inputSegmentations.get()}

    def launchClusteringStep(self, tsId: str):
        logger.info(cyanStr(f'Clustering step of ---> {tsId}'))
        segm = self.tomoMasksDict[tsId]
        fname_objl = 'objl_' + removeBaseExt(segm.getFileName()) + '.xml'
        fname_objl = os.path.abspath(os.path.join(self._getExtraPath(), fname_objl))

        # Launch DeepFinder executable:
        deepfinder_args = '-l ' + segm.getFileName()
        deepfinder_args += ' -r ' + str(self.cradius.get())
        deepfinder_args += ' -o ' + fname_objl

        Plugin.runDeepFinder(self, 'cluster', deepfinder_args)

    def createOutputStep(self, tsId: str, segmInd: int):
        with self._lock:
            segm = self.tomoMasksDict[tsId]
            logger.info(cyanStr(f'Generating the output of ---> {tsId}'))
            # Convert DeepFinder annotation output to Scipion SetOfCoordinates3D
            outCoords = self.createOutputSet()
            clusteringSummary = ''
            # Get objl filename:
            fname_segm = os.path.splitext(segm.getFileName())
            fname_segm = os.path.basename(fname_segm[0])
            fname_objl = 'objl_' + fname_segm + '.xml'

            # Read objl:
            objl_tomo = cv.objl_read(os.path.abspath(os.path.join(self._getExtraPath(), fname_objl)))

            # Generate string for protocol summary:
            msg = 'Segmentation ' + str(segmInd + 1) + ': a total of ' + str(
                len(objl_tomo)) + ' objects has been found.'
            clusteringSummary += msg
            lbl_list = cv.objl_get_labels(objl_tomo)
            for lbl in lbl_list:
                objl_class = cv.objl_get_class(objl_tomo, lbl)
                msg = '\nClass ' + str(lbl) + ': ' + str(len(objl_class)) + ' objects'
                clusteringSummary += msg
            clusteringSummary += '\n'

            # Get tomo corresponding to current tomomask:
            tomo = segm.getTomogram()
            tomoId = segm.getTsId()

            for idx in range(len(objl_tomo)):
                x = objl_tomo[idx][DF_COORD_X]
                y = objl_tomo[idx][DF_COORD_Y]
                z = objl_tomo[idx][DF_COORD_Z]
                lbl = objl_tomo[idx][DF_LABEL]
                score = objl_tomo[idx][DF_SCORE]

                coord = Coordinate3D()
                coord.setVolume(tomo)
                coord.setPosition(x, y, z, BOTTOM_LEFT_CORNER)
                coord.setTomoId(tomoId)
                coord.setVolId(segmInd + 1)
                coord.setGroupId(lbl)
                coord.setScore(score)

                outCoords.append(coord)

            self.clusteringSummary.set(clusteringSummary)
            self._store(self.clusteringSummary)

    # --------------------------- DEFINE info functions ---------------------- # TODO
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []
        if self.isFinished():
            if self.clusteringSummary.get():
                summary.append(self.clusteringSummary.get())

            # if self._noAnnotations.get():
            #     summary.append('NO OBJECTS WERE TAKEN.')

        return summary

    # --------------------------- UTILS functions -----------------------------
    def createOutputSet(self) -> SetOfCoordinates3D:
        outCoords = getattr(self, self._possibleOutputs.coordinates.name, None)
        boxSize = 2 * self.cradius.get()
        if outCoords:
            outCoords.enableAppend()
        else:
            setSegmentations = self.inputSegmentations.get()
            tomograms = getObjFromRelation(setSegmentations, self, SetOfTomograms)
            outCoords = SetOfCoordinates3D.create(self.getPath(), template='coordinates%s.sqlite')
            outCoords.setName('Detected objects')
            outCoords.setPrecedents(tomograms)
            outCoords.setSamplingRate(setSegmentations.getSamplingRate())
            outCoords.setBoxSize(boxSize)
            outCoords.setStreamState(outCoords.STREAM_OPEN)

            # Define relations
            self._defineOutputs(**{self._possibleOutputs.coordinates.name: outCoords})
            self._defineSourceRelation(self.inputSegmentations, outCoords)

        return outCoords
