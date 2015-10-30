#!/bin/sh


PYTHONPATH=${PYTHONPATH}:/home/raid2/liem/Dropbox/Workspace:/home/raid2/liem/Dropbox/Workspace/LeiCA:/home/raid2/liem/Dropbox/Workspace/LeiCA/preprocessing:/home/raid2/liem/Dropbox/Workspace/LeiCA/preprocessing/cpac_0391_local
PYTHONPATH=/home/raid2/liem/nipype11:$PYTHONPATH
export PYTHONPATH


source /home/raid2/liem/virtualenvs/leica/bin/activate

FSL --version 5.0 FREESURFER --version 5.3.0 AFNI ANTSENV MATPLOTLIB CPAC
