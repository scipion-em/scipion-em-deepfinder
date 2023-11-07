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
from os.path import exists
from pyworkflow.tests import BaseTest, setupTestProject
import tomo.protocols
import pwem.protocols
from tomo.protocols.protocol_import_tomograms import OUTPUT_NAME
from . import DataSet
from ..protocols import ImportCoordinates3D, DeepFinderGenerateTrainingTargetsSpheres, DeepFinderTrain, \
    ProtDeepFinderLoadTrainingModel, DeepFinderSegment, DeepFinderCluster


class TestDeepFinderImportCoordinates(BaseTest):
    """This class check if the protocol to import DeepFinder object lists works properly."""

    # modelled after tomo.test.TestTomoImportSetOfCoordinates3D

    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.dataset = DataSet.getDataSet('deepfinder')

    def _runDeepFinderImportCoordinates(self):
        # Get tomos:
        protImportTomogram = self.newProtocol(tomo.protocols.ProtImportTomograms,
                                              filesPath=self.dataset.getPath(),
                                              filesPattern='tomo*.mrc',
                                              samplingRate=10)

        self.launchProtocol(protImportTomogram)

        output = getattr(protImportTomogram, 'Tomograms', None)
        self.assertIsNotNone(output, "There was a problem with tomogram output")

        # Define and launch test protocol:
        protImportCoordinates3d = self.newProtocol(ImportCoordinates3D,
                                                   filesPath=self.dataset.getPath(),
                                                   importTomograms=protImportTomogram.Tomograms,
                                                   filesPattern='*.xml')
        self.launchProtocol(protImportCoordinates3d)

        return protImportCoordinates3d

    def test_import_set_of_coordinates_3D(self):
        protCoordinates = self._runDeepFinderImportCoordinates()
        output = getattr(protCoordinates, protCoordinates._possibleOutputs.coordinates.name, None)

        self.assertTrue(output, "There was a problem with coordinates 3d output")
        self.assertEqual(output.getSize(), 347)
        self.assertEqual(output.getSamplingRate(), 10)
        for tomo in output.getPrecedents():
            tomoId = tomo.getTsId()
            for coord in output.iterCoordinates(volume=tomo):
                self.assertEqual(coord.getTomoId(), tomoId)
                # All the coordinates from the test dataset are of the same class
                self.assertEqual(coord.getGroupId(), 1)
                # The coordinates from the test data set do not have score
                self.assertIsNone(coord.getScore())


class TestDeepFinderGenSphereTarget(BaseTest):
    """This class check if the protocol to generate DeepFinder training targets (TomoMasks) works properly."""

    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.dataset = DataSet.getDataSet('deepfinder')

    def _runDeepFinderGenSphereTarget(self):
        # Get tomos:
        protImportTomogram = self.newProtocol(tomo.protocols.ProtImportTomograms,
                                              filesPath=self.dataset.getPath(),
                                              filesPattern='tomo*.mrc',
                                              samplingRate=10)

        self.launchProtocol(protImportTomogram)

        output = getattr(protImportTomogram, 'Tomograms', None)
        self.assertIsNotNone(output, "There was a problem with tomogram output")

        # Get coordinates:
        protImportCoordinates3d = self.newProtocol(ImportCoordinates3D,
                                                   filesPath=self.dataset.getPath(),
                                                   importTomograms=protImportTomogram.Tomograms,
                                                   filesPattern='*.xml')
        self.launchProtocol(protImportCoordinates3d)

        output = getattr(protImportCoordinates3d, protImportCoordinates3d._possibleOutputs.coordinates.name, None)
        self.assertIsNotNone(output, "There was a problem with coordinate output")

        # Define and launch test protocol:
        protGenTargets = self.newProtocol(DeepFinderGenerateTrainingTargetsSpheres,
                                          inputCoordinates=output,
                                          sphereRadii=10)

        self.launchProtocol(protGenTargets)

        return protGenTargets

    def test_generate_sphere_targets(self):
        protGenTargets = self._runDeepFinderGenSphereTarget()
        output = getattr(protGenTargets, protGenTargets._possibleOutputs.segmentedTargets.name, None)

        self.assertTrue(output, "There was a problem with target generation output")
        self.assertTrue(output.getSize() == 2)
        self.assertTrue(output.getSamplingRate() == 10)

        return output


class TestDeepFinderTrain(BaseTest):
    """This class check if the protocol to train the DeepFinder CNN works properly."""

    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.dataset = DataSet.getDataSet('deepfinder')
        # cls.objl = cls.dataset.getFile('coordset0')
        # cls.tomogram = cls.dataset.getFile('tomo0')

    def _runDeepFinderTrain(self):
        # - This part could be adapted when the "tomomask import" protocol is ready - - - - - - - - - - - - - - - - - -
        # Get tomos:
        protImportTomogram = self.newProtocol(tomo.protocols.ProtImportTomograms,
                                              filesPath=self.dataset.getPath(),
                                              filesPattern='tomo*.mrc',
                                              samplingRate=10)

        self.launchProtocol(protImportTomogram)
        outputTomograms = getattr(protImportTomogram, OUTPUT_NAME, None)
        self.assertIsNotNone(outputTomograms, "There was a problem with tomogram output")

        # Get coordinates:
        protImportCoordinates3d = self.newProtocol(ImportCoordinates3D,
                                                   filesPath=self.dataset.getPath(),
                                                   importTomograms=outputTomograms,
                                                   filesPattern='*.xml')
        self.launchProtocol(protImportCoordinates3d)
        outputCoords = getattr(protImportCoordinates3d, protImportCoordinates3d._possibleOutputs.coordinates.name, None)
        self.assertIsNotNone(outputCoords, "There was a problem with coordinate output")

        # Get tomo masks (targets):
        protGenTargets = self.newProtocol(DeepFinderGenerateTrainingTargetsSpheres,
                                          inputCoordinates=outputCoords,
                                          sphereRadii=10)

        self.launchProtocol(protGenTargets)
        outputSegs = getattr(protGenTargets, protGenTargets._possibleOutputs.segmentedTargets.name, None)
        self.assertIsNotNone(outputSegs, "There was a problem with target generation output")

        # Split tomo mask set into train and valid:
        protSplitSets = self.newProtocol(pwem.protocols.ProtSplitSet,
                                         inputSet=outputSegs,
                                         numberOfSets=2)
        self.launchProtocol(protSplitSets)
        tomoMasksTrain = getattr(protSplitSets, 'outputTomoMasks01')
        tomoMasksValid = getattr(protSplitSets, 'outputTomoMasks02')
        self.assertIsNotNone(tomoMasksTrain, 'There was a problem with split set output')
        self.assertIsNotNone(tomoMasksValid, 'There was a problem with split set output')

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # Define and launch test protocol:
        trainProt1 = self._runTrainingWithInValSet(tomoMasksTrain, tomoMasksValid, outputCoords)
        trainProt2 = self._runTrainingWithoutInValSet(outputSegs, outputCoords)
        return [trainProt1, trainProt2]

    def _runTrainingWithInValSet(self, tomoMasksTrain, tomoMasksValid, outputCoords):
        # Param values are chosen so that computation is inexpensive. The output net weights will not be useful.
        protTrain = self.newProtocol(DeepFinderTrain,
                                     useSpecificValidation=True,
                                     tomoMasksTrain=tomoMasksTrain,
                                     tomoMasksValid=tomoMasksValid,
                                     coord=outputCoords,
                                     psize=0,
                                     bsize=1,
                                     epochs=30,
                                     stepsPerE=1,
                                     stepsPerV=1)

        self.launchProtocol(protTrain)
        return protTrain

    def _runTrainingWithoutInValSet(self, outputSegs, outputCoords):
        # Param values are chosen so that computation is inexpensive. The output net weights will not be useful.
        protTrain = self.newProtocol(DeepFinderTrain,
                                     tomoMasksTrain=outputSegs,
                                     useSpecificValidation=False,
                                     coord=outputCoords,
                                     psize=0,
                                     bsize=1,
                                     epochs=30,
                                     stepsPerE=1,
                                     stepsPerV=1)

        self.launchProtocol(protTrain)
        return protTrain

    def test_train(self):
        numClasses = 2  # 1 class of particles + background class
        outputSuffixes = ['epoch10', 'epoch20', 'epoch30', 'FINAL']
        protTrainList = self._runDeepFinderTrain()
        for protTrain in protTrainList:
            for suffix in outputSuffixes:
                output = getattr(protTrain, f'{protTrain._possibleOutputs.netWeights.name}_{suffix}', None)
                self.assertTrue(output, "There was a problem with training output (net model weights)")
                self.assertEqual(output.getNbOfClasses(), numClasses)
                self.assertTrue(exists(output.getPath()))


class TestDeepFinderSegment(BaseTest):
    """This class check if the protocol tomogram segmentation works properly."""

    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.dataset = DataSet.getDataSet('deepfinder')

    def _runDeepFinderSegment(self):
        # Get tomo:
        protImportTomogram = self.newProtocol(tomo.protocols.ProtImportTomograms,
                                              filesPath=self.dataset.getPath() + '/cropped_tomo0.mrc',
                                              samplingRate=10)

        self.launchProtocol(protImportTomogram)
        output = getattr(protImportTomogram, 'Tomograms', None)
        self.assertIsNotNone(output, "There was a problem with tomogram output")

        # Get model weights:
        protImportModel = self.newProtocol(ProtDeepFinderLoadTrainingModel,
                                           netWeightsFile=self.dataset.getPath() + '/net_weights_SHREC2019_4B4T.h5',
                                           numClasses=1)
        self.launchProtocol(protImportModel)
        output = getattr(protImportModel, protImportModel._possibleOutputs.netWeights.name, None)
        self.assertIsNotNone(output, "There was a problem with import model output")

        # Define and launche test protocol:
        protSegment = self.newProtocol(DeepFinderSegment,
                                       inputTomograms=protImportTomogram.Tomograms,
                                       weights=protImportModel.netWeights,
                                       psize=80)
        self.launchProtocol(protSegment)

        return protSegment

    def test_segment(self):
        protSegment = self._runDeepFinderSegment()
        output = getattr(protSegment, protSegment._possibleOutputs.segmentations.name, None)

        self.assertTrue(output, "There was a problem with segmentation output (SetOfTomoMasks)")

        return output


class TestDeepFinderCluster(BaseTest):
    """This class check if the protocol for analyzing/clustering segmentation maps works properly."""

    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.dataset = DataSet.getDataSet('deepfinder')

    def _runDeepFinderCluster(self):
        # Get TomoMask (with target generation protocol):
        # Get tomos:
        protImportTomogram = self.newProtocol(tomo.protocols.ProtImportTomograms,
                                              filesPath=self.dataset.getPath() + '/tomo0.mrc',
                                              samplingRate=10)

        self.launchProtocol(protImportTomogram)
        output = getattr(protImportTomogram, 'Tomograms', None)
        self.assertIsNotNone(output, "There was a problem with tomogram output")

        # Get coordinates:
        protImportCoordinates3d = self.newProtocol(ImportCoordinates3D,
                                                   filesPath=self.dataset.getPath(),
                                                   importTomograms=protImportTomogram.Tomograms,
                                                   filesPattern='*.xml')
        self.launchProtocol(protImportCoordinates3d)
        output = getattr(protImportCoordinates3d, protImportCoordinates3d._possibleOutputs.coordinates.name, None)
        self.assertIsNotNone(output, "There was a problem with coordinate output")

        # Get tomo masks (targets):
        protGenTargets = self.newProtocol(DeepFinderGenerateTrainingTargetsSpheres,
                                          inputCoordinates=output,
                                          sphereRadii=10)

        self.launchProtocol(protGenTargets)
        output = getattr(protGenTargets, protGenTargets._possibleOutputs.segmentedTargets.name, None)
        self.assertIsNotNone(output, "There was a problem with target generation output")

        # Define and launch test protocol:
        protClust = self.newProtocol(DeepFinderCluster,
                                     inputSegmentations=output,
                                     cradius=10)
        self.launchProtocol(protClust)

        return protClust

    def test_cluster(self):
        protClust = self._runDeepFinderCluster()
        output = getattr(protClust, protClust._possibleOutputs.coordinates.name, None)

        self.assertTrue(output, "There was a problem with segmentation map analysis output (coordinates)")
        self.assertTrue(output.getSize() == 155)

        return output

