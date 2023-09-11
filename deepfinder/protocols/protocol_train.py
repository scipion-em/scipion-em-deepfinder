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

import numpy as np

from pwem.protocols import EMProtocol
from pyworkflow import BETA
from pyworkflow.object import Integer
from pyworkflow.protocol import params, PointerParam, GPU_LIST, LEVEL_ADVANCED, FloatParam, GT, LT
from pyworkflow.utils.properties import Message

from deepfinder import Plugin, DF_CLASS_LABEL
import deepfinder.convert as cv
from deepfinder.objects import DeepFinderNet

from deepfinder.protocols import ProtDeepFinderBase
from tomo.constants import BOTTOM_LEFT_CORNER
from tomo.protocols import ProtTomoBase
from tomo.objects import SetOfTomoMasks

PSIZE_CHOICES = ['40', '44', '48', '52', '56', '60', '64']


class DFTrainOutputs(Enum):
    netWeights = DeepFinderNet


class DeepFinderTrain(EMProtocol, ProtDeepFinderBase, ProtTomoBase):
    """ This protocol launches the training procedure """

    _label = 'train'
    _devStatus = BETA
    _possibleOutputs = DFTrainOutputs

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

        form.addParam('tomoMasksTrain', PointerParam,
                      pointerClass='SetOfTomoMasks',
                      label="Training TomoMasks",
                      important=True,
                      help='Training dataset. Please select here your TomoMasks. '
                           'The corresponding tomograms will be loaded automatically.')

        form.addParam('tomoMasksValid', PointerParam,
                      pointerClass='SetOfTomoMasks',
                      label="Validation TomoMasks",
                      allowsNull=True,
                      help='Validation dataset. If empty, the tomo mask will be randomly split following the '
                           'fraction specified in the parameter "Validation data fraction".')

        form.addParam('valDataFraction', FloatParam,
                      label='Validation data fraction',
                      default=0.3,
                      validators=[GT(0.1), LT(0.5)],
                      condition='not tomoMasksValid',
                      help='Fraction of the "Training Tomomasks" that will be used as validation dataset. The admitted '
                           'values are [0.1, 0.5], which means from 10% to 50% of the introduced training tomo masks. '
                           'Only applies if "Validation TomoMasks" is empty.')

        form.addParam('coord', params.PointerParam,
                      label="Coordinates",
                      pointerClass='SetOfCoordinates3D',
                      help='Select coordinate set.')

        form.addSection(label='Training Parameters')
        form.addParam('psize', params.EnumParam,
                      display=params.EnumParam.DISPLAY_COMBO,
                      default=0,  # 40: 1st element in [40, 44, 48, 52, 56, 60, 64]
                      choices=PSIZE_CHOICES,
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
                      help='At the end of each epoch, evaluation on validation set is performed (useful to check if '
                           'network overfits).')

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
                      help='Can remain checked. Useful when in presence of unbalanced classes.')

        form.addParam('rndShift', params.IntParam,
                      default=13,
                      label='Random shift',
                      important=True,
                      help='(in voxels) Applied to positions in object list when sampling patches. Enhances network '
                           'robustness. Make sure that objects are still contained in patches when applying shift.')

        form.addHidden(GPU_LIST, params.StringParam, default='0',
                       expertLevel=LEVEL_ADVANCED,
                       label="Choose GPU IDs",
                       help="GPU ID, normally it is 0.")

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep(self.trainingStep)
        self._insertFunctionStep(self.createOutputStep)

    def trainingStep(self):
        tomoMasksTrain = self.tomoMasksTrain.get()
        coords = self.coord.get()
        # Get tomo paths, target paths, train objl and valid objl for DeepFinder
        if self.tomoMasksValid.get():
            path_tomos, path_targets, objl_train, objl_valid = self._getDeepFinderObjectsFromInput(
                tomoMasksTrain, self.tomoMasksValid.get(), coords)
        else:
            nTomoMasks = len(tomoMasksTrain)
            nValData = round(self.valDataFraction.get() * nTomoMasks)
            randPermIdxs = np.random.permutation(range(nTomoMasks))
            tomoMasksList = [tomoMask.clone() for tomoMask in tomoMasksTrain]
            tomoMasksListSorted = [tomoMasksList[i] for i in randPermIdxs]  # List of tomo masks [validation, training] after randomization
            path_tomos, path_targets = self._getPathListsFromTomoMaskSet(tomoMasksListSorted)
            objl_train, objl_valid = self._getObjlFromInputCoordinatesV2(tomoMasksListSorted, coords, nValData)

        # Save objl to extra folder:
        fname_objl_train = abspath(self._getExtraPath('objl_train.xml'))
        cv.objl_write(objl_train, fname_objl_train)
        fname_objl_valid = abspath(self._getExtraPath('objl_valid.xml'))
        cv.objl_write(objl_valid, fname_objl_valid)

        # Get number of classes from objl, and store as attribute (useful for output step):
        self.nClass = len(cv.objl_get_labels(objl_train)) + 1  # (+1 for background class)

        # Save parameters to xml file:
        params = cv.ParamsTrain()

        params.path_out = abspath(self._getExtraPath()) + '/'
        params.path_tomo = path_tomos
        params.path_target = path_targets
        params.path_objl_train = fname_objl_train
        params.path_objl_valid = fname_objl_valid
        params.Ncl = self.nClass
        params.psize = self._decodeContValue(getattr(self, 'psize').get())
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
        Plugin.runDeepFinder(self, 'train', deepfinder_args, gpuId=getattr(self, GPU_LIST).get())

    def createOutputStep(self):
        netWeights = DeepFinderNet()
        fname = abspath(self._getExtraPath('net_weights_FINAL.h5'))
        netWeights.setPath(fname)
        netWeights.setNbOfClasses(self.nClass)
        self._defineOutputs(**{self._possibleOutputs.netWeights.name: netWeights})

    # --------------------------- UTILITY functions -------------------------------- #
    @staticmethod
    def _decodeContValue(idx):
        """Decode the psize value and represent it as expected by DeepFinder"""
        return int(PSIZE_CHOICES[idx])

    def _getDeepFinderObjectsFromInput(self, tomoMaskSetTrain, tomoMaskSetValid, coord3DSet):
        """Get all objects of specified class.
        Args:
            tomoMaskSetTrain (SetOfTomoMasks)
            tomoMaskSetValid (SetOfTomoMasks)
            coord3DSet (SetOfCoordinates3D)
        Returns:
            list of strings : path_tomos[]
            list of strings : path_targets[]
            list of dict : objl_train
            list of dict : objl_valid
        """
        # Join the tomoMaskSets. 1st valid, then train. Order is important!
        tomoMaskList = self._setsOfTomoMasks2List(tomoMaskSetValid, tomoMaskSetTrain)

        # Get the file paths for tomos and targets (=tomoMasks)
        path_tomos, path_targets = self._getPathListsFromTomoMaskSet(tomoMaskList)

        # Get deepfinder objl from coord3DSet:
        objl_train, objl_valid = self._getObjlFromInputCoordinatesV2(tomoMaskList, coord3DSet, len(tomoMaskSetValid))

        return path_tomos, path_targets, objl_train, objl_valid

    @staticmethod
    def _setsOfTomoMasks2List(valTomoMasksSet, trainTomoMasksSet):
        """ Joins two tomoMaskSets.
        Args:
            valTomoMasksSet (SetOfTomoMasks)
            trainTomoMasksSet (SetOfTomoMasks)
        Returns:
            List of TomoMask in ordered [validation masks, training masks]
        """
        tomoMaskList = [tomoMask.clone() for tomoMask in valTomoMasksSet]
        tomoMaskList.extend([tomoMask.clone() for tomoMask in trainTomoMasksSet])
        return tomoMaskList

    @staticmethod
    def _getPathListsFromTomoMaskSet(tomoMaskList):
        """ Gets the path lists needed by DeepFinder from protocol input.
        Args:
            tomoMaskList (List): list of tomo masks
        Returns:
            list of strings : path_tomos[]
            list of strings : path_targets[]
        """
        path_tomos = []
        path_targets = []
        for tomoMask in tomoMaskList:
            path_tomos.append(abspath(tomoMask.getVolName()))
            path_targets.append(abspath(tomoMask.getFileName()))

        return path_tomos, path_targets

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []

        if self.isFinished():
            summary.append("Training finished.")
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
        trainTomoMasks = self.tomoMasksTrain.get()
        valTomoMasks = self.tomoMasksValid.get()
        if valTomoMasks and trainTomoMasks:
            if len(valTomoMasks) > len(trainTomoMasks):
                errorMsg.append('The validation masks set must be of the same or lower size than the training '
                                'masks set.')
        elif not valTomoMasks and len(trainTomoMasks) == 1:
            errorMsg.append('If no validation tomo masks are provided, the size of the training masks set must '
                            'be at least 2.')
        return errorMsg
