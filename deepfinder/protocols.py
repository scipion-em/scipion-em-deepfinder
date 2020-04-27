# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
# *
# * your institution
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
from pyworkflow.object import Integer
from pyworkflow.protocol import Protocol, params, IntParam, EnumParam, PointerParam
from pyworkflow.utils.properties import Message
from tomo.protocols import ProtTomoPicking
from deepfinder import Plugin

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
    """TODO This go the the help"""

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

        # TODO Prepare input for annotation GUI
        for tomo in self.inputTomograms.get().iterItems():

            # Launch annotation GUI passing the tomogram file name
            Plugin.runDeepFinder(self, 'annotation', '-t '+tomo.getFileName())




    def createOutputStep(self):
        # TODO Convert DeepFinder annotation output to Scipion SetOfCoordinates3D

        # Probably we need 1 SetOfCoordinated3D per "deepfinder class"

        # setTomograms = self.inputTomograms.get()
        #
        # # New set of coordinates 3D
        # coord3DSet = self._createSetOfCoordinates3D(setTomograms)
        # coord3DSet.setName("tomoCoord")
        # coord3DSet.setPrecedents(setTomograms)
        # coord3DSet.setSamplingRate(setTomograms.getSamplingRate())
        # coord3DSet.setBoxSize(self.boxSize.get())
        #
        #  # Or maybe it is better to iterate over the deppfinder xml output file (annotiation GUI generates)
        # for tomo in setTomograms.iterItems():
        #
        #     # Populate Set of 3D Coordinates with 3D Coordinates
        #     # Converting due to convention differences
        #     points = np.loadtxt(outPoints, delimiter=' ')
        #     angles = np.deg2rad(np.loadtxt(outAngles, delimiter=' '))
        #     x, y, z, angles =  getXmlAnnotations()
        #
        #     coord = Coordinate3D()
        #     coord.setPosition(x,y,z)
        #     coord.euler2Matrix(angles[0], angles[1], angles[2])
        #     coord.setVolume(tomo)
        #     coord3DSet.append(coord)
        #
        #
        # self._defineOutputs(outputCoordinates3D=coord3DSet)
        # self._defineSourceRelation(setTomograms, coord3DSet)

        pass

    # --------------------------- DEFINE info functions ----------------------
    def getMethods(self, output):
        msg = 'User picked %d particles ' % output.getSize()
        msg += 'with a particle size of %s.' % output.getBoxSize()
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