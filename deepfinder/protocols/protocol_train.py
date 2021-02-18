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

from pwem.protocols import EMProtocol
from pyworkflow.protocol import params, PointerParam
from pyworkflow.utils.properties import Message

from deepfinder import Plugin
import deepfinder.convert as cv
from deepfinder.objects import DeepFinderNet

from deepfinder.protocols import ProtDeepFinderBase

"""
Describe your python module here:
This module will provide the traditional Hello world example
"""


class DeepFinderTrain(EMProtocol, ProtDeepFinderBase):
    """ This protocol launches the training procedure """
    _label = 'train'

    def __init__(self, **args):
        EMProtocol.__init__(self, **args)
        self.nClass = None

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('targets', PointerParam,
                      pointerClass='SetOfTomoMasks',
                      label="Segmented targets",
                      important=True,
                      help='Training dataset. Please select here your targets. '
                           'The corresponding tomogram will be loaded automatically.')

        form.addParam('coordTrain', params.PointerParam,
                      label="Training coordinates",
                      pointerClass='SetOfCoordinates3D',
                      help='Select coordinate set for training.')

        form.addParam('coordValid', params.PointerParam,
                      label="Validation coordinates",
                      pointerClass='SetOfCoordinates3D',
                      help='Select coordinate set for validation.')

        form.addSection(label='Training Parameters')
        form.addParam('psize', params.EnumParam,
                      default=1,  # 40: 1st element in [40, 44, 48, 52, 56, 60, 64]
                      choices=list(range(40, 65, 4)),
                      label='Patch size',
                      important=True,
                      help='Size of patches loaded into memory for training.')

        form.addParam('bsize', params.IntParam,
                      default=25,
                      label='Batch size',
                      important=True,
                      help='Number of patches used to compute average loss.')

        form.addParam('epochs', params.IntParam,
                      default=100,
                      label='Number of epochs',
                      important=True,
                      help='At the end of each epoch, evaluation on validation set is performed (useful to check if network overfits).')

        form.addParam('stepsPerE', params.IntParam,
                      default=100,
                      label='Steps per epoch',
                      important=True,
                      help='Number of batches trained on per epoch.')

        form.addParam('stepsPerV', params.IntParam,
                      default=10,
                      label='Steps per validation',
                      important=True,
                      help='Number of batches used for validation.')

        form.addParam('bootstrap', params.BooleanParam,
                      default=True,
                      label='Bootstrap',
                      important=True,
                      help='Can remain checked. Usefull when in presence of unbalanced classes.')

        form.addParam('rndShift', params.IntParam,
                      default=13,
                      label='Random shift',
                      important=True,
                      help='(in voxels) Applied to positions in object list when sampling patches. Enhances network robustness. Make sure that objects are still contained in patches when applying shift.')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep('trainingStep')
        self._insertFunctionStep('createOutputStep')

    def trainingStep(self):
        # Get paths to tomograms and corresponding targets:
        path_tomo = []
        path_segm = []
        for segm in self.targets.get().iterItems():
            fname_segm = segm.getFileName()
            fname_tomo = segm.getReferenceTomogram()
            path_tomo.append(fname_tomo)
            path_segm.append(fname_segm)

        # Get objl_train and objl_valid and save to temp folder:
        objl_train = self._getObjlFromInputCoordinates(self.targets.get(), self.coordTrain.get())
        objl_valid = self._getObjlFromInputCoordinates(self.targets.get(), self.coordValid.get())

        fname_objl_train = abspath(self._getExtraPath('objl_train.xml'))
        cv.objl_write(objl_train, fname_objl_train)
        fname_objl_valid = abspath(self._getExtraPath('objl_valid.xml'))
        cv.objl_write(objl_valid, fname_objl_valid)

        # Get number of classes from objl, and store as attribute (useful for output step):
        self.nClass = len(cv.objl_get_labels(objl_train)) + 1  # (+1 for background class)

        # Save parameters to xml file:
        params = cv.ParamsTrain()

        params.path_out = abspath(self._getExtraPath())+'/'
        params.path_tomo = path_tomo
        params.path_target = path_segm
        params.path_objl_train = fname_objl_train
        params.path_objl_valid = fname_objl_valid
        params.Ncl = self.nClass
        params.psize = self.psize.get()
        params.bsize = self.bsize.get()
        params.nepochs = self.epochs.get()
        params.steps_per_e = self.stepsPerE.get()
        params.steps_per_v = self.stepsPerV.get()
        params.flag_direct_read = False  # in current deepfinder version only works with tomos/targets stored as h5
        params.flag_bootstrap = self.bootstrap.get()
        params.rnd_shift = self.rndShift.get()

        fname_params = abspath(self._getExtraPath('params_train.xml'))
        params.write(fname_params)

        # Launch DeepFinder training:
        deepfinder_args = '-p ' + fname_params
        Plugin.runDeepFinder(self, 'train', deepfinder_args)

    def createOutputStep(self):
        netWeights = DeepFinderNet()
        fname = abspath(self._getExtraPath('net_weights_FINAL.h5'))
        netWeights.setPath(fname)
        netWeights.setNbOfClasses(self.nClass)
        self._defineOutputs(netWeights=netWeights)

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