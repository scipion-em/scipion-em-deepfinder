=============================
Deepfinder plugin for Scipion
=============================

Deepfinder provides a deeplearning picking workflow for cryoelectron microscopy tomography data.

=====
Setup
=====

- **Install this plugin in devel mode:**

Using the command line:

.. code-block::

    scipion3 installp -p local/path/to/scipion-em-deepfinder --devel

Plugin integration
------------------

The following steps presuppose that you have Anaconda or Miniconda installed on your computer.
In ``~/.config/scipion/scipion.conf`` (Option View > Show Hidden Files must be enabled) set
**CONDA_ACTIVATION_CMD** variable in the Packages section.

For example:

.. code-block::

    CONDA_ACTIVATION_CMD = . ~/anaconda3/etc/profile.d/conda.sh

