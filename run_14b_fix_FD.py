import os
import numpy as np
import pandas as pd
import glob

def calculate_FD_P(in_file):
    """
    Baed on CPAC function
    https://github.com/FCP-INDI/C-PAC/blob/master/CPAC/generate_motion_statistics/generate_motion_statistics.py#L549
    fixed translation/rotation order for FSL. see:
    https://github.com/FCP-INDI/C-PAC/commit/ebc0d9fc4e683691a0fdfb95489236e841be94a0

    Method to calculate Framewise Displacement (FD) calculations
    (Power et al., 2012)

    Parameters
    ----------
    in_file : string
        movement parameters vector file path

    Returns
    -------
    FD time series
    """
    import numpy as np

    lines = open(in_file, 'r').readlines()
    rows = [[float(x) for x in line.split()] for line in lines]
    cols = np.array([list(col) for col in zip(*rows)])

    translations = np.transpose(np.abs(np.diff(cols[3:6, :])))
    rotations = np.transpose(np.abs(np.diff(cols[0:3, :])))

    FD_power = np.sum(translations, axis = 1) + (50*3.141/180)*np.sum(rotations, axis =1)

    #FD is zero for the first time point
    FD_power = np.insert(FD_power, 0, 0)
    return FD_power




if __name__ == "__main__":
    subjects_path = '/scr/adenauer2/Franz/LeiCA_NKI/results'
    par_template_path = '{subject_id}/rsfMRI_preprocessing/realign/par/TR_645/rest_realigned.nii.gz.par'
    out_file = '/scr/adenauer2/Franz/LeiCA_NKI/results/FD_fix/FD_fixed_n%s.csv'

    df = pd.DataFrame([], columns=['mean_FD_P', 'max_FD_P'])
    df.index.name = 'subject_id'

    os.chdir(subjects_path)
    subjects_list = glob.glob('0*') + glob.glob('A*')

    for subject_id in subjects_list:
        par_file = par_template_path.format(subject_id=subject_id)
        FD_ts = calculate_FD_P(par_file)
        mean_FD_P = np.mean(FD_ts)
        max_FD_P = np.max(FD_ts)
        df.loc[subject_id] = {'mean_FD_P': mean_FD_P, 'max_FD_P': max_FD_P}


    df.to_csv(out_file%(len(df)))

