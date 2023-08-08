# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     Scipion Team
# *
# * your institution
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
from os.path import join, isfile, abspath

from deepfinder.convert import objl_read
from pyworkflow.utils import removeBaseExt
from tomo.viewers.views_tkinter_tree import TomogramsTreeProvider


class ParticleAnnotatorProvider(TomogramsTreeProvider):

    def getObjectInfo(self, inTomo):
        tomogramName = removeBaseExt(inTomo.getFileName())
        filePath = join(self._path, "objl_annot_" + tomogramName + ".xml")

        if isfile(filePath):
            nCoords = len(objl_read(abspath(filePath)))
            return {'key': tomogramName, 'parent': None,
                    'text': tomogramName, 'values': (nCoords, 'DONE'),
                    'tags': "done"}
        else:
            return {'key': tomogramName, 'parent': None,
                    'text': tomogramName, 'values': (0, 'PENDING'),
                    'tags': "pending"}

    def getColumns(self):
        return [('Tomograms', 300), ("# coords", 100), ('status', 150)]
