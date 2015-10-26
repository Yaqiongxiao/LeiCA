__author__ = 'franzliem'
'''
how to run
run with:
source environs/setenv_MPI_nipype11.sh
'''

import os

# # LeiCA modules
from dMRI.tbss import run_tbss_wf

from variables import dicom_dir, preprocessed_data_dir, working_dir, freesurfer_dir, template_dir, script_dir, ds_dir
from variables import TR_list, full_subjects_list
from variables import vols_to_drop, rois_list, lp_cutoff_freq, hp_cutoff_freq, use_fs_brainmask
from variables import use_n_procs, plugin_name

use_n_procs = 8
plugin_name = 'MultiProc'
#plugin_name = 'CondorDAGMan'

# fixme
#subjects_list = ['A00055542']
subjects_list = full_subjects_list[:10]
working_dir = os.path.join(working_dir, 'wd_tbss')

# fixme
ds_dir = os.path.join(working_dir, 'ds')

dMRI_templates = {'dMRI_data': '{subject_id}/raw_niftis/dMRI/DTI_mx_137_reoriented.nii.gz',
                  'bvec_file': '{subject_id}/raw_niftis/dMRI/*.bvecs',
                  'bval_file': '{subject_id}/raw_niftis/dMRI/*.bvals',
                  }

for subject_id in subjects_list:
    subject_working_dir = os.path.join(working_dir, subject_id)
    subject_ds_dir = os.path.join(ds_dir, subject_id, 'tbss')

    # INPUT PARAMETERS for pipeline
    run_tbss_wf(subject_id=subject_id,
                working_dir=subject_working_dir,
                ds_dir=subject_ds_dir,
                use_n_procs=use_n_procs,
                plugin_name=plugin_name,
                dMRI_templates=dMRI_templates,
                in_path=preprocessed_data_dir)
