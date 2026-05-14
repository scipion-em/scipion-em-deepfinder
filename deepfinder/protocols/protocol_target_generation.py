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
from pwem.convert.headers import fixVolume
from pyworkflow.protocol import params, PointerParam, STEPS_PARALLEL
from pyworkflow.utils import removeBaseExt
from pyworkflow.utils.properties import Message
from pwem.protocols import EMProtocol
from tomo.protocols import ProtTomoBase
from tomo.objects import TomoMask, SetOfTomoMasks
from deepfinder import Plugin
import deepfinder.convert as cv
from deepfinder.protocols import ProtDeepFinderBase
import logging
logger = logging.getLogger(__name__)


class GenTargetsOutputs(Enum):
    segmentedTargets = SetOfTomoMasks


class DeepFinderGenerateTrainingTargetsSpheres(EMProtocol, ProtDeepFinderBase, ProtTomoBase):
    """
    Generates segmentation targets for DeepFinder training by converting annotated particle coordinates into
    volumetric spherical labels. These generated targets are designed to provide supervised learning data for
    deep learning based particle detection and segmentation in cryo-electron tomography workflows.

    AI Generated:

    Generate Training Targets Spheres (DeepFinderGenerateTrainingTargetsSpheres) - User Manual
        Overview

        The Generate Training Targets Spheres protocol creates segmentation maps that serve as training targets
        for DeepFinder neural network models. In cryo-electron tomography, manually annotated coordinates are
        often available as particle positions, but neural networks require dense volumetric labels during
        supervised learning. This protocol bridges that gap by transforming coordinate annotations into
        voxel-based target maps in which each particle is represented as a sphere with a biologically meaningful
        radius.

        The protocol is particularly useful during the preparation of training datasets for particle detection,
        semantic segmentation, or object localization workflows. By producing consistent target volumes aligned
        with the original tomograms, it enables the subsequent training of DeepFinder models capable of detecting
        macromolecular complexes directly within tomographic reconstructions.

        Inputs and Biological Context

        The protocol requires a set of 3D coordinates associated with one or more tomograms. These coordinates
        typically originate from manual annotation, template matching, subtomogram averaging workflows, or
        curated particle picking procedures. Each coordinate set may represent one biological class, allowing
        users to generate multiclass segmentation targets suitable for more advanced neural network training.

        In biological practice, the quality of the annotations strongly influences the final model performance.
        Coordinates should correspond to accurately localized particles, ideally centered on structurally
        meaningful regions of the complexes of interest. Poorly centered or inconsistent annotations may
        introduce uncertainty into the training process and reduce detection accuracy.

        Sphere-Based Representation

        The protocol models each annotated particle as a sphere within the target volume. The radius assigned
        to each class defines the approximate spatial extent of the object and therefore determines how the
        network interprets the biological structure during training.

        Choosing an appropriate sphere radius is biologically important. Small radii may fail to represent the
        full spatial occupancy of large complexes, making training unstable or incomplete. Excessively large
        radii may artificially merge neighboring particles or blur class boundaries, particularly in crowded
        cellular environments.

        In practical cryo-ET applications, the radius should approximately reflect the expected particle size
        after considering voxel size and tomogram binning. Users working with ribosomes, membrane complexes,
        viral particles, or cytoskeletal assemblies should adapt the radius values according to the apparent
        dimensions of the structures in the reconstructed tomograms.

        Multiclass Segmentation Training

        The protocol supports the generation of targets for multiple biological classes simultaneously. This is
        especially relevant in cellular tomography projects where several molecular species coexist in the same
        tomogram. Each class can be assigned an independent sphere radius, allowing the training targets to
        better reflect structural diversity across particle populations.

        From a biological perspective, multiclass training enables the neural network to distinguish between
        distinct macromolecular assemblies rather than merely detecting generic particle-like densities. This
        becomes valuable when studying heterogeneous cellular environments, organelle-associated complexes, or
        mixed viral populations.

        Tomogram Geometry and Spatial Consistency

        The generated target maps preserve the geometry and dimensions of the original tomograms. This ensures
        direct voxel correspondence between the tomographic data and the training labels, which is essential
        for stable neural network learning.

        Maintaining this spatial consistency is particularly important in cryo-electron tomography because the
        network must learn contextual relationships between biological structures and surrounding densities.
        Accurate correspondence between annotation and tomographic content improves localization precision and
        reduces ambiguities during inference.

        Parallel Processing and Large Datasets

        The protocol is designed to process multiple tomograms efficiently, making it suitable for modern
        cryo-ET projects involving large annotated datasets. This is especially important in deep learning
        workflows, where robust model training often requires substantial biological variability across many
        tomograms acquired under different imaging conditions.

        In practice, larger and more diverse training datasets generally improve network generalization and
        reduce overfitting. Including tomograms with varying contrast, crowding conditions, and structural
        orientations often leads to more biologically robust detection models.

        Biological Considerations for Radius Selection

        Radius selection should be approached carefully because it directly affects the receptive representation
        seen by the neural network. Structures that appear larger than the effective receptive field of the
        network may not be learned reliably. When particles occupy very large spatial regions, downsampling
        the tomograms prior to target generation may improve training stability and detection performance.

        Biological users should also consider whether the chosen radius emphasizes the full particle envelope
        or only the central core of the structure. In some applications, focusing on compact conserved regions
        may improve detection robustness, especially for flexible assemblies or elongated complexes.

        Outputs and Interpretation

        After execution, the protocol produces a set of tomographic segmentation masks corresponding to the
        generated training targets. Each output volume is associated with its original tomogram and can be used
        directly in downstream DeepFinder training workflows.

        These generated targets are not intended for biological interpretation by themselves. Instead, they act
        as computational supervision maps that teach the neural network how particles are spatially distributed
        within tomographic volumes.

        Practical Recommendations

        In routine cryo-ET deep learning workflows, users should begin with carefully curated coordinate sets
        and biologically realistic sphere radii. Visual inspection of the generated targets is strongly
        recommended before launching network training to ensure that particles are represented correctly and
        that neighboring structures remain distinguishable.

        For densely populated tomograms, slightly smaller radii may help reduce overlap between adjacent
        particles. Conversely, for sparse datasets or low-resolution tomograms, moderately larger radii can
        stabilize training by providing more robust target representations.

        Final Perspective

        The generation of accurate training targets is one of the most important steps in supervised deep
        learning workflows for cryo-electron tomography. Well-designed target maps provide the foundation for
        reliable neural network training and strongly influence the biological quality of subsequent particle
        detection results. Careful selection of annotations, biologically meaningful sphere sizes, and dataset
        diversity are essential for producing robust and interpretable DeepFinder models.
    """

    _label = 'generate sphere targets'
    _possibleOutputs = GenTargetsOutputs

    stepsExecutionMode = STEPS_PARALLEL
    def __init__(self, **args):
        EMProtocol.__init__(self, **args)
        self.tomoSet = None
        self.coord3DSet = None
        self.objlTomoList = None

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputCoordinates', PointerParam,
                      label="Input coordinates",
                      pointerClass='SetOfCoordinates3D',
                      important=True,
                      help='1 coordinate set per class. A set may contain coordinates from different tomograms.')

        form.addParam('sphereRadii', params.StringParam,
                      default='5,6,...,3',
                      label='Sphere radius [pix.]',
                      important=True,
                      help='Sphere radius, in voxels, per class. Should be separated by coma as follows: '
                           'Rclass1,Rclass2, ...')

        form.addParallelSection(threads=4, mpi=1)

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        tomoDictList = self._initialize()
        launchIdList = []
        for tomoDict in tomoDictList:
            launchId = self._insertFunctionStep(self.launchTargetGenerationStep, tomoDict, prerequisites=[], needsGPU=False)
            launchIdList.append(launchId)
        self._insertFunctionStep(self.createOutputStep, tomoDictList, prerequisites=launchIdList, needsGPU=False)

    def _initialize(self):
        self.coord3DSet = self.inputCoordinates.get()
        self.tomoSet = self.coord3DSet.getPrecedents()
        return self._getObjlFromInputCoordinates(self.coord3DSet)

    def launchTargetGenerationStep(self, tomoDict):
        tomo = tomoDict[self.TOMO]
        objl_tomo = tomoDict[self.OBJL]
        fname_params = tomoDict[self.PARAMS_XML]

        logger.info(f'Target generation step of ---> {tomo.getTsId()}')
        # Prepare parameter file for DeepFinder. First, set parameters that are common to all targets to be generated:
        param = cv.ParamsGenTarget()
        # Set strategy:
        param.strategy = 'spheres'
        # Set radius list:
        radius_list_string = self.sphereRadii.get()
        radius_list = [int(r) for r in radius_list_string.split(',')]
        param.radius_list = radius_list

        # Get objl for tomogram and save objl to extra folder:
        fname_objl = abspath(self._getExtraPath(f'objl_{tomo.getTsId()}.xml'))
        cv.objl_write(objl_tomo, fname_objl)

        param.path_objl = fname_objl

        # Set tomogram size:
        dimX, dimY, dimZ = tomo.getDimensions()
        param.tomo_size = (dimZ, dimY, dimX)

        # Set path to where write the generated target:
        param.path_target = abspath(self.getTargetName(tomo))

        # Save the parameter file:
        fname_params = abspath(self._getExtraPath(fname_params))
        param.write(fname_params)

        # Launch DeepFinder target generation:
        deepfinder_args = '-p ' + fname_params
        Plugin.runDeepFinder(self, 'generate_target', deepfinder_args)

    def createOutputStep(self, tomoDictList):
        logger.info('Generating the outputs...')
        targetSet = SetOfTomoMasks.create(self._getPath(), template='setOfTomoMasks%s.sqlite')
        targetSet.copyInfo(self.tomoSet)
        setattr(self, self._possibleOutputs.segmentedTargets.name, targetSet)

        # Import generated target from tmp folder and store into segmentation object:
        for tomoDict in tomoDictList:
            tomo = tomoDict[self.TOMO]
            tomoMaskName = self.getTargetName(tomo)
            fixVolume(tomoMaskName)
            target = TomoMask()
            target.cleanObjId()
            target.copyInfo(tomo)
            target.setFileName(tomoMaskName)
            # Link to origin tomogram:
            target.setVolName(tomo.getFileName())
            targetSet.append(target)

        # Define outputs and relations
        self._defineOutputs(**{self._possibleOutputs.segmentedTargets.name: targetSet})
        self._defineSourceRelation(self.inputCoordinates, targetSet)

    def getTargetName(self, tomo):
        return self._getExtraPath('target_' + removeBaseExt(tomo.getFileName()) + '.mrc')

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []

        if self.isFinished():
            summary.append("Target generation finished.")
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

    def _validate(self):
        errorMsg = []
        radius_list_string = self.sphereRadii.get()
        radius_list = [int(r) >= 24 for r in radius_list_string.split(',')]
        if any(radius_list):
            errorMsg.append('None of the radius values introduced should be *smaller than 24 voxels* ('
                            '[https://doi.org/10.1038/s41592-021-01275-4] receptive field '
                            'of the network --> the network would be more likely to detect objects that are smaller '
                            'than or equal to the receptive field size.)\n\n'
                            'Consider downsampling your tomograms so the entities desired to be detected are smaller '
                            'or equal than 48 x 48 x 48 voxels.')
        return errorMsg
