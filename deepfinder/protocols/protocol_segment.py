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
from pyworkflow.object import Integer, Set
from pyworkflow.protocol import Protocol, params, IntParam, EnumParam, PointerParam
from pyworkflow.utils.properties import Message
from tomo.protocols import ProtTomoPicking
from tomo.objects import Coordinate3D, Tomogram
from deepfinder.objects import DeepFinderNet

from deepfinder import Plugin
import deepfinder.convert as cv
from deepfinder.objects import DeepFinderSegmentation, SetOfDeepFinderSegmentations

import os

"""
Describe your python module here:
This module will provide the traditional Hello world example
"""

class DeepFinderSegmentation(ProtTomoPicking):
    """This protocol segments tomograms, using a trained neural network."""

    _label = 'segment'

    # --------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        ProtTomoPicking._defineParams(self, form)

        form.addParam('weights', PointerParam,
                      pointerClass='DeepFinderNet',
                      label="Neural network model", important=True,
                      help='Select a trained DeepFinder neural network.')

        form.addParam('Ncl', params.IntParam,
                      default=100,
                      label='Number of classes', important=True,
                      help='Number of classes, background included')

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
            deepfinder_args += ' -w ' + self.weights.getPath()
            deepfinder_args += ' -c ' + str(self.Ncl)
            deepfinder_args += ' -p ' + str(self.psize)
            deepfinder_args += ' -o ' + os.path.abspath(os.path.join(self._getExtraPath(), fname_segm))
            if self.bin:
                deepfinder_args += ' -bin '
            Plugin.runDeepFinder(self, 'segment', deepfinder_args)

    def createOutputStep(self):
        for tomo in self.inputTomograms.get().iterItems():
            # Generate objl filename (output):
            fname_tomo = os.path.splitext(tomo.getFileName())
            fname_tomo = os.path.basename(fname_tomo[0])
            fname_segm = 'segmentation_' + fname_tomo + '.mrc'

            # Import generated target from tmp folder and and store into segmentation object:
            segm = DeepFinderSegmentation()
            segm.cleanObjId()
            segm.setFileName(fname_segm)

            # Link to origin tomogram:
            tomoname = tomo.getFileName()
            segm.setTomoName(tomoname)

            # Link to output:
            name = 'segmentation_' + fname_tomo
            args = {}
            args[name] = segm

            self._defineOutputs(**args)


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
