# **************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
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
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
"""
This file contains constants related to scipion-em-dynamo protocols
"""


def getDFEnvName(version):
    return "deepfinder-%s" % version


DF_HOME = 'DF_HOME'
DF_VERSION = '0.2'
DF_FOLDER = 'deepfinder'
DEFAULT_ENV_NAME = getDFEnvName(DF_VERSION)
DEFAULT_ACTIVATION_CMD = 'conda activate ' + DEFAULT_ENV_NAME
DF_ENV_ACTIVATION = 'DF_ENV_ACTIVATION'
# DF_CLASS_LABEL = '_dfLabel'

# DeepFinder field for its XML coords files:
# Mandatory attributes
DF_LABEL = 'class_label'
DF_COORD_X = 'x'
DF_COORD_Y = 'y'
DF_COORD_Z = 'z'
# Optional attributes
DF_TOMO_IDX = 'tomo_idx'
DF_OBJ_ID = 'obj_id'
DF_PSI = 'psi'
DF_PHI = 'phi'
DF_THETA = 'the'
DF_SCORE = 'cluster_size'
