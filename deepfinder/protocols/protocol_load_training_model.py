from pwem.protocols import EMProtocol, FileParam
from pyworkflow import BETA
from pyworkflow.protocol import IntParam, GT
from pyworkflow.utils import Message

from deepfinder.objects import DeepFinderNet


class ProtDeepFinderLoadTrainingModel(EMProtocol):
    """Use two data-independent reconstructed tomograms to train a 3D cryo-CARE network."""

    _label = 'Load Training Model'
    _devStatus = BETA

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
                      help='Number of classes corresponding to this model (background included).')

    def _insertAllSteps(self):
        self._insertFunctionStep('createOutputStep')

    def createOutputStep(self):
        netWeights = DeepFinderNet()
        netWeights.setPath(self.netWeightsFile.get())
        netWeights.setNbOfClasses(self.numClasses.get())
        self._defineOutputs(netWeights=netWeights)

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        summary = []

        if self.isFinished():
            summary.append("Loaded training model info:\n"
                           "Net weights file = *{}*\n"
                           "Number of classes = *{}*\n".format(
                            self.netWeightsFile.get(), self.numClasses.get()))

        return summary