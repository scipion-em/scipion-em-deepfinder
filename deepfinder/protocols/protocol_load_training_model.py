# **************************************************************************
# *
# * Authors:     Scipion Team
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

from pwem.protocols import EMProtocol, FileParam
from pyworkflow.protocol import IntParam, GT
from pyworkflow.utils import Message
from deepfinder.objects import DeepFinderNet


class DFImportModelOutputs(Enum):
    netWeights = DeepFinderNet


class ProtDeepFinderLoadTrainingModel(EMProtocol):
    """Use two data-independent reconstructed tomograms to train a 3D cryo-CARE network."""

    _label = 'Load Training Model'
    _possibleOutputs = DFImportModelOutputs

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('netWeightsFile', FileParam,
                      label='Model weights file',
                      important=True,
                      allowsNull=False,
                      help='File which contains the weights for the neural network (.h5 file).')
        form.addParam('numClasses', IntParam,
                      label='Number of classes',
                      important=True,
                      allowsNull=False,
                      validators=[GT(0)],
                      help='Number of classes corresponding to this model.')

    def _insertAllSteps(self):
        self.nClasses = self.numClasses.get() + 1  # Include background class
        self._insertFunctionStep(self.createOutputStep)

    def createOutputStep(self):
        netWeights = DeepFinderNet()
        netWeights.setPath(self.netWeightsFile.get())
        netWeights.setNbOfClasses(self.nClasses)
        self._defineOutputs(**{self._possibleOutputs.netWeights.name: netWeights})

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        summary = []

        if self.isFinished():
            summary.append("Loaded training model info:\n"
                           "Net weights file = *{}*\n"
                           "Number of classes = *{}* (background class included)\n".format(
                            self.netWeightsFile.get(), self.numClasses.get() + 1))

        return summary
