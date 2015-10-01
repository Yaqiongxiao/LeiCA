__author__ = 'franzliem'
'''
how to run

'''

import os

# # LeiCA modules
from metrics import calc_con_mats

from variables import working_dir, freesurfer_dir, template_dir, script_dir, ds_dir, preprocessed_data_dir
from variables import TR_list, full_subjects_list
from variables import vols_to_drop, rois_list, lp_cutoff_freq, hp_cutoff_freq, use_fs_brainmask
from variables import use_n_procs, plugin_name


working_dir = os.path.join(working_dir, 'wd_con_mats')


# #fixme
# full_subjects_list = ['A00054581']

# INPUT PARAMETERS for pipeline

#use_n_procs = 30
#plugin_name = 'MultiProc'

bp_freq_list = [(None, None), (0.01, 0.1)]

parcellations_dict = {}
# parcellations_dict['msdl'] = {
#     'nii_path': os.path.join(template_dir, 'parcellations/msdl_atlas/MSDL_rois/msdl_rois.nii.gz'),
#     'is_probabilistic': True}
# parcellations_dict['craddock_205'] = {
#     'nii_path': os.path.join(template_dir, 'parcellations/craddock_2012/scorr_mean_single_resolution/scorr_mean_parc_n_21_k_205_rois.nii.gz'),
#     'is_probabilistic': False}
parcellations_dict['gordon'] = {
    'nii_path': os.path.join(template_dir, 'parcellations/Gordon_2014_Parcels/Parcels_MNI_111_sorted.nii.gz'),
    'is_probabilistic': False}


extraction_methods_list = ['correlation', 'sparse_inverse_covariance']


# fixme
# ignore warning from np.rank
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    calc_con_mats.connectivity_matrix_wf(subjects_list=full_subjects_list,
                                         preprocessed_data_dir=preprocessed_data_dir,
                                         working_dir=working_dir,
                                         ds_dir=ds_dir,
                                         parcellations_dict=parcellations_dict,
                                         extraction_methods_list=extraction_methods_list,
                                         bp_freq_list=bp_freq_list,
                                         use_n_procs=use_n_procs,
                                         plugin_name=plugin_name)
