# **************************************************************************
# *
# * Authors:     Scipion Team
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
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
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
from matplotlib import pyplot as plt
import pyworkflow.viewer as pwviewer
from pwem.viewers import ImageView
from deepfinder.protocols.protocol_train import DeepFinderTrain


class DeepFinderLCurvesViewer(pwviewer.Viewer):
    _label = 'Learning Curves Viewer'
    _targets = [DeepFinderTrain]

    def _visualize(self, obj, **kwargs):
        view = DFImageView(self.protocol._getExtraPath('net_train_history_plot.png'))
        view._tkParent = self.getTkRoot()
        return [view]


class DFImageView(ImageView):

    def show(self):
        image_file = self.getImagePath()
        plt.figure(num='DeepFinder Learning Curves')
        image = plt.imread(image_file)
        plt.imshow(image)
        plt.axis('off')
        plt.tight_layout()  # Decrease the padding
        plt.show()
