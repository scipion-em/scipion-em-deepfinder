=============================
Deepfinder plugin for Scipion
=============================

.. image:: https://img.shields.io/pypi/v/scipion-em-deepfinder.svg
        :target: https://pypi.python.org/pypi/scipion-em-deepfinder
        :alt: PyPI release

.. image:: https://img.shields.io/pypi/l/scipion-em-deepfinder.svg
        :target: https://pypi.python.org/pypi/scipion-em-deepfinder
        :alt: License

.. image:: https://img.shields.io/pypi/pyversions/scipion-em-deepfinder.svg
        :target: https://pypi.python.org/pypi/scipion-em-deepfinder
        :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/dm/scipion-em-deepfinder
        :target: https://pypi.python.org/pypi/scipion-em-deepfinder
        :alt: Downloads


Deepfinder_ provides a deeplearning picking workflow for cryo-electron microscopy tomography data.

============
Installation
============
The plugin can be installed in user (stable) or developer (latest, may be unstable) mode:

**1. User (stable) version:**:

.. code-block::

    scipion3 installp -p scipion-em-deepfinder

**2. Developer (latest, may be unstable) version:**:

* Clone the source code repository:

.. code-block::

    git clone https://github.com/scipion-em/scipion-em-deepfinder.git

* Move to devel branch:

.. code-block::

    git checkout devel

* Install:

.. code-block::

    scipion3 installp -p local/path/to/scipion-em-deepfinder --devel

Configuration variables
-----------------------
*CONDA_ACTIVATION_CMD*: If undefined, it will rely on conda command being in the
PATH (not recommended), which can lead to execution problems mixing Scipion
python with conda ones. One example of this can be seen below but
depending on your conda version and shell you will need something different:
CONDA_ACTIVATION_CMD = eval "$(/extra/anaconda/bin/conda shell.bash hook)"

*DF_ENV_ACTIVATION*: (default = conda activate deepfinder-0.2):
Command to activate the DeepFinder environment.

*DF_HOME*: (default = ScipionHome/Software/em/deepfinder-0.2):
Location of the DeepFinder package.

=========
Protocols
=========
The integrated protocols are:

1. Annotate: manual annotation of macromolecules in the tomograms, using a visual tool.

2. Generate sphere targets: generates segmentation maps from annotations. These segmentation maps will be used as 
   targets to train DeepFinder

3. Training.

4. Segment: segmentation of tomograms, using a trained neural network.

5. Cluster: analyses the segmentation maps and outputs particle coordinates and class.

6. Import DeepFinder coordinates.

7. Import DeepFinder Training model.

=====
Tests
=====

The installation can be checked out running some tests. To list all of them, execute:

.. code-block::

     scipion3 tests --grep deepfinder

To run all of them, execute:

.. code-block::

     scipion3 tests --grep deepfinder --run

To run a specific test, for example, the tests to check the sphere targets generation (the following command
can be copied from the test list displayed when listing the tests, as explained above):

.. code-block::

    scipion3 tests deepfinder.tests.test_deepfinder.TestDeepFinderGenSphereTarget

===============
Video tutorials
===============

A playlist_ was created in I2PC Youtube channel to show how to use Deepfinder plugin in Scipion.


==========
References
==========

* `Deep Learning Improves Macromolecules Localization and Identification in 3D Cellular Cryo-Electron Tomograms. <https://doi.org/10.1038/s41592-021-01275-4>`_
  Emmanuel Moebel, Antonio Martinez-Sanchez et al., Nat Methods 18, 1386–1394 (2021).


===================
Contact information
===================

If you experiment any problem, please contact us here: scipion-users@lists.sourceforge.net or open an issue_.

We'll be pleased to help.

*Scipion Team*

.. _issue: https://github.com/scipion-em/scipion-em-deepfinder/issues
.. _Deepfinder: https://gitlab.inria.fr/serpico/deep-finder
.. _playlist: https://www.youtube.com/watch?v=20Xxs6zZS3k&list=PLyJiuGnB9hAx5_GBfgSQza9FEFMZKW7Rz