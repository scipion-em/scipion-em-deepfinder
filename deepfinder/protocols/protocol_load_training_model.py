from enum import Enum

from pwem.protocols import EMProtocol, FileParam
from pyworkflow.protocol import IntParam, GT
from pyworkflow.utils import Message
from deepfinder.objects import DeepFinderNet


class DFImportModelOutputs(Enum):
    netWeights = DeepFinderNet


class ProtDeepFinderLoadTrainingModel(EMProtocol):
    """
    Loads a previously trained DeepFinder neural network model together
    with its associated class configuration so it can be reused for
    segmentation and inference workflows in cryo-electron tomography.

    AI Generated:

    Load Training Model (ProtDeepFinderLoadTrainingModel) — User Manual
        Overview

        The Load Training Model protocol imports an existing DeepFinder
        neural network model into the processing environment so it can
        be applied to tomogram segmentation and related downstream
        analyses. Its main purpose is to make trained neural networks
        available as reusable biological tools without requiring the
        user to repeat the training process.

        In cryo-electron tomography workflows, neural network training
        can be computationally expensive and time consuming. Once a
        model has been trained successfully, researchers often reuse it
        across multiple datasets, projects, or biological conditions.
        This protocol provides a convenient way to register those models
        for later inference and segmentation tasks.

        Biological Context and Motivation

        Deep learning models used in cryo-ET segmentation encode
        biological knowledge derived from annotated training data. The
        imported model therefore represents a learned interpretation of
        structural patterns present in tomograms, including molecular
        complexes, organelles, membranes, viral particles, or other
        biologically meaningful classes.

        Reusing trained models is especially valuable when working with
        similar experimental conditions or related biological systems.
        For example, a model trained on bacterial ribosomes, membrane
        vesicles, or filamentous assemblies may be applied to newly
        acquired tomograms with comparable imaging conditions and voxel
        sizes.

        Inputs and General Workflow

        The protocol requires a neural network weights file together
        with the number of biological classes represented by the model.
        These classes define the structural categories that the network
        can recognize during segmentation.

        Once imported, the model becomes available for subsequent
        protocols that require a DeepFinder neural network input. This
        allows users to separate the computationally intensive training
        stage from the biological interpretation and inference stages.

        Understanding the Number of Classes

        The number of classes is a biologically important parameter
        because it defines the semantic categories recognized by the
        neural network. These classes typically correspond to annotated
        structures used during training, such as membranes, ribosomes,
        viral capsids, cytoskeletal filaments, or background regions.

        In segmentation workflows, the background is generally treated
        as an additional class. Biological users should therefore ensure
        that the imported class count matches the original training
        configuration to avoid inconsistencies during prediction and
        interpretation.

        Compatibility Considerations

        Successful reuse of a neural network model depends strongly on
        compatibility between the original training data and the new
        tomograms to be analyzed. Differences in voxel size, contrast,
        denoising procedures, reconstruction methods, or biological
        composition may reduce segmentation accuracy.

        Models generally perform best when applied to datasets that
        resemble the conditions present during training. Applying a
        network to highly different biological systems or acquisition
        conditions may lead to unstable predictions or biologically
        misleading segmentations.

        Outputs and Their Interpretation

        The protocol produces a reusable DeepFinder neural network
        object that can be connected directly to segmentation protocols.
        This output encapsulates both the trained weights and the class
        information required for biological inference.

        The imported model itself does not yet generate biological
        segmentations. Instead, it serves as the foundation for later
        prediction workflows in which tomograms are analyzed and
        converted into annotated volumetric maps.

        Practical Recommendations

        Before importing a model, users should verify that the weights
        file corresponds to a completed and validated training process.
        It is advisable to maintain clear documentation regarding the
        biological classes, voxel size, preprocessing strategy, and
        training dataset associated with each model.

        When multiple models are available, selecting the most suitable
        one should depend on the similarity between the original
        training conditions and the intended biological application.
        Models specialized for one organism, cellular compartment, or
        imaging condition may not generalize reliably to unrelated
        datasets.

        Final Perspective

        Reusable neural network models are central components of modern
        cryo-electron tomography workflows because they enable rapid and
        scalable biological interpretation of volumetric data. By
        importing validated DeepFinder models into the analysis
        environment, researchers can efficiently apply previously
        learned structural knowledge to new tomographic datasets while
        preserving consistency across experiments and projects.
    """

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
