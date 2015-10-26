__author__ = 'franzliem'

import os
import pandas as pd

# # LeiCA modules
from learning.learning_prepare_data_wf import learning_prepare_data_wf

from variables import working_dir, freesurfer_dir, template_dir, script_dir, ds_dir, preprocessed_data_dir
from variables import behav_file
from variables import vols_to_drop, rois_list, lp_cutoff_freq, hp_cutoff_freq, use_fs_brainmask
# from variables import use_n_procs, plugin_name

working_dir = os.path.join(working_dir, 'wd_learning')

use_n_procs = 32
plugin_name = 'MultiProc'



# fixme
ds_dir = os.path.join(working_dir, 'learning_out')

# # load subjects list
# df = pd.read_pickle(behav_file)
# subjects_list = df.leica_id.values

# fixme
# in_data_name = 'matrix_gordon_correlation_bpNone.None'
# in_data_name = 'reho'

# in_data_name_list =['matrix_gordon_correlation_bpNone.None', 'reho']
# in_data_name_list = ['alff',
#                      'variability_std',
#                      'falff',
#                      'evc',
#                      'dc',
#                      'reho']
# in_data_name_list = ['alff', 'alff_gordon']

# # # # # # # # # #
# data_lookup_dict
# # # # # # # # # #
gordon_path = os.path.join(template_dir, 'parcellations/Gordon_2014_Parcels/Parcels_MNI_111_sorted.nii.gz')
craddock_788_path = os.path.join(template_dir, 'parcellations/craddock_2012/scorr_mean_single_resolution/scorr_mean_parc_n_43_k_788_rois.nii.gz')

data_lookup_dict = {}

data_lookup_dict['matrix_gordon_correlation_bpNone.None'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}', 'metrics/con_mat/matrix',
                             'bp_None.None', 'gordon', 'correlation', 'matrix.pkl'),
    'matrix_name': 'correlation'}

data_lookup_dict['matrix_gordon_correlation_bp0.01.0.1'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}', 'metrics/con_mat/matrix',
                             'bp_0.01.0.1', 'gordon', 'correlation', 'matrix.pkl'),
    'matrix_name': 'correlation'}

data_lookup_dict['matrix_craddock_205_correlation_bpNone.None'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}', 'metrics/con_mat/matrix',
                             'bp_None.None', 'craddock_205', 'correlation', 'matrix.pkl'),
    'matrix_name': 'correlation'}

data_lookup_dict['matrix_craddock_205_correlation_bp0.01.0.1'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}', 'metrics/con_mat/matrix',
                             'bp_0.01.0.1', 'craddock_205', 'correlation', 'matrix.pkl'),
    'matrix_name': 'correlation'}

data_lookup_dict['matrix_msdl_correlation_bp0.01.0.1'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}', 'metrics/con_mat/matrix',
                             'bp_0.01.0.1', 'msdl', 'correlation', 'matrix.pkl'),
    'matrix_name': 'correlation'}

data_lookup_dict['matrix_msdl_correlation_bpNone.None'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}', 'metrics/con_mat/matrix',
                             'bp_None.None', 'msdl', 'correlation', 'matrix.pkl'),
    'matrix_name': 'correlation'}

data_lookup_dict['reho'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/reho/reho_MNI_3mm/TR_645/ReHo_warp.nii.gz')}

data_lookup_dict['falff'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/alff/falff_MNI_3mm/TR_645/brain_mask_epiSpace_calc_warp.nii.gz')}

data_lookup_dict['alff'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/alff/alff_MNI_3mm/TR_645/residual_filtered_3dT_warp.nii.gz')}

data_lookup_dict['alff_gordon'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/alff/alff_MNI_3mm/TR_645/residual_filtered_3dT_warp.nii.gz'),
    'parcellation_path': gordon_path}

data_lookup_dict['alff_craddock_788'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/alff/alff_MNI_3mm/TR_645/residual_filtered_3dT_warp.nii.gz'),
    'parcellation_path': craddock_788_path}

data_lookup_dict['alff_gm'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/alff/alff_MNI_3mm/TR_645/residual_filtered_3dT_warp.nii.gz'),
    'use_gm_mask': True}

data_lookup_dict['alff_6mm'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/alff/alff_MNI_3mm/TR_645/residual_filtered_3dT_warp.nii.gz'),
    'fwhm': 6}

data_lookup_dict['variability_std'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/variability/MNI_3mm/TR_645/ts_std_warp.nii.gz')}

data_lookup_dict['dc'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/centrality/dc/TR_645/degree_centrality_binarize.nii.gz')}
data_lookup_dict['dc_gm'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/centrality/dc/TR_645/degree_centrality_binarize.nii.gz'),
    'use_gm_mask': True}

data_lookup_dict['evc'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/centrality/evc/TR_645/eigenvector_centrality_binarize.nii.gz')}

data_lookup_dict['evc_gm'] = {
    'path_str': os.path.join(preprocessed_data_dir, '{subject_id}',
                             'metrics/centrality/evc/TR_645/eigenvector_centrality_binarize.nii.gz'),
    'use_gm_mask': True}

# for k in data_lookup_dict.keys():
#     data_lookup_dict[k + '_gordon'] = {
#         'path_str': data_lookup_dict[k]['path_str'],
#         'parcellation_path': gordon_path}


# in_data_name_list = ['alff', 'falff', 'reho', 'evc_gm', 'dc_gm', 'variability_std',
#                      'matrix_gordon_correlation_bpNone.None', 'matrix_gordon_correlation_bp0.01.0.1',
#                      'matrix_craddock_205_correlation_bpNone.None', 'matrix_craddock_205_correlation_bp0.01.0.1',
#                      'matrix_msdl_correlation_bp0.01.0.1', 'matrix_msdl_correlation_bpNone.None',
#                      ]

# in_data_name_list = ['alff', 'falff', 'reho', 'variability_std', 'matrix_craddock_205_correlation_bpNone.None',
#                      'matrix_gordon_correlation_bpNone.None',
#                      ['alff', 'falff', 'reho', 'variability_std', 'matrix_craddock_205_correlation_bpNone.None'],
#                      ['alff', 'variability_std', 'matrix_craddock_205_correlation_bpNone.None']]

in_data_name_list = [['alff'], ['alff_gordon'], ['alff_craddock_788']]

import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
learning_prepare_data_wf(working_dir=working_dir,
                         ds_dir=ds_dir,
                         template_dir=template_dir,
                         df_file=behav_file,
                         in_data_name_list=in_data_name_list,
                         data_lookup_dict=data_lookup_dict,
                         use_n_procs=use_n_procs,
                         plugin_name=plugin_name)
