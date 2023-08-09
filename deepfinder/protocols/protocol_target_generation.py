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
from pyworkflow import BETA
from pyworkflow.object import Set
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
    """ This protocol generates segmentation maps from annotations. These segmentation maps will be used as targets
     to train DeepFinder """

    _label = 'generate sphere targets'
    _devStatus = BETA
    _possibleOutputs = GenTargetsOutputs

    def __init__(self, **args):
        EMProtocol.__init__(self, **args)
        self.stepsExecutionMode = STEPS_PARALLEL
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
        counter = 0
        launchIdList = []
        for tomoDict in tomoDictList:
            launchId = self._insertFunctionStep(self.launchTargetGenerationStep, tomoDict, prerequisites=[])
            launchIdList.append(launchId)
            counter += 1
        self._insertFunctionStep(self.createOutputStep, tomoDictList, prerequisites=launchIdList)

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
        radius_list = [int(r) >= 48 for r in radius_list_string.split(',')]
        if any(radius_list):
            errorMsg.append('None of the radius values introduced should be *smaller than 48 voxels* ('
                            '[https://doi.org/10.1038/s41592-021-01275-4] receptive field '
                            'of the network --> the network would be more likely to detect objects that are smaller '
                            'than or equal to the receptive field size.)\n\n'
                            'Consider downsampling your tomograms so the entities desired to be detected are smaller '
                            'or equal than 48 x 48 x 48 voxels.')
        return errorMsg
