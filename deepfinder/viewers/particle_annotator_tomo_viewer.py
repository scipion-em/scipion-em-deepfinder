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

import threading
from os.path import abspath
from pyworkflow.gui.dialog import ToolbarListDialog
from pyworkflow.utils.path import removeBaseExt
from deepfinder import Plugin


class ParticleAnnotatorDialog(ToolbarListDialog):
    """
    This class allows to  call a deepfinder particle annotation subprocess for rach element of a list of Tomograms.
    """

    tomo = None
    proc = None

    def __init__(self, parent, path, **kwargs):
        self.path = path
        self.provider = kwargs.get("provider", None)
        self.prot = kwargs.get('prot', None)
        ToolbarListDialog.__init__(self, parent,
                                   "Particle Annotator Object Manager",
                                   allowsEmptySelection=False,
                                   itemDoubleClick=self.doubleClickOnTomogram,
                                   allowSelect=False,
                                   **kwargs)

    def refresh_gui(self):
        if self.proc.is_alive():
            self.after(1000, self.refresh_gui)
        else:
            self.tree.update()

    def doubleClickOnTomogram(self, e=None):
        self.tomo = e
        self.proc = threading.Thread(target=self.launchParticleAnnotatorForTomogram, args=(self.tomo,))
        self.proc.start()
        self.after(1000, self.refresh_gui)

    def launchParticleAnnotatorForTomogram(self, tomo):
        print("\n==> Running Deepfinder Particle Annotator:")
        tomoName = tomo.getFileName()
        fname_objl = 'objl_annot_' + removeBaseExt(tomoName) + '.xml'
        deepfinder_args = ' -t %s ' % abspath(tomoName)
        deepfinder_args += '-o %s' % abspath(self.prot._getExtraPath(fname_objl))
        deepfinder_args += ' -scipion'  # hide unnecessary buttons from DeepFinder GUI
        Plugin.runDeepFinder(self.prot, 'annotate', deepfinder_args)
