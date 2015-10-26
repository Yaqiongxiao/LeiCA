__author__ = 'franzliem'

import os
import pandas as pd

# # LeiCA modules
from learning.mean_con_mat_wf import mean_con_mat_wf

from variables import working_dir, freesurfer_dir, template_dir, script_dir, ds_dir, preprocessed_data_dir
from variables import behav_file
from variables import vols_to_drop, rois_list, lp_cutoff_freq, hp_cutoff_freq, use_fs_brainmask
from variables import use_n_procs, plugin_name

working_dir = os.path.join(working_dir, 'wd_group_con_mats')

use_n_procs = 4
plugin_name = 'MultiProc'

bp_freq_list = [(None, None), (0.01, 0.1)]
parcellations_list = ['msdl',
                      'craddock_205',
                      'gordon'
                      ]

extraction_methods_list = ['correlation']  # , 'sparse_inverse_covariance']



# load subjects list
df = pd.read_pickle(behav_file)
subjects_list = df.leica_id.values


import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    mean_con_mat_wf(subjects_list=subjects_list,
                    preprocessed_data_dir=preprocessed_data_dir,
                    working_dir=working_dir,
                    ds_dir=ds_dir,
                    parcellations_list=parcellations_list,
                    extraction_methods_list=extraction_methods_list,
                    bp_freq_list=bp_freq_list,
                    use_n_procs=use_n_procs,
                    plugin_name=plugin_name)
