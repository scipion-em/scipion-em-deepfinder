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
import glob
from os.path import abspath

from pyworkflow.object import Boolean, String
from pyworkflow.utils import removeBaseExt
from tomo.protocols import ProtTomoPicking
from tomo.objects import Coordinate3D

from deepfinder import Plugin
import deepfinder.convert as cv

"""
Describe your python module here:
This module will provide the traditional Hello world example
"""


class DeepFinderAnnotations(ProtTomoPicking):
    """This protocol allows you to annotate macromolecules in your tomograms, using a visual tool."""

    _label = 'annotate'

    def __init__(self, **args):
        ProtTomoPicking.__init__(self, **args)
        self._noAnnotations = Boolean(True)
        self.annotationSummary = String()

    # --------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        ProtTomoPicking._defineParams(self, form)

    # --------------------------- INSERT steps functions ----------------------
    def _insertAllSteps(self):
        # Launch Boxing GUI
        for tomo in self.inputTomograms.get().iterItems():
            self._insertFunctionStep('launchAnnotationStep', tomo)
        self._insertFunctionStep('createOutputStep')

    # --------------------------- STEPS functions -----------------------------
    def launchAnnotationStep(self, tomo):
        # This generates 1 objl.xml file per tomogram and stores it in EXTRA:
        # Generate objl filename (output):
        fname_objl = 'objl_annot_' + removeBaseExt(tomo.getFileName()) + '.xml'

        # Launch annotation GUI passing the tomogram file name
        deepfinder_args = ' -t %s ' % abspath(tomo.getFileName())
        deepfinder_args += '-o %s' % abspath(self._getExtraPath(fname_objl))
        Plugin.runDeepFinder(self, 'annotateJJ', deepfinder_args)

    def createOutputStep(self):
        if glob.glob(self._getExtraPath('*.xml')):
            self._noAnnotations.set(False)

            # Convert DeepFinder annotation output to Scipion SetOfCoordinates3D
            setTomograms = self.inputTomograms.get()

            # First, determine the classes that have been annotated (check in all object lists):
            objl = []
            objlReadResults = []
            for tomo in setTomograms.iterItems():
                # Get objl filename:
                fname_objl = 'objl_annot_' + removeBaseExt(tomo.getFileName()) + '.xml'

                # Read objl:
                objl_tomo = cv.objl_read(abspath(self._getExtraPath(fname_objl)))
                objlReadResults.append(objl_tomo)
                objl.extend(objl_tomo)

            # For each class, iterate over all object lists (1 per tomo) and store coordinates
            # in SetOfCoordinates3D (1 per class)
            # Remark: only 1 setOfCoordinates3D can exist at a time, else:
            # "Protocol failed: Cannot operate on a closed database."
            coord3DSet = self._createSetOfCoordinates3D(setTomograms)
            coord3DSet.setSamplingRate(setTomograms.getSamplingRate())
            coordCounter = 0
            lbl_list = cv.objl_get_labels(objl)
            nClasses = len(lbl_list)
            annotationSummary = '%i classes have been annotated.' % nClasses

            for lbl in lbl_list:
                objl_class = cv.objl_get_class(objl, lbl)
                lblStr = str(lbl)
                msg = '\nClass %s: %i object(s)' % (lblStr, len(objl_class))
                annotationSummary += msg
                print(msg)

                for tomoInd, tomo in enumerate(setTomograms.iterItems()):
                    objl_class = cv.objl_get_class(objlReadResults[tomoInd - 1], lbl)
                    for idx in range(len(objl_class)):
                        x = objl_class[idx]['x']
                        y = objl_class[idx]['y']
                        z = objl_class[idx]['z']

                        coord = Coordinate3D()
                        coord.setObjId(coordCounter + 1)
                        coord.setPosition(x, y, z)
                        coord.setVolume(tomo)
                        coord.setVolId(tomoInd + 1)
                        coord._dfLabel = String(lblStr)

                        coord3DSet.append(coord)
                        coordCounter += 1

                self._defineOutputs(outputCoordinates=coord3DSet)
                self._defineSourceRelation(setTomograms, coord3DSet)

            self.annotationSummary.set(annotationSummary)
            self._store(self.annotationSummary, self._noAnnotations)

    # --------------------------- DEFINE info functions ----------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []
        if self.isFinished():
            if self.annotationSummary.get():
                summary.append(self.annotationSummary.get())

            if self._noAnnotations.get():
                summary.append('NO ANNOTATIONS WERE TAKEN.')

        return summary
