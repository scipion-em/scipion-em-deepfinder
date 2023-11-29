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
from tomo.objects import Coordinate3D, SetOfCoordinates3D
import pyworkflow.object as pwobj
from pwem.objects.data import EMObject


class DeepFinderNet(EMObject):
    """ Simple class to store the neural network model for DeepFinder. """

    def __init__(self, path=None, noClasses=None, **kwargs):
        EMObject.__init__(self, **kwargs)
        self._path = pwobj.String(path)
        self._nbOfClasses = pwobj.Integer(noClasses)  # nb of classes corresponding to this model (background included)

    def getPath(self):
        return self._path.get()

    def setPath(self, path):
        self._path.set(path)

    def getNbOfClasses(self):
        return self._nbOfClasses.get()

    def setNbOfClasses(self, nclass):
        self._nbOfClasses.set(nclass)

    def __str__(self):
        return "DeepFinderModel(path=%s)" % self.getPath()
