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

class DeepFinderGenerateTrainingTargetsSpheres(Protocol):
    """ This protocol generates segmentation maps from annotations. These segmentation maps will be used as targets
     to train DeepFinder """
    _label = 'generate sphere target'

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputCoordinates', params.MultiPointerParam, label="Input coordinates",
                      pointerClass='SetOfCoordinates3D', help='Select coordinate sets for each class.')

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

        # First, convert the input setOfCoordinates3D to objl, and save objl in tmp folder:
        l = 1 # one class/setOfCoordinate3D. Class labels are reassigned here, and may not correspond to the label from annotation step.
        objl = []
        for pointer in self.inputCoordinates:
            coord3DSet = pointer.get()
            print('-----------------------')
            print(coord3DSet.getSummary())
            print('-----------------------')
            for coord in coord3DSet.iterItems():
                x = coord.getX()
                y = coord.getY()
                z = coord.getZ()
                lbl = l
                cv.objl_add(objl, label=lbl, coord=[z,y,x])
                print('x='+str(x) + ', y=' + str(y) + ', z='+str(z)+', lbl='+str(lbl))
            l+=1
        fname_objl = os.path.abspath(os.path.join(self._getExtraPath(), 'objl.xml'))
        cv.objl_write(objl, fname_objl)

        # Next, prepare and save parameter file for DeepFinder
        params = cv.ParamsGenTarget()
        params.path_objl = fname_objl

        # Set optional volume for target initialization:
        if self.initialVolume.get()!=None:
            params.path_initial_vol = self.initialVolume.get().getFileName()

        # Set tomogram size:
        coord = self.inputCoordinates[0].get().getFirstItem() # take 1st element of 1st setOfCoord3D
        #dimX, dimY, dimZ = coord.getVolume().getDim() # getVolume does not work. So I have to proceed as follows:
        tomo = Tomogram()
        tomo.setFileName(coord.getVolName())
        dimX, dimY, dimZ = tomo.getDim()
        params.tomo_size = (dimZ, dimY, dimX)

        # Set strategy:
        params.strategy = 'spheres'

        # Set radius list:
        radius_list_string = self.sphereRadii.get()
        radius_list = []
        for r in radius_list_string.split(','):radius_list.append(int(r))
        params.radius_list = radius_list
        print('RADIUS LIST : '+str(radius_list))

        # Set path to where write the generated target:
        params.path_target = os.path.abspath(os.path.join(self._getExtraPath(), 'target.mrc'))

        # Save the parameter file:
        fname_params = os.path.abspath(os.path.join(self._getExtraPath(), 'params_target_generation.xml'))
        params.write(fname_params)

        # Launch DeepFinder target generation:
        deepfinder_args = '-p ' + fname_params
        Plugin.runDeepFinder(self, 'generate_target', deepfinder_args)

    def createOutputStep(self):
        # Import generated target from tmp folder and and store into segmentation object:
        target = DeepFinderSegmentation() #Tomogram()

        fname = os.path.abspath(os.path.join(self._getExtraPath(), 'target.mrc'))
        target.setFileName(fname)

        # Link to origin tomogram:
        coord = self.inputCoordinates[0].get().getFirstItem()  # take 1st element of 1st setOfCoord3D
        #tomo = coord.getVolume() # getVolume does not work so I have to proceed as follows
        #target.setTomogram(tomo)
        target.setTomoName(coord.getVolName)

        # Link to output:
        self._defineOutputs(outputTomogram=target)
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


