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
from os.path import join

import pwem
from pyworkflow.utils import Environ

from .constants import *
__version__ = '3.0.0'
_logo = "icon.png"
_references = ['EMMANUEL2020']


class Plugin(pwem.Plugin):
    _homeVar = DF_HOME
    _pathVars = [DF_HOME]
    _url = 'https://deepfinder.readthedocs.io/en/latest/guide.html'

    @classmethod
    def _defineVariables(cls):
        cls._defineEmVar(DF_HOME, DF_FOLDER + '-' + DF_VERSION)
        cls._defineVar(DF_ENV_ACTIVATION, DEFAULT_ACTIVATION_CMD)

    @classmethod
    def getEnviron(cls, gpuId='0'):
        """ Setup the environment variables needed to launch deepfinder. """
        environ = Environ(os.environ)
        if 'PYTHONPATH' in environ:
            # this is required for python virtual env to work
            del environ['PYTHONPATH']

        environ.update({'CUDA_VISIBLE_DEVICES': gpuId})
        return environ

    @classmethod
    def getDeepFinderEnvActivation(cls):
        return cls.getVar(DF_ENV_ACTIVATION)

    @classmethod
    def runDeepFinder(cls, protocol, program, args, cwd=None, gpuId='0'):
        program = cls.getDeepFinderProgram(program)
        fullProgram = '%s %s && %s' % (cls.getCondaActivationCmd(), cls.getDeepFinderEnvActivation(), program)
        protocol.runJob(fullProgram, args, env=cls.getEnviron(gpuId=gpuId), cwd=cwd)

    @classmethod
    def getDeepFinderProgram(cls, program):
        return os.path.join(cls.getHome(), 'bin', '%s' % program)

    @classmethod
    def getDependencies(cls):
        neededProgs = []
        condaActivationCmd = cls.getCondaActivationCmd()
        if not condaActivationCmd:
            neededProgs.append('conda')

        return neededProgs

    @classmethod
    def defineBinaries(cls, env):
        cls.addDeepFinderPackage(env, DF_VERSION)

    @classmethod
    def addDeepFinderPackage(cls, env, version):

        DF_INSTALLED = 'deepfinder_%s_installed' % version
        env_name = getDFEnvName(version)
        # try to get CONDA activation command
        installationCmd = cls.getCondaActivationCmd()

        # Create the environment
        installationCmd += 'conda create -y -n %s -c anaconda python=3.6 cudnn=7.6.0=cuda10.0_0 && ' \
                           % env_name

        # Activate new the environment
        installationCmd += 'conda activate %s && ' % env_name

        # Install downloaded code
        installationCmd += 'pip install -r requirements_gpu.txt && '  # for GPU usage should be requirements_gpu.txt

        # Flag installation finished
        installationCmd += 'touch %s' % DF_INSTALLED

        df_commands = [(installationCmd, DF_INSTALLED)]

        env.addPackage(DF_FOLDER, version=version,
                       url='https://gitlab.inria.fr/serpico/deep-finder/-/archive/master/deep-finder-master.tar.gz',
                       commands=df_commands,
                       buildDir='deep-finder-master',
                       neededProgs=cls.getDependencies(),
                       default=True)

    @classmethod
    def getDeepFinderCmd(cls, program):
        """ Composes a DeepFinder command for a given program. """

        # Program to run
        program = cls.getDeepFinderProgram(program)

        fullProgram = '%s %s && %s' % (cls.getCondaActivationCmd(), cls.getDeepFinderEnvActivation(), program)

        # Command to run
        cmd = fullProgram

        return cmd




