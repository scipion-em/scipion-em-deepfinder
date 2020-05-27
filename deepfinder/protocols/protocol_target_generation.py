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

from pwem.protocols import EMProtocol

from tomo.protocols import ProtTomoPicking
from tomo.objects import Coordinate3D, Tomogram

from deepfinder import Plugin
import deepfinder.convert as cv
from deepfinder.objects import DeepFinderSegmentation, SetOfDeepFinderSegmentations

from deepfinder.protocols import ProtDeepFinderBase

import os

"""
Describe your python module here:
This module will provide the traditional Hello world example
"""

class DeepFinderGenerateTrainingTargetsSpheres(EMProtocol, ProtDeepFinderBase):
    """ This protocol generates segmentation maps from annotations. These segmentation maps will be used as targets
     to train DeepFinder """
    _label = 'generate sphere target'

    def __init__(self, **args):
        EMProtocol.__init__(self, **args)
        self.tomoname_list = []
        self.targetname_list = []

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputCoordinates', params.MultiPointerParam, label="Input coordinates",
                      pointerClass='SetOfCoordinates3D', help='1 coordinate set per class. A set may contain coordinates from different tomograms.')

        form.addParam('initialVolume', PointerParam,
                      pointerClass='Tomogram',
                      label="Target initialization", important=True, allowsNull=True,
                      help='For integrating non-macromolecule classes (e.g. membranes).')

        form.addParam('sphereRadii', params.StringParam,
                      default='5,6,...,3',
                      label='Sphere radii', important=True,
                      help='Sphere radius per class. Should be separated by coma as follows: Rclass1,Rclass2,...')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep('launchTargetGenerationStep')
        self._insertFunctionStep('createOutputStep')

    def launchTargetGenerationStep(self):
        # Disclaimer: for now this method supposes that coord3DSets contain coords from 1 single tomogram.
        # TODO: adapt to multi-tomogram
        # check out setOfCoord3D.iterCoordinates(vol): Iterate over the coordinates associated with a tomogram.
        # getPrecedents(): Returns the SetOfTomograms or Tilt Series associated with this SetOfCoordinates

        # --------------------------------------------------------------------------------------------------------------
        # First, get list of unique tomo filenames:
        tomoname_list = []
        for pointer in self.inputCoordinates: # first get all filenames
            coord3DSet = pointer.get()
            samplingRate = coord3DSet.getSamplingRate()
            for coord in coord3DSet.iterItems():
                tomoname_list.append((coord.getVolName(), samplingRate)) # FIXME: Tuple to keep SR for output Step
        tomoname_set = set(tomoname_list)  # insert the list to the set: the set stores only unique values
        tomoname_list = (list(tomoname_set))  # convert the set to the list
        self.tomoname_list = tomoname_list # store as attribute for createOutputStep

        # Then, convert the input setOfCoordinates3D to objl
        l = 1 # one class/setOfCoordinate3D. Class labels are reassigned here, and may not correspond to the label from annotation step.
        objl = []
        for pointer in self.inputCoordinates:
            coord3DSet = pointer.get()
            for coord in coord3DSet.iterItems():
                x = coord.getX()
                y = coord.getY()
                z = coord.getZ()
                lbl = l
                tidx = [idt for idt, item in enumerate(self.tomoname_list)
                        if coord.getVolName() == item[0]]
                cv.objl_add(objl, label=lbl, coord=[z,y,x], tomo_idx=tidx[0])
            l+=1

        #objl = self._getObjlFromInputCoordinates(self.inputCoordinates, tomoname_list)

        # --------------------------------------------------------------------------------------------------------------
        # Prepare parameter file for DeepFinder. First, set parameters that are common to all targets to be generated:
        params = cv.ParamsGenTarget()
        # Set strategy:
        params.strategy = 'spheres'
        # Set radius list:
        radius_list_string = self.sphereRadii.get()
        radius_list = []
        for r in radius_list_string.split(','): radius_list.append(int(r))
        params.radius_list = radius_list
        # Set optional volume for target initialization:
        if self.initialVolume.get() != None: # TODO should be 1 initial vol per target
            params.path_initial_vol = self.initialVolume.get().getFileName()

        # --------------------------------------------------------------------------------------------------------------
        # Now, set parameters specific to each tomogram:
        for tidx,tomo_tuple in enumerate(tomoname_list):
            # Save objl to tmp folder:
            objl_tomo = cv.objl_get_tomo(objl,tidx)
            fname_objl = os.path.abspath(os.path.join(self._getExtraPath(), 'objl.xml'))
            cv.objl_write(objl_tomo, fname_objl)

            params.path_objl = fname_objl

            # Set tomogram size:
            tomo = Tomogram()
            tomo.setFileName(tomo_tuple[0])
            dimX, dimY, dimZ = tomo.getDim()
            params.tomo_size = (dimZ, dimY, dimX)

            # Set path to where write the generated target:
            fname_tomo = os.path.splitext(tomo_tuple[0])
            fname_tomo = os.path.basename(fname_tomo[0])
            fname_target = 'target_' + fname_tomo + '.mrc'
            fname_target = os.path.abspath(os.path.join(self._getExtraPath(), fname_target))
            self.targetname_list.append(fname_target)
            params.path_target = fname_target

            # Save the parameter file:
            fname_params = os.path.abspath(os.path.join(self._getExtraPath(), 'params_target_generation.xml'))
            params.write(fname_params)

            # Launch DeepFinder target generation:
            deepfinder_args = '-p ' + fname_params
            Plugin.runDeepFinder(self, 'generate_target', deepfinder_args)

    def createOutputStep(self):

        targetSet = self._createSetOfDeepFinderSegmentations()
        targetSet.setName('sphere target set')

        for tidx,targetname in enumerate(self.targetname_list):
            # Import generated target from tmp folder and and store into segmentation object:

            target = DeepFinderSegmentation()
            target.cleanObjId()
            target.setFileName(targetname)

            # Link to origin tomogram:
            tomoname = self.tomoname_list[tidx][0]
            target.setTomoName(tomoname)

            # Set sampling rate:
            # tomo = Tomogram()
            # tomo.setFileName(tomoname)
            samplingRate = self.tomoname_list[tidx][1] # FIXME: Fixes Sampling Rate
            target.setSamplingRate(samplingRate)

            targetSet.append(target)

        # Link to output:
        # targetSet.write() # FIXME: EMProtocol is the one that has the method to save Sets
        self._defineOutputs(outputTargetSet=targetSet)
        self._defineSourceRelation(self.inputCoordinates, targetSet)


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


