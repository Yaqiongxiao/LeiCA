__author__ = 'franzliem'

def aggregate_data(file_list, out_filename):
    '''
    tries to guess data type.
    loads data an concatenates it.
    returns np.array with subjects as first dim
    '''

    import os
    import nibabel as nb
    import numpy as np


    def _merge_nii(file_list, out_filename):
        from nipype.pipeline.engine import Node, Workflow
        import nipype.interfaces.fsl as fsl

        merge = Node(fsl.Merge(dimension='t'), name='merge')
        merge.base_dir = os.getcwd()
        merge.inputs.in_files = file_list
        merge.inputs.merged_file = out_filename
        result = merge.run()

        return result.outputs.merged_file



    def _merge_pickle(file_list, out_filename):
        import pickle
        import numpy as np
        import os
        
        out_data = None

        for matrix_file in file_list:
            with open(matrix_file, 'r') as f:
                in_data = pickle.load(f)

            if out_data is None:
                out_data = {}
                for k in in_data.keys():
                    out_data[k] = in_data[k][np.newaxis,...]
            else:
                for k in in_data.keys():
                    out_data[k] = np.concatenate((out_data[k],  in_data[k][np.newaxis,...]))

        full_out_filename = os.path.join(os.getcwd(), out_filename)
        with open(full_out_filename, 'w') as f:
            pickle.dump(out_data, f)
            
        return full_out_filename
    

    if file_list[0].endswith('.nii.gz'): # 3d nii files
        merged_file = _merge_nii(file_list, out_filename)

    elif file_list[0].endswith('.pkl'): # pickled matrix files
        merged_file = _merge_pickle(file_list, out_filename)
        
    else:
        raise Exception('Cannot guess type from filename: %s'%file_list[0])

    return merged_file
