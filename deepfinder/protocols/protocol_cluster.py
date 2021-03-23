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
from pyworkflow.object import Integer, Set, String, Float
from pyworkflow.protocol import Protocol, params, IntParam, EnumParam, PointerParam
from pyworkflow.utils.properties import Message
from tomo.objects import Coordinate3D
from tomo.protocols import ProtTomoPicking
from deepfinder.objects import Coordinate3DWithScore

from deepfinder import Plugin
import deepfinder.convert as cv
from deepfinder.protocols import ProtDeepFinderBase

import os

"""
Describe your python module here:
This module will provide the traditional Hello world example
"""


class DeepFinderCluster(ProtTomoPicking, ProtDeepFinderBase):
    """This protocol analyses segmentation maps and outputs particle coordinates and class."""

    _label = 'cluster'

    def __init__(self, **args):
        ProtTomoPicking.__init__(self, **args)
        #ProtDeepFinderBase.__init__(self, **args)
        self.clusteringSummary = String()

    # --------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputSegmentations', PointerParam,
                      pointerClass='SetOfTomoMasks',
                      label="Segmentation maps", important=True,
                      help='Please select the segmentation maps you would like to analyze.')

        form.addParam('cradius', params.IntParam,
                      default=5,
                      label='Clustering radius', important=True,
                      help='Should correspond to average radius of target objects (in voxels)')

    # --------------------------- INSERT steps functions ----------------------
    def _insertAllSteps(self):

        # Launch Boxing GUI
        self._insertFunctionStep('launchClusteringStep')
        self._insertFunctionStep('createOutputStep')

    # --------------------------- STEPS functions -----------------------------
    def launchClusteringStep(self):
        for segm in self.inputSegmentations.get().iterItems():
            fname_segm = os.path.splitext(segm.getFileName())
            fname_segm = os.path.basename(fname_segm[0])
            fname_objl = 'objl_' + fname_segm + '.xml'
            fname_objl = os.path.abspath(os.path.join(self._getExtraPath(), fname_objl))

            # Launch DeepFinder executable:
            deepfinder_args = '-l ' + segm.getFileName()
            deepfinder_args += ' -r ' + str(self.cradius)
            deepfinder_args += ' -o ' + fname_objl

            Plugin.runDeepFinder(self, 'cluster', deepfinder_args)

    def createOutputStepOLD(self):
        # Convert DeepFinder annotation output to Scipion SetOfCoordinates3D
        setSegmentations = self.inputSegmentations.get()

        # First, determine the classes that have been found (check in all object lists):
        objl = []
        for segm in setSegmentations.iterItems():
            # Get objl filename:
            fname_segm = os.path.splitext(segm.getFileName())
            fname_segm = os.path.basename(fname_segm[0])
            fname_objl = 'objl_' + fname_segm + '.xml'

            # Read objl:
            objl_tomo = cv.objl_read(os.path.abspath(os.path.join(self._getExtraPath(), fname_objl)))
            objl.extend(objl_tomo)

        lbl_list = cv.objl_get_labels(objl)  # get unique class labels

        # For each class, iterate over all object lists (1 per tomo) and store coordinates
        # in SetOfCoordinates3D (1 per class)
        # Remark: only 1 setOfCoordinates3D can exist at a time, else:
        # "Protocol failed: Cannot operate on a closed database."
        for lbl in lbl_list:
            coord3DSet = self._createSetOfCoordinates3DWithScore(setSegmentations,
                                                        lbl)  # lbl is a suffix for sqlite filename. Important, else overwrite!
            coord3DSet.setName('Class ' + str(lbl))
            coord3DSet.setPrecedents(setSegmentations)
            coord3DSet.setSamplingRate(setSegmentations.getSamplingRate())

            for segm in setSegmentations.iterItems():
                # Get objl filename:
                fname_segm = os.path.splitext(segm.getFileName())
                fname_segm = os.path.basename(fname_segm[0])
                fname_objl = 'objl_' + fname_segm + '.xml'

                # Read objl:
                objl_tomo = cv.objl_read(os.path.abspath(os.path.join(self._getExtraPath(), fname_objl)))
                objl_class = cv.objl_get_class(objl_tomo, lbl)
                for idx in range(len(objl_class)):
                    x = objl_class[idx]['x']
                    y = objl_class[idx]['y']
                    z = objl_class[idx]['z']
                    score = objl_class[idx]['cluster_size']

                    coord = Coordinate3DWithScore()
                    coord.setPosition(x, y, z)
                    coord.setScore(score)
                    coord.setVolume(segm)
                    # coord.setVolName(segm.getFileName())
                    coord3DSet.append(coord)

            # Link to output:
            name = 'outputCoordinates3D_class' + str(lbl)
            args = {}
            coord3DSet.setStreamState(Set.STREAM_OPEN)
            args[name] = coord3DSet

            self._defineOutputs(**args)
            self._defineSourceRelation(setSegmentations, coord3DSet)

        # I (emoebel) don't know what this is for, but is apparently necessary (copied from Estrella's XmippProtCCroi)
        for outputset in self._iterOutputsNew():
            outputset[1].setStreamState(Set.STREAM_CLOSED)
        self._store()


    def createOutputStep(self):
        # Convert DeepFinder annotation output to Scipion SetOfCoordinates3D
        setSegmentations = self.inputSegmentations.get()


        coord3DSet = self._createSetOfCoordinates3DWithScore(setSegmentations)  # lbl is a suffix for sqlite filename. Important, else overwrite!
        coord3DSet.setName('Detected objects')
        coord3DSet.setPrecedents(setSegmentations)
        coord3DSet.setSamplingRate(setSegmentations.getSamplingRate())

        coordCounter = 0
        clusteringSummary = ''
        for segmInd, segm in enumerate(setSegmentations.iterItems()):
            # Get objl filename:
            fname_segm = os.path.splitext(segm.getFileName())
            fname_segm = os.path.basename(fname_segm[0])
            fname_objl = 'objl_' + fname_segm + '.xml'

            # Read objl:
            objl_tomo = cv.objl_read(os.path.abspath(os.path.join(self._getExtraPath(), fname_objl)))

            # Generate string for protocol summary:
            msg = 'Segmentation '+str(segmInd+1)+': a total of ' + str(len(objl_tomo)) + ' objects has been found.'
            clusteringSummary += msg
            lbl_list = cv.objl_get_labels(objl_tomo)
            for lbl in lbl_list:
                objl_class = cv.objl_get_class(objl_tomo, lbl)
                msg = '\nClass ' + str(lbl) + ': ' + str(len(objl_class)) + ' objects'
                clusteringSummary += msg
            clusteringSummary += '\n'

            # Get tomo corresponding to current tomomask:
            tomo = segm.getTomogram()

            for idx in range(len(objl_tomo)):
                x = objl_tomo[idx]['x']
                y = objl_tomo[idx]['y']
                z = objl_tomo[idx]['z']
                lbl = objl_tomo[idx]['label']
                score = objl_tomo[idx]['cluster_size']

                coord = Coordinate3D()
                coord.setObjId(coordCounter)
                coord.setPosition(x, y, z)
                coord.setVolume(tomo)
                coord.setVolId(segmInd + 1)
                coord._dfLabel = String(str(lbl))
                coord._dfScore = Float(score)

                coord3DSet.append(coord)

                coordCounter += 1

        self._defineOutputs(outputCoordinates=coord3DSet)
        self._defineSourceRelation(setSegmentations, coord3DSet)

        self.clusteringSummary.set(clusteringSummary)
        self._store(self.clusteringSummary)

        # # Link to output:
        # name = 'outputCoordinates3D'
        # args = {}
        # coord3DSet.setStreamState(Set.STREAM_OPEN)
        # args[name] = coord3DSet
        #
        # self._defineOutputs(**args)
        # self._defineSourceRelation(setSegmentations, coord3DSet)
        #
        # # I (emoebel) don't know what this is for, but is apparently necessary (copied from Estrella's XmippProtCCroi)
        # for outputset in self._iterOutputsNew():
        #     outputset[1].setStreamState(Set.STREAM_CLOSED)
        # self._store()


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
