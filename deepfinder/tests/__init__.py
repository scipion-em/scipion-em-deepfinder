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

from pyworkflow.tests import DataSet

DataSet(name='deepfinder', folder='deepfinder',
        files={
               'tomo0': 'tomo0.mrc',
               'tomo1': 'tomo1.mrc',
               'cropped_tomo0': 'cropped_tomo0.mrc',
               'tomomask0': 'target0.mrc',
               'tomomask1': 'target1.mrc',
               'coordset0': 'tomo0.xml',
               'coordset1': 'tomo1.xml',
               'trainmodel': 'net_weights_SHREC2019_4B4T.h5'
        })