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

from tomo.protocols import ProtTomoBase
import deepfinder.objects
import deepfinder.convert as cv

class ProtDeepFinderBase(ProtTomoBase):
    def _createSetOfDeepFinderSegmentations(self, suffix=''):
        return self._createSet(deepfinder.objects.SetOfDeepFinderSegmentations,
                               'segmentations%s.sqlite', suffix)

    def _getObjlFromInputCoordinates(self, inputCoordinates, tomoname_list):
        """Get all objects of specified class.

        Args:
            inputCoordinates (MultiPointerParam)
            tomoname_list (list of strings): ['/path/to/tomo1.mrc', '/path/to/tomo2.mrc', '/path/to/tomo3.mrc']
        Returns:
            list of dict: deep finder object list (contains particle infos)
        """
        l = 1  # one class/setOfCoordinate3D. Class labels are reassigned here, and may not correspond to the label from annotation step.
        objl = []
        for pointer in inputCoordinates:
            coord3DSet = pointer.get()
            for coord in coord3DSet.iterItems():
                x = coord.getX()
                y = coord.getY()
                z = coord.getZ()
                lbl = l
                tidx = tomoname_list.index(coord.getVolName())
                cv.objl_add(objl, label=lbl, coord=[z, y, x], tomo_idx=tidx)
            l += 1
        return objl

