
__author__ = 'franzliem'
import os

import pandas as pd
import nibabel as nb

from variables import preprocessed_data_dir
from variables import full_subjects_list


#fixme
#full_subjects_list.remove('A00056097')

df = pd.DataFrame([], columns = ['n_trs'])

for subject in full_subjects_list:
    print subject
    rs_nii_file = os.path.join(preprocessed_data_dir, subject, 'raw_niftis/rsfMRI/TR_645/rsfMRI_645_reoriented.nii.gz')
    nii = nb.load(rs_nii_file)
    df.loc[subject] = nii.shape[-1]

print('subject with missing TRs')
print df[df.n_trs<900]
