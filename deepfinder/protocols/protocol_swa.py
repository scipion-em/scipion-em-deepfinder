# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors: Scipion Team
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
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
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
from enum import Enum
from os.path import abspath

from deepfinder import Plugin
from pwem.protocols import EMProtocol
from pyworkflow.protocol import params, MultiPointerParam, GPU_LIST, LEVEL_ADVANCED
from pyworkflow.utils.properties import Message

from deepfinder.objects import DeepFinderNet

ARCHITECTURE_CHOICES = ['unet', 'resunet']


class DFSWAOutputs(Enum):
    netWeights = DeepFinderNet


class DeepFinderSWA(EMProtocol):
    """This protocol performs Stochastic Weight Averaging (SWA): it averages, layer by layer,
    the weights of two or more previously trained DeepFinder network models, producing a
    single new network model. All the selected weight files must correspond to networks of
    the same architecture and number of classes."""

    _label = 'swa'
    _possibleOutputs = DFSWAOutputs

    def __init__(self, **args):
        EMProtocol.__init__(self, **args)
        self.nClass = None

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputWeights', MultiPointerParam,
                      pointerClass='DeepFinderNet',
                      minNumObjects=2,
                      maxNumObjects=0,
                      label="Network weights",
                      important=True,
                      help='Select 2 or more trained DeepFinder network models (outputs of the '
                           '"train" or "Load Training Model" protocols) whose weights will be '
                           'averaged (Stochastic Weight Averaging). All the selected models must '
                           'share the same architecture, patch size and number of classes.')

        form.addParam('architecture', params.EnumParam,
                      display=params.EnumParam.DISPLAY_COMBO,
                      default=0,  # 'unet'
                      choices=ARCHITECTURE_CHOICES,
                      label='Architecture',
                      help='Network architecture shared by all the selected weight files.')

        form.addHidden(GPU_LIST, params.StringParam, default='0',
                       expertLevel=LEVEL_ADVANCED,
                       label="Choose GPU IDs",
                       help="GPU ID, normally it is 0.")

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep(self.swaStep)
        self._insertFunctionStep(self.createOutputStep)

    def swaStep(self):
        self.nClass = self.inputWeights[0].get().getNbOfClasses()

        deepfinder_args = '-w ' + ' '.join(abspath(w.get().getPath()) for w in self.inputWeights)
        deepfinder_args += ' -c ' + str(self.nClass)
        deepfinder_args += ' -p 48 ' # 'Patch size used to (re)build the models before loading. It must be a multiple of 4, but the value will not change the weights'
        deepfinder_args += ' -o ' + abspath(self._getExtraPath('swa_weights.h5'))
        # to allow backward compatability, --model is only passed if not 'unet'
        if ARCHITECTURE_CHOICES[self.architecture.get()] != 'unet':
            deepfinder_args += ' --model ' + ARCHITECTURE_CHOICES[self.architecture.get()]

        Plugin.runDeepFinder(self, 'swa', deepfinder_args, useGPU=True)

    def createOutputStep(self):
        netWeights = DeepFinderNet(path=abspath(self._getExtraPath('swa_weights.h5')),
                                   noClasses=self.nClass)
        self._defineOutputs(**{self._possibleOutputs.netWeights.name: netWeights})
        for w in self.inputWeights:
            self._defineSourceRelation(w, netWeights)

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        summary = []

        if self.isFinished():
            netWeights = getattr(self, self._possibleOutputs.netWeights.name, None)
            nClasses = netWeights.getNbOfClasses() if netWeights else self.inputWeights[0].get().getNbOfClasses()
            summary.append("Averaged *{}* network models (*{}* architecture) with Stochastic Weight "
                           "Averaging.\nNumber of classes = *{}* (background class included).".format(
                            len(self.inputWeights), ARCHITECTURE_CHOICES[self.architecture.get()], nClasses))

        return summary

    def _validate(self):
        errorMsg = []

        if len(self.inputWeights) < 2:
            errorMsg.append('Please select at least 2 network weight files to average.')
        else:
            nClassSet = {w.get().getNbOfClasses() for w in self.inputWeights}
            if len(nClassSet) > 1:
                errorMsg.append('All the selected network weights must have the same number of classes.')

        return errorMsg
