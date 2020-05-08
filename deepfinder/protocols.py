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
from deepfinder.objects import DeepFinderSegmentation

import os

"""
Describe your python module here:
This module will provide the traditional Hello world example
"""

class DeepFinderPrefixHelloWorld(Protocol):
    """ This protocol will print hello world in the console
     IMPORTANT: Classes names should be unique, better prefix them"""
    _label = 'Hello world'

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('message', params.StringParam,
                      default='Hello world!',
                      label='Message', important=True,
                      help='What will be printed in the console.')

        form.addParam('times', params.IntParam,
                      default=10,
                      label='Times', important=True,
                      help='Times the message will be printed.')

        form.addParam('previousCount', params.IntParam,
                      default=0,
                      allowsNull=True,
                      label='Previous count',
                      help='Previous count of printed messages',
                      allowsPointers=True)
    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep('greetingsStep')
        self._insertFunctionStep('createOutputStep')

    def greetingsStep(self):
        # say what the parameter says!!

        for time in range(0, self.times.get()):
            print(self.message)

    def createOutputStep(self):
        # register how many times the message has been printed
        # Now count will be an accumulated value
        timesPrinted = Integer(self.times.get() + self.previousCount.get())
        self._defineOutputs(count=timesPrinted)

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


class DeepFinderAnnotations(ProtTomoPicking):
    """This protocol allows you to annotate macromolecules in your tomograms, using a visual tool."""

    _label = 'annotations'

    # --------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        ProtTomoPicking._defineParams(self, form)


    # --------------------------- INSERT steps functions ----------------------
    def _insertAllSteps(self):

        # Launch Boxing GUI
        self._insertFunctionStep('launchAnnotationStep')
        self._insertFunctionStep('createOutputStep')

    # --------------------------- STEPS functions -----------------------------
    def launchAnnotationStep(self):

        # This generates 1 objl.xml file per tomogram and stores it in TMP:
        for tomo in self.inputTomograms.get().iterItems():
            # Generate objl filename (output):
            fname_tomo = os.path.splitext( tomo.getFileName() )
            fname_tomo = os.path.basename(fname_tomo[0])
            fname_objl = 'objl_annot_'+fname_tomo+'.xml'

            # Launch annotation GUI passing the tomogram file name
            deepfinder_args = '-t ' + tomo.getFileName()
            deepfinder_args += ' -o ' + os.path.abspath(os.path.join(self._getExtraPath(), fname_objl))
            Plugin.runDeepFinder(self, 'annotation', deepfinder_args)




    def createOutputStep(self):
        # Convert DeepFinder annotation output to Scipion SetOfCoordinates3D
        setTomograms = self.inputTomograms.get()

        # First, determine the classes that have been annotated (check in all object lists):
        objl = []
        for tomo in setTomograms.iterItems():
            # Get objl filename:
            fname_tomo = os.path.splitext(tomo.getFileName())
            fname_tomo = os.path.basename(fname_tomo[0])
            fname_objl = 'objl_annot_' + fname_tomo + '.xml'

            # Read objl:
            objl_tomo = cv.objl_read(os.path.abspath(os.path.join(self._getExtraPath(), fname_objl)))
            objl.extend(objl_tomo)

        lbl_list = cv.objl_get_labels(objl)  # get unique class labels

        # For each class, iterate over all object lists (1 per tomo) and store coordinates
        # in SetOfCoordinates3D (1 per class)
        # Remark: only 1 setOfCoordinates3D can exist at a time, else:
        # "Protocol failed: Cannot operate on a closed database."
        for lbl in lbl_list:
            coord3DSet = self._createSetOfCoordinates3D(setTomograms)
            coord3DSet.setName('Class '+str(lbl))
            coord3DSet.setPrecedents(setTomograms)
            coord3DSet.setSamplingRate(setTomograms.getSamplingRate())

            for tomo in setTomograms.iterItems():
                # Get objl filename:
                fname_tomo = os.path.splitext(tomo.getFileName())
                fname_tomo = os.path.basename(fname_tomo[0])
                fname_objl = 'objl_annot_' + fname_tomo + '.xml'

                # Read objl:
                objl_tomo = cv.objl_read(os.path.abspath(os.path.join(self._getExtraPath(), fname_objl)))
                objl_class = cv.objl_get_class(objl_tomo, lbl)
                for idx in range(len(objl_class)):
                    x = objl_class[idx]['x']
                    y = objl_class[idx]['y']
                    z = objl_class[idx]['z']

                    coord = Coordinate3D()
                    coord.setPosition(x, y, z)
                    coord.setVolume(tomo)
                    coord.setVolName(tomo.getFileName())
                    coord3DSet.append(coord)

            # Link to output:
            name = 'outputCoordinates3Dclass'+str(lbl)
            args = {}
            args[name] = coord3DSet
            coord3DSet.setStreamState(Set.STREAM_OPEN)
            self._defineOutputs(**args)
            self._defineSourceRelation(setTomograms, coord3DSet)

        pass

    # --------------------------- DEFINE info functions ----------------------
    def getMethods(self, output):
        msg = 'User picked %d particles ' % output.getSize()
        return msg

    def _methods(self):
        methodsMsgs = []
        if self.inputTomograms is None:
            return ['Input tomogram not available yet.']

        methodsMsgs.append("Input tomograms imported of dims %s." % (
            str(self.inputTomograms.get().getDim())))

        if self.getOutputsSize() >= 1:
            for key, output in self.iterOutputAttributes():
                msg = self.getMethods(output)
                methodsMsgs.append("%s: %s" % (self.getObjectTag(output), msg))
        else:
            methodsMsgs.append(Message.TEXT_NO_OUTPUT_CO)

        return methodsMsgs


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



class DeepFinderDisplay(Protocol):
    """ This protocol allows you to explore tomograms or segmentation maps with ortho-slices. The seegmentation map
    can be superimposed to the tomogram. Useful for visualising your results."""
    _label = 'display volume'

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('tomogram', PointerParam,
                      pointerClass='Tomogram',
                      label="Tomogram", important=True, allowsNull=True,
                      help='Select tomogram to display.')

        form.addParam('segmentation', PointerParam,
                      pointerClass='DeepFinderSegmentation',
                      label="Segmentation map", important=True, allowsNull=True,
                      help='Select segmentation map to display.')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep('displayStep')

    def displayStep(self):
        deepfinder_args = ''
        if self.tomogram.get() != None:
            fname = self.tomogram.get().getFileName()
            deepfinder_args += '-t ' + fname
        if self.segmentation.get() != None:
            fname = self.segmentation.get().getFileName()
            deepfinder_args += ' -l ' + fname

        # Launch display GUI:
        Plugin.runDeepFinder(self, 'display', deepfinder_args)


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