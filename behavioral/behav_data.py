# FIXME
# check for duplicates
import os, glob, json
import pandas as pd
from utils import read_nki_cvs, leica_id_to_a_number_mapping, merge_dataframes, get_health_status
import numpy as np

save_file = '/Users/franzliem/Dropbox/LeiCA/sample/20150925_leicanki_sample.pkl'

behav_files_path = '/Users/franzliem/Dropbox/LeiCA/assessment_data_20150817_entireNKI_wlongChlid_wnfb/'
behav_files_stubs_list = ['Demos_', '_Age_']  # , 'STAI']

# preare subject name mapping
leica_subjects_file = '/Users/franzliem/Dropbox/Workspace/LeiCA/subjects/subjects_2015-09-06_r1-7.txt'
nki_id_mapping_file = '/Users/franzliem/Dropbox/LeiCA/nki_r1_r6_matched_ids_unq.csv'

# # get sex labels
# variables_dict_file = '/Users/franzliem/Dropbox/Workspace/LeiCA/subjects/codebook/variable_dict.json'
# with open(variables_dict_file) as fi:
#     variables_dict = json.load(fi)
# variables_dict['DEM_002']['response']

# get M to A number mapping
leica_subjects = leica_id_to_a_number_mapping(leica_subjects_file, nki_id_mapping_file)

df = pd.DataFrame([])

for file_stub in behav_files_stubs_list:
    file_list = glob.glob(os.path.join(behav_files_path, '*' + file_stub + '*'))
    # import pdb; pdb.set_trace()

    for f in file_list:
        print(f)
        df_add = read_nki_cvs(f)
        df = merge_dataframes(df, df_add)


# sex mapping
sex_mapping = {1: 'M', 2: 'F'}
df['sex'] = df.DEM_002
df = df.replace({'sex': sex_mapping})


# get health status
diagnostics_file = glob.glob(os.path.join(behav_files_path, '*_Diagnostic Summary_*'))[0]
df_health = get_health_status(diagnostics_file)
df = merge_dataframes(df, df_health)

# add subjects id mapping to df
df = merge_dataframes(df, leica_subjects)

# remove subjects that are not in leica
df = df[~df.leica_id.isnull()]

# remove exactly duplicated lines
df = df[~df.duplicated()]

# print ambigous duplicates (same index but different values
print('DUPLICATE INDICES!!!')
print(df.index.get_duplicates())
print('')

import warnings

warnings.warn('NONAMBIGOUS INDEX INFO IN DF. FIX.')
df = df[~df.index.duplicated()]


# remove bad subjects (e.g. failed preprocessing/only few TRs)

bad_subjects_list = ['0124028',
                     'A00051882']

for b in bad_subjects_list:
    df = df[~(df.leica_id == b)]

pd.to_pickle(df, save_file)
