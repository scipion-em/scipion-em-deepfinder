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
from os.path import abspath

from pyworkflow import BETA
from pyworkflow.protocol import params, PointerParam
from pyworkflow.utils import removeBaseExt
from pyworkflow.utils.properties import Message

from pwem.protocols import EMProtocol
from tomo.protocols import ProtTomoBase
from tomo.objects import TomoMask, SetOfTomoMasks, SetOfTomograms

from deepfinder import Plugin
import deepfinder.convert as cv
from deepfinder.protocols import ProtDeepFinderBase


class DeepFinderGenerateTrainingTargetsSpheres(EMProtocol, ProtDeepFinderBase, ProtTomoBase):
    """ This protocol generates segmentation maps from annotations. These segmentation maps will be used as targets
     to train DeepFinder """

    _label = 'generate sphere target'
    _devStatus = BETA

    def __init__(self, **args):
        EMProtocol.__init__(self, **args)
        self.targetname_list = []
        self.tomoSet = None
        self.coord3DSet = None

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
                      label='Sphere radii', important=True,
                      help='Sphere radius, in voxels,  per class. Should be separated by coma as follows: '
                           'Rclass1,Rclass2, ...')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        self._initialize()
        self._insertFunctionStep('launchTargetGenerationStep')
        self._insertFunctionStep('createOutputStep')

    def launchTargetGenerationStep(self):

        self.tomoSet = self.inputCoordinates.get().getPrecedents()

        # Prepare parameter file for DeepFinder. First, set parameters that are common to all targets to be generated:
        param = cv.ParamsGenTarget()
        # Set strategy:
        param.strategy = 'spheres'
        # Set radius list:
        radius_list_string = self.sphereRadii.get()
        radius_list = [int(r) for r in radius_list_string.split(',')]
        param.radius_list = radius_list
        # Set optional volume for target initialization:
        #if self.initialVolume.get():  # TODO should be 1 initial vol per target
        #    param.path_initial_vol = self.initialVolume.get().getFileName()

        objl_tomoList = self._getObjlFromInputCoordinates(self.inputCoordinates.get())

        # --------------------------------------------------------------------------------------------------------------
        # Now, set parameters specific to each tomogram:
        for tidx, tomo in enumerate(self.tomoSet):
            # Get objl for tomogram and save objl to extra folder:
            objl_tomo = cv.objl_get_tomo(objl_tomoList, tomo.getObjId())
            fname_objl = abspath(self._getExtraPath('objl.xml'))
            cv.objl_write(objl_tomo, fname_objl)

            param.path_objl = fname_objl

            # Set tomogram size:
            dimX, dimY, dimZ = tomo.getDimensions()
            param.tomo_size = (dimZ, dimY, dimX)

            # Set path to where write the generated target:
            fname_target = self._getExtraPath('target_' + removeBaseExt(tomo.getFileName()) + '.mrc')
            self.targetname_list.append(fname_target)
            param.path_target = abspath(fname_target)

            # Save the parameter file:
            fname_params = abspath(self._getExtraPath('params_target_generation_%i.xml' % tidx))
            param.write(fname_params)

            # Launch DeepFinder target generation:
            deepfinder_args = '-p ' + fname_params
            Plugin.runDeepFinder(self, 'generate_target', deepfinder_args)

    def createOutputStep(self):
        targetSet = SetOfTomoMasks.create(self._getPath(), template='setOfTomoMasks%s.sqlite')
        targetSet.copyInfo(self.tomoSet)
        targetSet.setName('sphere target set')

        for tomo, targetname in zip(self.tomoSet, self.targetname_list):

            # Import generated target from tmp folder and and store into segmentation object:
            target = TomoMask()
            target.cleanObjId()
            target.copyInfo(tomo)
            target.setFileName(targetname)

            # Link to origin tomogram:
            target.setVolName(tomo.getFileName())

            targetSet.append(target)

        # Link to output:
        # targetSet.write() # FIXME: EMProtocol is the one that has the method to save Sets
        self._defineOutputs(outputTargetSet=targetSet)
        self._defineSourceRelation(self.inputCoordinates, targetSet)

    def _initialize(self):
        self.coord3DSet = self.inputCoordinates.get()
        self.tomoSet = self.coord3DSet.getPrecedents()

    # --------------------------- INFO functions ----------------------------------- # TODO
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


