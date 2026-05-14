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
from deepfinder import DF_LABEL
from pyworkflow.object import Integer
from tomo.constants import BOTTOM_LEFT_CORNER
from tomo.objects import SetOfTomograms, Coordinate3D
from tomo.protocols import ProtTomoBase
import deepfinder.convert as cv


class ProtDeepFinderBase(ProtTomoBase):
    """
    Provides shared utilities for integrating DeepFinder object annotations
    with tomographic workflows in Scipion. The protocol acts as a bridge
    between coordinate-based particle annotations and the object-list
    representation required by DeepFinder-based training, segmentation,
    and detection procedures.

    AI Generated:

    DeepFinder Base Utilities (ProtDeepFinderBase) - User Manual
        Overview

        The DeepFinder Base Utilities protocol provides a common framework
        for transforming annotated particle coordinates into object-list
        representations suitable for DeepFinder processing. Its primary
        purpose is to ensure that tomographic annotations generated or
        curated within Scipion can be consistently interpreted by
        DeepFinder workflows for training, validation, segmentation, and
        object detection.

        In cryo-electron tomography projects, particle annotations often
        originate from manual picking, template matching, neural-network
        predictions, or previous segmentation analyses. These annotations
        must be converted into a structured representation that preserves
        spatial coordinates, tomogram identity, and class membership. This
        protocol standardizes that conversion process so that downstream
        DeepFinder protocols can operate reliably across heterogeneous
        datasets.

        Coordinate and Class Management

        A central role of the protocol is the interpretation of annotated
        3D coordinates together with their associated biological or
        structural classes. Each coordinate is treated as an object located
        within a tomogram and assigned to a specific category representing
        a particle type, macromolecular complex, membrane feature, or other
        structural target.

        Correct class assignment is biologically important because neural
        network training and segmentation quality strongly depend on the
        consistency of labels across the dataset. The protocol ensures that
        annotations remain compatible with DeepFinder conventions, including
        the handling of background classes and label indexing. This helps
        avoid ambiguities that could otherwise reduce classification
        accuracy or compromise training stability.

        Tomogram Association and Dataset Consistency

        The protocol maintains the relationship between coordinates and
        their originating tomograms. This association is essential in
        tomography workflows because each volume may correspond to a
        different biological condition, acquisition session, or experimental
        preparation.

        Preserving tomogram identity becomes especially important during
        neural network training, where the ordering and grouping of
        tomograms can influence validation strategies and reproducibility.
        By organizing annotations according to their corresponding tomograms,
        the protocol supports coherent dataset preparation for both
        supervised learning and downstream quantitative analyses.

        Training and Validation Workflows

        The protocol is designed to facilitate machine learning workflows
        that require separation between training and validation datasets.
        Validation tomograms are commonly used to monitor generalization
        performance and detect overfitting during neural network training.

        In practical cryo-ET studies, maintaining a strict distinction
        between training and validation data is essential for obtaining
        biologically meaningful performance estimates. The protocol supports
        this organization by preparing object annotations in a way that
        preserves the intended dataset partitioning throughout the workflow.

        Biological Interpretation

        From a biological perspective, the quality of coordinate annotation
        directly affects the interpretability of segmentation and detection
        results. Poorly curated labels, inconsistent class definitions, or
        inaccurate spatial annotations can propagate errors into the neural
        network and ultimately reduce the reliability of downstream
        structural interpretation.

        For this reason, users should ensure that coordinate annotations are
        biologically consistent, spatially accurate, and representative of
        the structural diversity present in the dataset. Balanced annotation
        across classes is also recommended whenever possible, particularly
        in supervised learning applications involving rare particle types or
        heterogeneous cellular environments.

        Practical Recommendations

        In routine workflows, it is advisable to verify that all tomograms
        share compatible voxel sizes and coordinate conventions before
        generating DeepFinder object lists. Consistency in annotation style
        and class labeling significantly improves reproducibility and model
        robustness.

        When preparing datasets for training, users should carefully inspect
        the distribution of annotations across tomograms and classes. Large
        imbalances or mislabeled structures may bias the neural network and
        reduce segmentation quality in biologically relevant regions.

        Validation tomograms should ideally represent biological conditions
        similar to those expected during inference while remaining distinct
        from the training subset. This improves the reliability of
        performance assessment and helps identify potential overfitting.

        Final Perspective

        Within DeepFinder-based cryo-electron tomography pipelines, the
        conversion of coordinate annotations into structured object lists is
        a foundational preparation step. Although conceptually simple, this
        stage strongly influences the reliability of neural network
        training, segmentation accuracy, and downstream biological
        interpretation. Careful organization of annotations, coherent class
        definitions, and accurate tomogram association are therefore
        essential for robust and reproducible tomography analysis.
    """

    TOMO = 'tomo'
    OBJL = 'objl'
    PARAMS_XML = 'paramsXml'

    @staticmethod
    def _getObjlFromInputCoordinates(coord3DSet):
        """Get all objects of specified class.
        Args:
            tomoSet (SetOfTomograms)
            coord3DSet (SetOfCoordinates3D)
        Returns:
            list of dict: deep finder object list (contains particle infos)
        """
        # Coordinate _groupId attribute is used to store the DeepFinder class label, that has to be greater than zero.
        # To avoid the zero value of _groupId of non-DeepFinder annotated coordinates, they must be corrected if
        # necessary
        groupIds = coord3DSet.getUniqueValues(Coordinate3D.GROUP_ID_ATTR)
        dfLabelCorrection = 1 if min(groupIds) == 0 else 0

        objlListDict = []
        tomoList = [tomo.clone() for tomo in coord3DSet.getPrecedents()]
        for tomoInd, tomo in enumerate(tomoList):
            objl = []
            for coord in coord3DSet.iterCoordinates(volume=tomo):
                x = coord.getX(BOTTOM_LEFT_CORNER)
                y = coord.getY(BOTTOM_LEFT_CORNER)
                z = coord.getZ(BOTTOM_LEFT_CORNER)
                lbl = coord.getGroupId() + dfLabelCorrection
                cv.objl_add(objl, label=lbl, coord=[z, y, x], tomo_idx=tomoInd)
            objlListDict.append({ProtDeepFinderBase.TOMO: tomo.clone(),
                                 ProtDeepFinderBase.OBJL: objl,
                                 ProtDeepFinderBase.PARAMS_XML: f'params_target_generation_{tomoInd + 1}.xml'
                                 })

        return objlListDict

    @staticmethod
    def _getObjlFromInputCoordinatesV2(tomoMasksList, coord3DSet, nValTomoMasks):
        """Get all Coord objects related to the given Tomogram objects.
        The output is an objl as needed by DeepFinder.
        The tomo_idx in the objl respects the order in tomoSet, which is important for the Train protocol
        Args:
            tomoMasksList (list) list of TomoMasks ordered [validation masks, training masks]
            coord3DSet (SetOfCoordinates3D)
            nValTomoMasks (int): number of validation tomo masks
        Returns:
            list of dict: deep finder object list (contains particle infos)
        """
        objl_train = []
        objl_valid = []
        for tidx, tomoMask in enumerate(tomoMasksList):
            tomoId = tomoMask.getObjId()
            listToAdd = objl_valid if tidx <= nValTomoMasks - 1 else objl_train
            for coord in coord3DSet.iterCoordinates(volume=tomoId):
                x = coord.getX(BOTTOM_LEFT_CORNER)
                y = coord.getY(BOTTOM_LEFT_CORNER)
                z = coord.getZ(BOTTOM_LEFT_CORNER)
                lbl = coord.getGroupId()
                cv.objl_add(listToAdd, label=lbl, coord=[z, y, x], tomo_idx=tidx)
        return objl_train, objl_valid



