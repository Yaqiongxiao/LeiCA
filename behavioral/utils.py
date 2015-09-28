import os
import pandas as pd
import numpy as np


def get_health_status(filename):
    #     def get_no_axis_1(s):
    #         if s.startswith('#CODE:V71.09'):
    #             return True
    #         else:
    #             return False
    # #CODE:314  #DESC:Attention-Deficit/Hyperactivi
    #         #CODE:296. Depression

    def get_diagnosis(diag_str):
        code_diag_mapping = {'#CODE:V71.09': 'no_axis_1',
                             '#CODE:  #DESC:No Diagnosis or Condition on Axis I': 'no_axis_1',
                             '#CODE:296.': 'depression',
                             '#CODE:314': 'adhd',
                             '#CODE:303': 'drugs',
                             '#CODE:304': 'drugs',
                             '#CODE:305': 'drugs'
                             }
        diag = 'other'
        for k, v in code_diag_mapping.items():
            if diag_str.startswith(k):
                diag = v
        return diag

    df = read_nki_cvs(filename)
    df['diagnosis'] = df['DIAG_01'].map(get_diagnosis)
    df['no_axis_1'] = df['diagnosis'] == 'no_axis_1'
    df = df[['diagnosis', 'no_axis_1', 'DIAG_01']]

    return df


def read_nki_cvs(filename):
    '''
    imports nki csv and returns pandas data frame with 'Anonymous ID' as index
    csv files with header like:
        "","","Calculated Age"
        "Anonymized ID","Subject Type","AGE_04"
        "A000355xx","Child-Age 11","11.183561643836"
    '''

    df = pd.read_csv(filename, header=1, index_col='Anonymized ID')
    df['origin_file'] = os.path.basename(filename)
    return df


def merge_dataframes(df1, df2):
    '''
    returns merged data frame
    with outer: also returns subjects that are only included in one df (with nans)
    '''

    return pd.merge(df1, df2, left_index=True, right_index=True, how='outer')


def leica_id_to_a_number_mapping(leica_subjects_file, nki_id_mapping_file):
    '''
    for release 1...5 nki subjects '010...' finds 'A...' number
    for > r5 subjects
    returns dataframe with index is leica_subject_id and a_number
    '''
    import numpy as np

    leica_subjects = pd.read_csv(leica_subjects_file, dtype=object, header=None, names=['leica_id'])
    leica_subjects.set_index(leica_subjects.leica_id, inplace=True)

    nki_id_mapping = pd.read_csv(nki_id_mapping_file)
    nki_id_mapping.set_index(nki_id_mapping.a_number, inplace=True)
    nki_id_mapping['zero_number'] = ['01' + v[4:] for v in nki_id_mapping.m_number.values]
    bad = []
    for l in leica_subjects.index:
        if l.startswith('A'):  # use A number a
            leica_subjects.loc[l, 'a_number'] = l
        else:
            if np.any(nki_id_mapping.loc[nki_id_mapping.zero_number == l].index):
                leica_subjects.loc[l, 'a_number'] = \
                    nki_id_mapping.loc[nki_id_mapping.zero_number == l].index[0]
            else:
                bad.append(l)
    leica_subjects.set_index(leica_subjects.a_number, inplace=True)

    import warnings
    warnings.warn('REMOVING SUBJECTS WITHOUT M TO A MAPPING. FIX.')
    leica_subjects = leica_subjects[~leica_subjects['a_number'].isnull()]

    leica_subjects.drop('a_number', axis=1, inplace=True)
    return leica_subjects
