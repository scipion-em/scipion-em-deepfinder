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
from tomo.objects import Tomogram, SetOfTomograms
import pyworkflow.object as pwobj
from pwem.objects.data import EMObject, Volume, SetOfVolumes


class DeepFinderSegmentation(Volume):
    """Class for storing tomogram segmentation maps. A segmentation should always be linked to its origin tomogram."""
    def __init__(self, **kwargs):
        Volume.__init__(self, **kwargs)
        self._acquisition = None
        self._tsId = pwobj.String(kwargs.get('tsId', None))

        self._tomoPointer = pwobj.Pointer(objDoStore=False)
        self._tomoId = pwobj.Integer()
        self._tomoName = pwobj.String()

    def getTomogram(self): # does not work, similar problem to Coordinate3D.getVolume
        return self._tomoPointer.get()

    def setTomogram(self, tomo):
        self._tomoPointer.set(tomo)
        self._tomoId.set(tomo.getObjId())
        self._tomoName.set(tomo.getFileName())

        self.setSamplingRate(tomo.getSamplingRate())

    def setTomoName(self, tomoName):
        self._tomoName.set(tomoName)

    def getTomoName(self):
        return self._tomoName.get()


class SetOfDeepFinderSegmentations(SetOfVolumes):
    ITEM_TYPE = DeepFinderSegmentation
    EXPOSE_ITEMS = True

    def __init__(self, *args, **kwargs):
        SetOfVolumes.__init__(self, **kwargs)


class DeepFinderNet(EMObject):
    """ Simple class to store the neural network model for DeepFinder. """

    def __init__(self, path=None, **kwargs):
        EMObject.__init__(self, **kwargs)
        self._path = pwobj.String(path)

    def getPath(self):
        return self._path.get()

    def setPath(self, path):
        self._path.set(path)

    def __str__(self):
        return "DeepFinderModel(path=%s)" % self.getPath()