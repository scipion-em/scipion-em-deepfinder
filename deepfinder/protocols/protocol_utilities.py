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
from pyworkflow import BETA
from pyworkflow.protocol import Protocol, params, IntParam, EnumParam, PointerParam
from pyworkflow.utils.properties import Message
from tomo.protocols import ProtTomoPicking
from tomo.objects import Coordinate3D, Tomogram

from deepfinder.protocols import ProtDeepFinderBase
from deepfinder import Plugin
import deepfinder.convert as cv
# from deepfinder.objects import DeepFinderSegmentation, SetOfDeepFinderSegmentations

import os


class DeepFinderDisplay(Protocol):
    """ This protocol allows you to explore tomograms or segmentation maps with ortho-slices. The seegmentation map
    can be superimposed to the tomogram. Useful for visualising your results."""

    _label = 'display volume'
    _devStatus = BETA

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('tomogram', PointerParam,
                      pointerClass='Tomogram',
                      label="Tomogram", important=True, allowsNull=True,
                      help='Select tomogram to display.')

        form.addParam('segmentation', PointerParam,
                      pointerClass='SetOfDeepFinderSegmentations',
                      label="Segmentation map", important=True, allowsNull=True,
                      help='Select segmentation map to display.')


    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep('displayStep')

    def displayStep(self):
        # TODO only one input: can be Tomogram or DeepFinderSegmentation. Depending on type, different call (as below)

        deepfinder_args = ''
        if self.tomogram.get() != None:
            fname = self.tomogram.get().getFileName()
            deepfinder_args += '-t ' + fname
        if self.segmentation.get() != None:
            for seg in self.segmentation.get().iterItems():
                fname = seg.getFileName()
                deepfinder_args += ' -l ' + fname

                fname_tomo = str(seg.getTomoName())
                if fname_tomo != '':  # if a tomo is linked to segmentation, also display tomo
                    deepfinder_args += ' -t ' + fname_tomo



            # fname = self.segmentation.get().getFileName()
            # deepfinder_args += ' -l ' + fname
            #
            # fname_tomo = str( self.segmentation.get().getTomoName() )
            # if fname_tomo != '': # if a tomo is linked to segmentation, also display tomo
            #     deepfinder_args += ' -t ' + fname_tomo

        # Launch display GUI:
        Plugin.runDeepFinder(self, 'display', deepfinder_args)


    # --------------------------- INFO functions ----------------------------------- # TODO
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []

        if self.isFinished():

            summary.append("This protocol has printed *%s* %i times." % (self.message, self.times))
        return summary

    def _methods(self):
        methods = []

        if self.isFinished():
            methods.append("%s has been printed in this run %i times." % (self.message, self.times))
            if self.previousCount.hasPointer():
                methods.append("Accumulated count from previous runs were %i."
                               " In total, %s messages has been printed."
                               % (self.previousCount, self.count))
        return methods

# class DeepFinderSetifySegmentations(Protocol, ProtDeepFinderBase):
#     """ This protocol will print hello world in the console
#          IMPORTANT: Classes names should be unique, better prefix them"""
#     _label = 'setify segmentations'
#
#     # -------------------------- DEFINE param functions ----------------------
#     def _defineParams(self, form):
#         """ Define the input parameters that will be used.
#         Params:
#             form: this is the form to be populated with sections and params.
#         """
#         # You need a params to belong to a section:
#         form.addSection(label=Message.LABEL_INPUT)
#
#
#         form.addParam('segmentations', params.MultiPointerParam, label="Training coordinates",
#                       pointerClass='DeepFinderSegmentation', help='Select segmentation to be merged into a set.')
#
#     # --------------------------- STEPS functions ------------------------------
#     def _insertAllSteps(self):
#         # Insert processing steps
#         self._insertFunctionStep('setifyStep')
#
#     def setifyStep(self):
#         samplingRate = self.segmentations[0].get().getSamplingRate()
#         segmSet = self._createSetOfDeepFinderSegmentations()
#         segmSet.setSamplingRate(samplingRate)
#         for pointer in self.segmentations:
#             segm = pointer.get()
#             segmSet.append(segm)
#
#         self._defineOutputs(outputSegmentationSet=segmSet)