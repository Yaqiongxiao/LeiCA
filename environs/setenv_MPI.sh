#!/bin/sh


PYTHONPATH=${PYTHONPATH}:/home/raid2/liem/Dropbox/Workspace:/home/raid2/liem/Dropbox/Workspace/LeiCA:/home/raid2/liem/Dropbox/Workspace/LeiCA/preprocessing:/home/raid2/liem/Dropbox/Workspace/LeiCA/preprocessing/cpac_0391_local
export PYTHONPATH


#make sure that DCMSTACK is called AFTER CPAC
FSL --version 5.0 FREESURFER --version 5.3.0 AFNI CPAC DCMSTACK PANDAS NILEARN SKLEARN MATPLOTLIB NUMPY SEABORN
