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
from pyworkflow.protocol import Protocol, params, IntParam, EnumParam, PointerParam
from pyworkflow.utils.properties import Message
from tomo.protocols import ProtTomoPicking

from deepfinder import Plugin
from deepfinder.objects import DeepFinderSegmentation
from deepfinder.protocols import ProtDeepFinderBase

import os

"""
Describe your python module here:
This module will provide the traditional Hello world example
"""

class DeepFinderSegment(ProtTomoPicking, ProtDeepFinderBase):
    """This protocol segments tomograms, using a trained neural network."""

    _label = 'segment'

    # --------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        ProtTomoPicking._defineParams(self, form)

        form.addParam('weights', PointerParam,
                      pointerClass='DeepFinderNet',
                      label="Neural network model", important=True,
                      help='Select a trained DeepFinder neural network.')

        #form.addParam('Ncl', params.IntParam,
        #              default=100,
        #              label='Number of classes', important=True,
        #              help='Number of classes, background included')

        form.addParam('psize', params.IntParam,
                      default=100,
                      label='Patch size', important=True,
                      help='')

        form.addParam('bin', params.BooleanParam,
                      default=True,
                      label='Binning', important=True,
                      help='If selected, also saves a binned version of the segmentation. Useful for speeding up cluster protocol.')


    # --------------------------- INSERT steps functions ----------------------
    def _insertAllSteps(self):

        # Launch Boxing GUI
        self._insertFunctionStep('launchSegmentationStep')
        self._insertFunctionStep('createOutputStep')

    # --------------------------- STEPS functions -----------------------------
    def launchSegmentationStep(self):
        for tomo in self.inputTomograms.get().iterItems():
            # Generate objl filename (output):
            fname_tomo = os.path.splitext( tomo.getFileName() )
            fname_tomo = os.path.basename(fname_tomo[0])
            fname_segm = 'segmentation_'+fname_tomo+'.mrc'

            # Launch annotation GUI passing the tomogram file name
            deepfinder_args = '-t ' + tomo.getFileName()
            deepfinder_args += ' -w ' + self.weights.get().getPath() # FIXME: Return object from pointer
            deepfinder_args += ' -c ' + str(self.weights.get().getNbOfClasses())
            deepfinder_args += ' -p ' + str(self.psize)
            deepfinder_args += ' -o ' + os.path.abspath(os.path.join(self._getExtraPath(), fname_segm))
            if self.bin:
                deepfinder_args += ' -bin '
            Plugin.runDeepFinder(self, 'segment', deepfinder_args)

    def createOutputStep(self):
        segmSet = self._createSetOfDeepFinderSegmentations()
        segmSet.setName('segmentation set')

        for tomo in self.inputTomograms.get().iterItems():
            # Generate objl filename (output):
            fname_tomo = os.path.splitext(tomo.getFileName())
            fname_tomo = os.path.basename(fname_tomo[0])
            fname_segm = 'segmentation_' + fname_tomo + '.mrc'
            fname_segm = os.path.abspath(os.path.join(self._getExtraPath(), fname_segm))

            # Import generated target from tmp folder and and store into segmentation object:
            segm = DeepFinderSegmentation()
            segm.cleanObjId()
            segm.setFileName(fname_segm)

            # Link to origin tomogram:
            tomoname = tomo.getFileName()
            segm.setTomoName(tomoname)

            # Append to set:
            segmSet.append(segm)

        # Link to output:
        # targetSet.write() # FIXME: EMProtocol is the one that has the method to save Sets
        self._defineOutputs(outputSegmentationSet=segmSet)
        self._defineSourceRelation(self.inputTomograms, segmSet)


        # If 'bin' option is checked, also link binned segmentation maps to output.
        # I have to do this in a separate loop because only one set can be open at a time
        # else error: Protocol failed: Cannot operate on a closed database
        if self.bin:
            segmSetBin = self._createSetOfDeepFinderSegmentations()
            segmSetBin.setName('binned segmentation set')

            for tomo in self.inputTomograms.get().iterItems():
                # Generate objl filename (output):
                fname_tomo = os.path.splitext(tomo.getFileName())
                fname_tomo = os.path.basename(fname_tomo[0])
                fname_segm = 'segmentation_' + fname_tomo + '_binned.mrc'
                fname_segm = os.path.abspath(os.path.join(self._getExtraPath(), fname_segm))

                # Import generated target from tmp folder and and store into segmentation object:
                segm = DeepFinderSegmentation()
                segm.cleanObjId()
                segm.setFileName(fname_segm)

                # Link to origin tomogram:
                tomoname = tomo.getFileName()
                segm.setTomoName(tomoname)

                # Append to set:
                segmSetBin.append(segm)

            self._defineOutputs(outputSegmentationSetBinned=segmSetBin)
            self._defineSourceRelation(self.inputTomograms, segmSetBin)


    # --------------------------- DEFINE info functions ---------------------- # TODO
    def getMethods(self, output):
        msg = 'User picked %d particles ' % output.getSize()
        return msg

    def _methods(self):
        methodsMsgs = []
        if self.inputTomograms is None:
            return ['Input tomogram not available yet.']

        methodsMsgs.append("Input tomograms imported of dims %s." % (
            str(self.inputTomograms.get().getDim())))

        if self.getOutputsSize() >= 1:
            for key, output in self.iterOutputAttributes():
                msg = self.getMethods(output)
                methodsMsgs.append("%s: %s" % (self.getObjectTag(output), msg))
        else:
            methodsMsgs.append(Message.TEXT_NO_OUTPUT_CO)

        return methodsMsgs
