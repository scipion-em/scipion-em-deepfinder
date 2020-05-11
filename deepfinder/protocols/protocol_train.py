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

from deepfinder import Plugin
import deepfinder.convert as cv
from deepfinder.objects import DeepFinderSegmentation, SetOfDeepFinderSegmentations

import os

"""
Describe your python module here:
This module will provide the traditional Hello world example
"""

class DeepFinderTrain(Protocol):
    """ This protocol will print hello world in the console
     IMPORTANT: Classes names should be unique, better prefix them"""
    _label = 'train'

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('targets', PointerParam,
                      pointerClass='SetOfDeepFinderSegmentations',
                      label="Training examples", important=True,
                      help='Training dataset. Please select here your targets. The corresponding tomogram will be loaded automatically.')

        form.addParam('coordTrain', params.MultiPointerParam, label="Training coordinates",
                      pointerClass='SetOfCoordinates3D', help='Select coordinate sets for training.')

        form.addParam('coordValid', params.MultiPointerParam, label="Validation coordinates",
                      pointerClass='SetOfCoordinates3D', help='Select coordinate sets for validation.')

        form.addParam('psize', params.IntParam,
                      default=56,
                      choices=list(range(24,65,4)),
                      label='Patch size', important=True,
                      help='')

        form.addParam('bsize', params.IntParam,
                      default=25,
                      label='Batch size', important=True,
                      help='')

        form.addParam('epochs', params.IntParam,
                      default=100,
                      label='Number of epochs', important=True,
                      help='')

        form.addParam('stepsPerE', params.IntParam,
                      default=100,
                      label='Steps per epoch', important=True,
                      help='')

        form.addParam('stepsPerV', params.IntParam,
                      default=10,
                      label='Steps per validation', important=True,
                      help='')

        form.addParam('bootstrap', params.BooleanParam,
                      default=True,
                      label='Bootstrap', important=True,
                      help='')

        form.addParam('rndShift', params.IntParam,
                      default=13,
                      label='Random shift', important=True,
                      help='')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep('trainingStep')
        self._insertFunctionStep('createOutputStep')

    def trainingStep(self):
        path_tomo = []
        path_segm = []
        for segm in self.targets.get().iterItems():
            # Generate objl filename (output):
            fname_segm = segm.getFileName()
            fname_tomo = segm.getTomoName()
            path_tomo.append(fname_segm)
            path_segm.append(fname_tomo)

        print(path_tomo)
        print(path_segm)

    def createOutputStep(self):
        pass

    # --------------------------- INFO functions -----------------------------------
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