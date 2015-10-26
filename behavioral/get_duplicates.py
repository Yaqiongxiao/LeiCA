# #FIXME
# #check for duplicates
# import os, glob
# import pandas as pd
# from utils import read_nki_cvs, leica_id_to_a_number_mapping, merge_dataframes, get_health_status
#
#
#
# behav_files_path = '/Users/franzliem/Dropbox/LeiCA/assessment_data_20150817_entireNKI_wlongChlid_wnfb/'
# behav_files_stubs_list =  ['Age_'] #['Demos_', '_Age_'] #, 'STAI']
#
# #preare subject name mapping
# leica_subjects_file = '/Users/franzliem/Dropbox/Workspace/LeiCA/subjects/subjects_2015-09-06_r1-7.txt'
# nki_id_mapping_file = '/Users/franzliem/Dropbox/LeiCA/nki_r1_r6_matched_ids_unq.csv'
#
# leica_subjects = leica_id_to_a_number_mapping(leica_subjects_file, nki_id_mapping_file)
#
#
# df = pd.DataFrame([])
#
# for file_stub in behav_files_stubs_list:
#     file_list = glob.glob(os.path.join(behav_files_path, '*' + file_stub + '*'))
#     #import pdb; pdb.set_trace()
#
#     for f in file_list:
#         print(f)
#         df_add = read_nki_cvs(f)
#         # if 'Subject Type' in df_add.columns:
#         #     print('Dropping Subject Type from df as this often causes duplicates.')
#         #     df_add = df_add.drop('Subject Type', axis=1)
#
#         df = merge_dataframes(df, df_add)
#
#
#
# #add subjects id mapping to df
# df = merge_dataframes(df, leica_subjects)
#
# #remove duplicate indices
#
#
# #remove subjects that are not in leica
# df = df[~df.leica_id.isnull()]
#
#
#
#
# df = df.drop(df.index.get_duplicates())
#
# #remove exactly duplicated lines
# df = df[~df.duplicated()]
#
# #print ambigous duplicates (same index but different values
# print('DUPLICATE INDICES!!!')
# print(df.index.get_duplicates())
