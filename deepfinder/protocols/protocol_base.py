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
from tomo.constants import BOTTOM_LEFT_CORNER
from tomo.objects import SetOfTomograms
from tomo.protocols import ProtTomoBase
import deepfinder.objects
import deepfinder.convert as cv


class ProtDeepFinderBase(ProtTomoBase):

    def _createSetOfDeepFinderSegmentations(self, suffix=''):
        return self._createSet(deepfinder.objects.SetOfDeepFinderSegmentations,
                               'segmentations%s.sqlite', suffix)

    def _createSetOfCoordinates3DWithScore(self, volSet, suffix=''):
        coord3DSet = self._createSet(deepfinder.objects.SetOfCoordinates3DWithScore,
                                     'coordinates%s.sqlite', suffix,
                                     indexes=['_volId'])
        coord3DSet.setPrecedents(volSet)
        return coord3DSet

    @staticmethod
    def _getObjlFromInputCoordinates(coord3DSet):
        """Get all objects of specified class.
        Args:
            tomoSet (SetOfTomograms)
            coord3DSet (SetOfCoordinates3D)
        Returns:
            list of dict: deep finder object list (contains particle infos)
        """
        objl = []
        tomoList = [tomo.clone() for tomo in coord3DSet.getPrecedents()]
        for tomo in tomoList:
            tomoId = tomo.getObjId()
            for coord in coord3DSet.iterCoordinates(volume=tomoId):
                x = coord.getX(BOTTOM_LEFT_CORNER)
                y = coord.getY(BOTTOM_LEFT_CORNER)
                z = coord.getZ(BOTTOM_LEFT_CORNER)
                lbl = int(str(coord._dfLabel))
                cv.objl_add(objl, label=lbl, coord=[z, y, x], tomo_idx=tomoId)

        return objl

    @staticmethod
    def _getObjlFromInputCoordinatesV2(tomoSet, coord3DSet): # emoebel : I modified a bit to suit my needs
        """Get all Coord objects related to the given Tomogram objects.
        The output is an objl as needed by DeepFinder.
        The tomo_idx in the objl respects the order in tomoSet, which is important for the Train protocol
        Args:
            tomoSet (SetOfTomograms)
            coord3DSet (SetOfCoordinates3D)
        Returns:
            list of dict: deep finder object list (contains particle infos)
        """
        # /!\ tidx is tomo index for object list, tomoId is tomo index for SetOfCoordinates3D. Not the same !!
        objl = []
        for tidx, tomo in enumerate(tomoSet):
            tomoId = tomo.getObjId()
            for coord in coord3DSet.iterCoordinates(volume=tomoId):
                x = coord.getX(BOTTOM_LEFT_CORNER)
                y = coord.getY(BOTTOM_LEFT_CORNER)
                z = coord.getZ(BOTTOM_LEFT_CORNER)
                lbl = int(str(coord._dfLabel))
                cv.objl_add(objl, label=lbl, coord=[z, y, x], tomo_idx=tidx)

        return objl



