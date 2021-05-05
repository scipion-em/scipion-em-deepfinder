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
from pyworkflow.tests import BaseTest, setupTestProject

import tomo.protocols
from pyworkflow.utils import magentaStr

import deepfinder.protocols

from . import DataSet

class TestDeepFinderImportCoordinates(BaseTest):
    """This class check if the protocol to import DeepFinder object lists works properly."""
    # modelled after tomo.test.TestTomoImportSetOfCoordinates3D

    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.dataset = DataSet.getDataSet('deepfinder')
        #cls.objl = cls.dataset.getFile('coordset0')
        #cls.tomogram = cls.dataset.getFile('tomo0')

    def _runDeepFinderImportCoordinates(self):
        print(magentaStr('=======> ' + self.dataset.getPath()))
        protImportTomogram = self.newProtocol(tomo.protocols.ProtImportTomograms,
                                              filesPath=self.dataset.getPath(),
                                              filesPattern='tomo*.mrc',
                                              samplingRate=10)

        self.launchProtocol(protImportTomogram)

        output = getattr(protImportTomogram, 'outputTomograms', None)

        self.assertIsNotNone(output, "There was a problem with tomogram output")

        protImportCoordinates3d = self.newProtocol(deepfinder.protocols.ImportCoordinates3D,
                                                   filesPath=self.dataset.getPath(),
                                                   importTomograms=protImportTomogram.outputTomograms,
                                                   filesPattern='.xml')
        self.launchProtocol(protImportCoordinates3d)

        return protImportCoordinates3d

    def test_import_set_of_coordinates_3D(self):
        protCoordinates = self._runDeepFinderImportCoordinates()
        output = getattr(protCoordinates, 'outputCoordinates', None)
        self.assertTrue(output, "There was a problem with coordinates 3d output")
        self.assertTrue(output.getSize() == 347)
        self.assertTrue(output.getSamplingRate() == 10)

        return output