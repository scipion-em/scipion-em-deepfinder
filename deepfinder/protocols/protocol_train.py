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
from enum import Enum
from os.path import abspath
import numpy as np

from deepfinder import Plugin
from pwem.protocols import EMProtocol
from pyworkflow.protocol import params, PointerParam, GPU_LIST, LEVEL_ADVANCED, FloatParam, GT, LT
from pyworkflow.utils import removeBaseExt
from pyworkflow.utils.properties import Message
import deepfinder.convert as cv
from deepfinder.objects import DeepFinderNet
from deepfinder.protocols import ProtDeepFinderBase
from tomo.protocols import ProtTomoBase
from tomo.objects import SetOfTomoMasks

PSIZE_CHOICES = ['40', '44', '48', '52', '56', '60', '64']


class DFTrainOutputs(Enum):
    netWeights = DeepFinderNet


class DeepFinderTrain(EMProtocol, ProtDeepFinderBase, ProtTomoBase):
    """
    Trains DeepFinder neural network models for semantic segmentation and
    particle recognition in cryo-electron tomography datasets. The protocol
    uses annotated tomograms, tomographic masks, and particle coordinates to
    learn structural patterns that can later be used for automated object
    detection and segmentation in volumetric cryo-EM data.

    AI Generated:

    DeepFinder Training (DeepFinderTrain) — User Manual
        Overview

        The DeepFinder Training protocol prepares and trains deep learning
        models for the analysis of cryo-electron tomography data. Its main
        objective is to teach a neural network to recognize biologically
        meaningful structures inside tomograms by learning from annotated
        examples. In practical cryo-ET workflows, this protocol is commonly
        used to develop models capable of identifying macromolecular
        complexes, organelles, membranes, viral components, or other cellular
        features directly within three-dimensional volumes.

        For biological users, this protocol represents a supervised learning
        approach in which manually curated annotations guide the training
        process. The resulting model can later be applied to new tomograms
        for automated segmentation or particle localization, significantly
        reducing manual workload and improving reproducibility across large
        datasets.

        Inputs and General Workflow

        The protocol requires a set of tomographic masks together with the
        associated tomograms and a corresponding set of three-dimensional
        coordinates describing the positions of annotated objects. The masks
        define the target regions that the neural network must learn to
        recognize, while the coordinates provide object identity and spatial
        localization information.

        Training and validation datasets can be generated automatically or
        defined explicitly by the user. In the automatic approach, the
        protocol randomly partitions the available tomo masks into training
        and validation subsets according to a user-defined validation
        fraction. This strategy is generally sufficient for most biological
        applications and simplifies workflow preparation.

        Alternatively, users may provide an independent validation dataset.
        This option is useful when datasets originate from different
        experimental conditions or when strict separation between training
        and validation samples is required to assess model generalization.

        Patch-Based Learning

        DeepFinder training operates on volumetric patches extracted from
        tomograms rather than on complete tomographic volumes. Patch-based
        learning reduces memory requirements and allows the neural network
        to focus on local structural information. The patch size parameter
        therefore plays an important biological and computational role.

        Smaller patches require less GPU memory and may improve sensitivity
        to local details, but they can limit the contextual information
        available to the network. Larger patches provide broader structural
        context and may improve recognition of large assemblies or extended
        cellular features, although they demand more computational resources.

        In biological practice, the patch size should generally be large
        enough to contain the full target structure together with sufficient
        surrounding context to distinguish it from neighboring densities.

        Training Dynamics and Optimization

        The protocol allows control over several key training parameters,
        including batch size, number of epochs, and the number of steps
        performed during training and validation. These parameters determine
        how intensively the neural network learns from the dataset and how
        frequently its performance is evaluated.

        The batch size controls how many volumetric patches contribute to
        each optimization step. Larger batch sizes may stabilize training
        but require more GPU memory. Smaller batches are computationally
        lighter but may produce noisier optimization behavior.

        The number of epochs determines how many times the network revisits
        the dataset during learning. In biological workflows, insufficient
        training may lead to underfitting, where important structures are
        not properly recognized, whereas excessive training may produce
        overfitting, causing the model to memorize the training data rather
        than generalize to unseen tomograms.

        Validation and Model Generalization

        Validation plays a critical role in assessing whether the network
        is learning biologically meaningful patterns rather than memorizing
        the training examples. During validation, the model is evaluated
        using data not directly used for optimization. Monitoring validation
        behavior helps identify overfitting and provides a more realistic
        estimate of model performance on future datasets.

        In cryo-electron tomography, variability between tomograms can be
        substantial because of differences in imaging conditions, specimen
        thickness, contrast, or sample preparation. For this reason,
        maintaining a representative validation dataset is especially
        important for ensuring robust biological interpretation.

        Bootstrap Sampling and Robustness

        The protocol supports bootstrap-based sampling strategies that help
        compensate for unbalanced class distributions. In many biological
        datasets, some structures may appear much more frequently than
        others. Without corrective strategies, the neural network may become
        biased toward dominant classes while poorly learning rare but
        biologically important targets.

        Bootstrap sampling increases the effective representation of less
        frequent classes and improves the robustness of the resulting model.
        This is particularly valuable in cellular tomography studies where
        certain macromolecular assemblies may be sparsely distributed.

        Random Shift Augmentation

        To improve generalization, the protocol introduces random spatial
        shifts during patch extraction. This augmentation strategy exposes
        the network to slightly different object positions and prevents
        excessive dependence on exact coordinate centering.

        From a biological perspective, this improves robustness against
        experimental variability and helps the model recognize structures
        under realistic positional fluctuations. However, the selected shift
        should remain small enough to ensure that target structures stay
        fully contained within the extracted patches.

        Outputs and Model Interpretation

        After training, the protocol produces one or more neural network
        weight files corresponding to different training stages or epochs.
        These trained models can subsequently be used for automated
        segmentation, particle localization, or inference workflows on
        previously unseen tomograms.

        The quality of the resulting models depends strongly on the quality
        and consistency of the training annotations. High-quality biological
        annotations are often more important than simply increasing dataset
        size. Inconsistent labeling may confuse the neural network and
        reduce prediction reliability.

        Practical Recommendations

        For most biological applications, it is advisable to begin with a
        moderate validation fraction and default training parameters. Visual
        inspection of prediction quality on independent tomograms is often
        the best indicator of whether the model has learned meaningful
        structural features.

        Users should ensure that training datasets capture the expected
        diversity of biological states, orientations, and imaging conditions.
        Networks trained on overly homogeneous data may fail when applied to
        more variable experimental datasets.

        When GPU memory is limited, reducing patch size or batch size is
        usually preferable to reducing dataset diversity. Conversely, when
        sufficient computational resources are available, larger patches and
        longer training schedules may improve segmentation quality for
        structurally complex tomograms.

        Final Perspective

        Deep learning approaches such as DeepFinder are transforming
        cryo-electron tomography by enabling scalable and automated analysis
        of complex volumetric datasets. Successful application of these
        methods depends not only on computational settings but also on the
        biological quality of annotations, careful dataset preparation, and
        thoughtful validation strategies. Well-trained models can greatly
        accelerate structural interpretation and support large-scale studies
        of molecular organization inside cells.
    """

    _label = 'train'
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

        form.addParam('useSpecificValidation', params.BooleanParam,
                      expertLevel=LEVEL_ADVANCED,
                      default='False',
                      label="Use specific set for Validation?",
                      help='Recommended value as false. The default value (False) will atuomatically split '
                      'the set of tomo masks according to the "Validation data fraction". If this parameter '
                      ' is true, the user can provide a certain set of tomoMask for validating the training.')

        form.addParam('tomoMasksValid', PointerParam,
                      expertLevel=LEVEL_ADVANCED,
                      condition='useSpecificValidation',
                      pointerClass='SetOfTomoMasks',
                      label="Validation TomoMasks",
                      allowsNull=True,
                      help='(Only available when "Use specific set for Validation" is True.) This is the validation'
                      ' set of tomo Masks to ensure that the network learns properly.')

        form.addParam('valDataFraction', FloatParam,
                      label='Validation data fraction',
                      condition='not useSpecificValidation ',
                      default=0.3,
                      validators=[GT(0.1), LT(0.5)],
                      help='Fraction of the "Training Tomomasks" that will be used as validation dataset. The admitted '
                           'values are [0.1, 0.5], which means from 10% to 50% of the introduced training tomo masks. '
                           'Only applies if "Validation TomoMasks" is empty.')

        form.addParam('coord', params.PointerParam,
                      label="Coordinates",
                      pointerClass='SetOfCoordinates3D',
                      important=True,
                      help='Select coordinate set.')

        form.addSection(label='Training Parameters')
        form.addParam('psize', params.EnumParam,
                      display=params.EnumParam.DISPLAY_COMBO,
                      default=0,  # 40: 1st element in [40, 44, 48, 52, 56, 60, 64]
                      choices=PSIZE_CHOICES,
                      label='Patch size',
                      help='Size of patches loaded into memory for training.')

        form.addParam('bsize', params.IntParam,
                      default=25,
                      label='Batch size',
                      help='Number of patches used to compute average loss.')

        form.addParam('epochs', params.IntParam,
                      default=100,
                      label='Number of epochs',
                      help='At the end of each epoch, evaluation on validation set is performed (useful to check if '
                           'network overfits).')

        form.addParam('stepsPerE', params.IntParam,
                      default=100,
                      label='Steps per epoch',
                      help='Number of batches trained on per epoch.')

        form.addParam('stepsPerV', params.IntParam,
                      default=10,
                      label='Steps per validation',
                      help='Number of batches used for validation.')

        form.addParam('bootstrap', params.BooleanParam,
                      default=True,
                      label='Bootstrap',
                      help='Can remain checked. Useful when in presence of unbalanced classes.')

        form.addParam('rndShift', params.IntParam,
                      default=13,
                      label='Random shift',
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
        Plugin.runDeepFinder(self, 'train', deepfinder_args, useGPU=True)

    def createOutputStep(self):
        trainingModels = sorted(glob.glob(self._getExtraPath('net_weights_*.h5')), reverse=True)
        for trainingModel in trainingModels:
            netWeights = DeepFinderNet(path=abspath(trainingModel),
                                       noClasses=self.nClass)
            modelEpoch = removeBaseExt(trainingModel).replace('net_weights_', '')
            self._defineOutputs(**{self._possibleOutputs.netWeights.name + f'_{modelEpoch}': netWeights})
            self._defineSourceRelation(self.tomoMasksTrain, netWeights)

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
        valFraction = self.valDataFraction.get()
        if valTomoMasks and trainTomoMasks:
            if len(valTomoMasks) > len(trainTomoMasks):
                errorMsg.append('The validation masks set must be of the same or lower size than the training '
                                'masks set.')
        elif not valTomoMasks and len(trainTomoMasks) == 1:
            errorMsg.append('If no validation tomo masks are provided, the size of the training masks set must '
                            'be at least 2.')
        if self.useSpecificValidation.get() and not valTomoMasks:
            errorMsg.append('Please provide a validation set.')

        return errorMsg

