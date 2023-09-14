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
from pyworkflow.protocol import params, PointerParam, GPU_LIST, LEVEL_ADVANCED
from pyworkflow.utils import removeBaseExt
from pyworkflow.utils.properties import Message
from tomo.objects import Tomogram, TomoMask, SetOfTomoMasks
from tomo.protocols import ProtTomoPicking

from deepfinder import Plugin
from deepfinder.protocols import ProtDeepFinderBase


class DFSegmentOutputs(Enum):
    segmentations = SetOfTomoMasks


class DeepFinderSegment(ProtTomoPicking, ProtDeepFinderBase):
    """This protocol segments tomograms, using a trained neural network."""

    _label = 'segment'
    _possibleOutputs = DFSegmentOutputs

    # --------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        ProtTomoPicking._defineParams(self, form)

        form.addParam('weights', PointerParam,
                      pointerClass='DeepFinderNet',
                      label="Neural network model",
                      important=True,
                      help='Select a trained DeepFinder neural network.')

        form.addParam('psize', params.IntParam,
                      default=100,
                      label='Patch size',
                      help='It must be a multiple of 4, due to the network architecture.')

        form.addHidden(GPU_LIST, params.StringParam, default='0',
                       expertLevel=LEVEL_ADVANCED,
                       label="Choose GPU IDs",
                       help="GPU ID, normally it is 0.")

    # --------------------------- INSERT steps functions ----------------------
    def _insertAllSteps(self):
        tomoList = [tomo.clone() for tomo in self.inputTomograms.get()]
        for tomo in tomoList:
            self._insertFunctionStep(self.launchSegmentationStep, tomo)
            self._insertFunctionStep(self.createOutputStep, tomo)

    # --------------------------- STEPS functions -----------------------------
    def launchSegmentationStep(self, tomo):
        outputFileName = self._genOutputFileName(tomo)

        # Launch annotation GUI passing the tomogram file name
        deepfinder_args = '-t ' + tomo.getFileName()
        deepfinder_args += ' -w ' + self.weights.get().getPath()  # FIXME: Return object from pointer
        deepfinder_args += ' -c ' + str(self.weights.get().getNbOfClasses())
        deepfinder_args += ' -p ' + str(self.psize)
        deepfinder_args += ' -o ' + abspath(self._getExtraPath(outputFileName))

        Plugin.runDeepFinder(self, 'segment', deepfinder_args, gpuId=getattr(self, GPU_LIST).get())

    def createOutputStep(self, tomo):
        tomoMaskSet = getattr(self, self._possibleOutputs.segmentations.name, None)
        if not tomoMaskSet:
            tomoMaskSet = SetOfTomoMasks.create(self._getPath(), template='setOfTomoMasks%s.sqlite')
            tomoMaskSet.copyInfo(self.inputTomograms.get())
            tomoMaskSet.setDim(self.inputTomograms.get().getDimensions())
            tomoMaskSet.setName('segmented tomogram set')

        tomoMaskName = self._genOutputFileName(tomo)
        # Import generated target from extra folder and store into TomoMask object:
        tomoMask = TomoMask()
        tomoMask.cleanObjId()
        tomoMask.copyInfo(tomo)
        tomoMask.setFileName(self._getExtraPath(tomoMaskName))

        # Link to origin tomogram:
        tomoMask.setVolName(tomo.getFileName())
        tomoMaskSet.append(tomoMask)

        # Link to output:
        self._defineOutputs(**{self._possibleOutputs.segmentations.name: tomoMaskSet})
        self._defineSourceRelation(self.weights, tomoMaskSet)
        self._defineSourceRelation(self.inputTomograms, tomoMaskSet)

    # --------------------------- INFO functions ----------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []

        if self.isFinished():
            summary.append("Segmentation finished.")
        return summary

    def getMethods(self, output):
        msg = 'User picked %d particles ' % output.getSize()
        return msg

    def _methods(self):
        methodsMsgs = []
        tomoMaskSet = getattr(self, self._possibleOutputs.segmentations.name, None)

        if self.inputTomograms is None:
            return ['Input tomogram not available yet.']

        methodsMsgs.append("Input tomograms imported of dims %s." % (
            str(self.inputTomograms.get().getDim())))

        if tomoMaskSet.getSize() >= 1:
            for key, output in self.iterOutputAttributes():
                msg = self.getMethods(output)
                methodsMsgs.append("%s: %s" % (self.getObjectTag(output), msg))
        else:
            methodsMsgs.append(Message.TEXT_NO_OUTPUT_CO)

        return methodsMsgs

    # --------------------------- UTILS functions ----------------------
    def _genOutputData(self, fileList, suffix):
        outputSetOfTomo = self._createSetOfTomograms(suffix=suffix)
        outputSetOfTomo.copyInfo(self.inputTomograms.get())
        for i, inTomo in enumerate(self.inputTomograms.get()):
            tomo = Tomogram()
            tomo.setLocation(self._getExtraPath(fileList[i]))
            tomo.setSamplingRate(inTomo.getSamplingRate())
            outputSetOfTomo.append(tomo)

        return outputSetOfTomo

    @staticmethod
    def _genOutputFileName(tomo):
        return 'segmentation_' + removeBaseExt(tomo.getFileName()) + '.mrc'
