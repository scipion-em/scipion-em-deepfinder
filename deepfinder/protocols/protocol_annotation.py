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

import os

"""
Describe your python module here:
This module will provide the traditional Hello world example
"""

class DeepFinderAnnotations(ProtTomoPicking):
    """This protocol allows you to annotate macromolecules in your tomograms, using a visual tool."""

    _label = 'annotate'

    def __init__(self, **args):
        ProtTomoPicking.__init__(self, **args)
        self.objl = []

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

        # This generates 1 objl.xml file per tomogram and stores it in EXTRA:
        for tomo in self.inputTomograms.get().iterItems():
            # Generate objl filename (output):
            fname_tomo = os.path.splitext( tomo.getFileName() )
            fname_tomo = os.path.basename(fname_tomo[0])
            fname_objl = 'objl_annot_'+fname_tomo+'.xml'

            # Launch annotation GUI passing the tomogram file name
            deepfinder_args = '-t ' + tomo.getFileName()
            deepfinder_args += ' -o ' + os.path.abspath(os.path.join(self._getExtraPath(), fname_objl))
            Plugin.runDeepFinder(self, 'annotate', deepfinder_args)




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
        self.objl = objl  # store as class attribute for _summary

        # Test summary string:
        lbl_list = cv.objl_get_labels(self.objl)
        print(str(len(lbl_list)) + ' classes have been annotated.')
        for lbl in lbl_list:
            objl_class = cv.objl_get_class(self.objl, lbl)
            print('Class ' + str(lbl) + ': ' + str(len(objl_class)) + ' objects')

        # For each class, iterate over all object lists (1 per tomo) and store coordinates
        # in SetOfCoordinates3D (1 per class)
        # Remark: only 1 setOfCoordinates3D can exist at a time, else:
        # "Protocol failed: Cannot operate on a closed database."
        for lbl in lbl_list:
            coord3DSet = self._createSetOfCoordinates3D(setTomograms, lbl) # lbl is a suffix for sqlite filename. Important, else overwrite!
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
            coord3DSet.setStreamState(Set.STREAM_OPEN)
            args[name] = coord3DSet

            self._defineOutputs(**args)
            self._defineSourceRelation(setTomograms, coord3DSet)

        # I (emoebel) don't know what this is for, but is apparently necessary (copied from Estrella's XmippProtCCroi)
        for outputset in self._iterOutputsNew():
            outputset[1].setStreamState(Set.STREAM_CLOSED)
        self._store()



    # --------------------------- DEFINE info functions ----------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []
        if self.isFinished():
            lbl_list = cv.objl_get_labels(self.objl)
            summary.append(str(len(lbl_list))+' classes have been annotated.')
            for lbl in lbl_list:
                objl_class = cv.objl_get_class(self.objl, lbl)
                summary.append('Class '+str(lbl)+': '+str(len(objl_class))+' object(s)')

        return summary
