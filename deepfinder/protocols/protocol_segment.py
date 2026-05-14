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
import logging
from enum import Enum
from os.path import abspath
from pyworkflow.protocol import params, PointerParam, GPU_LIST, LEVEL_ADVANCED, STEPS_PARALLEL
from pyworkflow.utils import removeBaseExt, cyanStr
from pyworkflow.utils.properties import Message
from tomo.objects import Tomogram, TomoMask, SetOfTomoMasks
from tomo.protocols import ProtTomoPicking
from deepfinder import Plugin
from deepfinder.protocols import ProtDeepFinderBase

logger = logging.getLogger(__name__)


class DFSegmentOutputs(Enum):
    segmentations = SetOfTomoMasks


class DeepFinderSegment(ProtTomoPicking, ProtDeepFinderBase):
    """
    Segments tomograms using a trained DeepFinder neural network model in order
    to identify and classify structural regions within cryo-electron tomography
    data.

    AI Generated:

    DeepFinder Segment (DeepFinderSegment) — User Manual
        Overview

        The DeepFinder Segment protocol performs semantic segmentation of
        tomographic volumes using a previously trained DeepFinder neural
        network. Its purpose is to assign class identities to voxels within
        tomograms, producing annotated volumetric maps that highlight biological
        structures, molecular assemblies, or cellular regions of interest.

        In cryo-electron tomography workflows, segmentation is a key step for
        interpreting crowded intracellular environments and locating meaningful
        biological features inside noisy three-dimensional data. Rather than
        focusing on isolated particles alone, this protocol enables the study
        of spatial organization, macromolecular distributions, and structural
        context directly within tomograms.

        Biological Context and Applications

        Segmentation is especially valuable in cellular cryo-ET studies where
        many different structures coexist within the same reconstructed volume.
        Biological users commonly employ this protocol to identify membranes,
        ribosomes, filaments, vesicles, viral particles, or other annotated
        macromolecular complexes that were previously represented during network
        training.

        The quality and biological reliability of the segmentation strongly
        depend on the representativeness of the training data used to create
        the neural network model. Networks trained on diverse examples and
        realistic annotations generally provide more robust predictions across
        different tomograms and acquisition conditions.

        Inputs and General Workflow

        The protocol requires two principal inputs: a set of tomograms to be
        segmented and a trained DeepFinder neural network model. The neural
        network defines the classes that can be recognized during prediction,
        while the tomograms provide the volumetric data to analyze.

        During execution, each tomogram is processed independently and converted
        into a segmentation map in which voxel values correspond to predicted
        biological classes. The resulting segmented tomograms preserve the
        spatial geometry of the original data, allowing direct visualization
        and downstream analysis in the native tomographic coordinate system.

        Patch Size and Segmentation Strategy

        Segmentation is performed by analyzing the tomogram in volumetric
        patches. The patch size determines the amount of structural context
        visible to the neural network during prediction. Larger patches provide
        broader contextual information that may improve recognition of extended
        or complex structures, while smaller patches reduce memory consumption
        and may accelerate execution.

        From a biological perspective, the patch size should be large enough to
        capture the complete morphology of the structures being segmented.
        Extremely small patches may fail to provide sufficient contextual
        information for distinguishing neighboring biological components,
        particularly in crowded cellular environments.

        GPU Acceleration and Computational Considerations

        The protocol is designed to use GPU acceleration for neural network
        inference. This substantially reduces processing time, especially for
        large tomograms or datasets containing multiple volumes. Segmentation of
        high-resolution tomograms can be computationally demanding, and users
        should ensure that sufficient GPU memory is available for the selected
        patch size.

        Parallel execution allows independent tomograms to be segmented
        efficiently, making the protocol suitable for facility-scale cryo-ET
        pipelines and large biological studies involving many datasets.

        Outputs and Their Interpretation

        The protocol produces segmented tomograms in which voxel intensities
        represent predicted structural classes. These segmentation maps can be
        visualized directly alongside the original tomograms to inspect the
        biological plausibility of the predictions.

        The outputs are especially useful for downstream analyses such as object
        extraction, structural quantification, spatial statistics, subtomogram
        averaging preparation, or visualization of cellular architecture.
        Segmented regions may also serve as masks for focused analysis or as
        guides for manual curation.

        Biological interpretation should always include visual inspection of
        the segmentation quality. Neural network predictions may contain false
        positives, incomplete boundaries, or ambiguities in regions with low
        signal-to-noise ratio. Careful validation against known structural
        features or experimental expectations is therefore recommended.

        Practical Recommendations

        For most biological applications, the best results are obtained when
        the neural network has been trained using tomograms that resemble the
        experimental data in resolution, contrast, voxel size, and biological
        composition. Significant differences between training and prediction
        datasets may reduce segmentation accuracy.

        Users should begin by segmenting a small subset of representative
        tomograms and visually evaluating the outputs before scaling to large
        datasets. If predictions appear fragmented or biologically inconsistent,
        retraining the network with improved annotations or more diverse
        training examples is often more effective than modifying segmentation
        parameters alone.

        Structures that are rare, highly flexible, or poorly contrasted may
        require additional annotated examples during training to achieve
        reliable detection. Similarly, densely packed cellular regions may
        benefit from carefully curated training annotations that clearly
        separate neighboring biological entities.

        Final Perspective

        Semantic segmentation is one of the most powerful approaches for
        interpreting complex cryo-electron tomography data because it transforms
        noisy volumetric reconstructions into biologically organized maps. By
        combining deep learning with volumetric structural information, the
        DeepFinder Segment protocol enables researchers to study molecular
        organization directly inside cells and heterogeneous environments.

        Reliable segmentation depends not only on computational performance but
        also on biologically meaningful training data, thoughtful validation,
        and careful interpretation of predicted structures within their native
        cellular context.
    """

    _label = 'segment'
    _possibleOutputs = DFSegmentOutputs
    stepsExecutionMode = STEPS_PARALLEL

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tomoDict = None

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

        form.addParallelSection(threads=1, mpi=0)

    # --------------------------- INSERT steps functions ----------------------
    def _insertAllSteps(self):
        self.__initialize()
        closeDpes = []
        for tsId in self.tomoDict.keys():
            segId = self._insertFunctionStep(self.launchSegmentationStep, tsId,
                                             prerequisites=[],
                                             needsGPU=True)
            cOutId = self._insertFunctionStep(self.createOutputStep, tsId,
                                              prerequisites=segId,
                                              needsGPU=False)
            closeDpes.append(cOutId)
        # Add a final step to close the sets
        self._insertFunctionStep(self._closeOutputSet,
                                 prerequisites=closeDpes,
                                 needsGPU=False)

    # --------------------------- STEPS functions -----------------------------
    def __initialize(self):
        self.tomoDict = {tomo.getTsId(): tomo.clone() for tomo in self.inputTomograms.get()}

    def launchSegmentationStep(self, tsId: str):
        logger.info(cyanStr(f'Segmenting step of ---> {tsId}'))
        tomo = self.tomoDict[tsId]
        outputFileName = self._genOutputFileName(tomo)

        # Launch annotation GUI passing the tomogram file name
        deepfinder_args = '-t ' + tomo.getFileName()
        deepfinder_args += ' -w ' + self.weights.get().getPath()  # FIXME: Return object from pointer
        deepfinder_args += ' -c ' + str(self.weights.get().getNbOfClasses())
        deepfinder_args += ' -p ' + str(self.psize)
        deepfinder_args += ' -o ' + abspath(self._getExtraPath(outputFileName))

        Plugin.runDeepFinder(self, 'segment', deepfinder_args, useGPU=True)

    def createOutputStep(self, tsId: str):
        with self._lock:
            logger.info(cyanStr(f'Generating the output of ---> {tsId}'))
            tomo = self.tomoDict[tsId]
            tomoMaskSet = self.createOutputSet()

            tomoMaskName = self._genOutputFileName(tomo)
            # Import generated target from extra folder and store into TomoMask object:
            tomoMask = TomoMask()
            tomoMask.cleanObjId()
            tomoMask.copyInfo(tomo)
            tomoMask.setFileName(self._getExtraPath(tomoMaskName))

            # Link to origin tomogram:
            tomoMask.setVolName(tomo.getFileName())
            tomoMaskSet.append(tomoMask)
            self._store(tomoMaskSet)

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

    def createOutputSet(self) -> SetOfTomoMasks:
        tomoMaskSet = getattr(self, self._possibleOutputs.segmentations.name, None)
        if tomoMaskSet:
            tomoMaskSet.enableAppend()
        else:
            inTomosPointer = self.inputTomograms
            inTomos = inTomosPointer.get()
            tomoMaskSet = SetOfTomoMasks.create(self._getPath(), template='setOfTomoMasks%s.sqlite')
            tomoMaskSet.copyInfo(inTomos)
            tomoMaskSet.setDim(inTomos.getDimensions())
            tomoMaskSet.setName('segmented tomogram set')
            tomoMaskSet.setStreamState(tomoMaskSet.STREAM_OPEN)

            # Link to output:
            self._defineOutputs(**{self._possibleOutputs.segmentations.name: tomoMaskSet})
            self._defineSourceRelation(self.weights, tomoMaskSet)
            self._defineSourceRelation(inTomosPointer, tomoMaskSet)

        return tomoMaskSet
