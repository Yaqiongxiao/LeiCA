def mean_con_mat_wf(subjects_list,
                    preprocessed_data_dir,
                    working_dir,
                    ds_dir,
                    parcellations_list,
                    extraction_methods_list,
                    bp_freq_list,
                    use_n_procs,
                    plugin_name):

    import os
    from nipype import config
    from nipype.pipeline.engine import Node, Workflow, MapNode, JoinNode
    import nipype.interfaces.utility as util
    import nipype.interfaces.io as nio
    from nipype.interfaces.freesurfer.utils import ImageInfo
    from utils import aggregate_data


    #####################################
    # GENERAL SETTINGS
    #####################################
    wf = Workflow(name='mean_con_mats')
    wf.base_dir = os.path.join(working_dir)

    nipype_cfg = dict(logging=dict(workflow_level='DEBUG'), execution={'stop_on_first_crash': True,
                                                                       'remove_unnecessary_outputs': True,
                                                                       'job_finished_timeout': 120})
    config.update_config(nipype_cfg)
    wf.config['execution']['crashdump_dir'] = os.path.join(working_dir, 'crash')

    ds = Node(nio.DataSink(), name='ds')
    ds.inputs.base_directory = os.path.join(ds_dir, 'group_conmats_test')

    ds.inputs.regexp_substitutions = [
        # ('subject_id_', ''),
        ('_parcellation_', ''),
        ('_bp_freqs_', 'bp_'),
        ('_extraction_method_', ''),
        ('_subject_id_[A0-9]*/', '')
    ]



    #####################################
    # SET ITERATORS
    #####################################
    # SUBJECTS ITERATOR
    subjects_infosource = Node(util.IdentityInterface(fields=['subject_id']), name='subjects_infosource')
    subjects_infosource.iterables = ('subject_id', subjects_list)

    # PARCELLATION ITERATOR
    parcellation_infosource = Node(util.IdentityInterface(fields=['parcellation']), name='parcellation_infosource')
    parcellation_infosource.iterables = ('parcellation', parcellations_list)

    # BP FILTER ITERATOR
    bp_filter_infosource = Node(util.IdentityInterface(fields=['bp_freqs']), name='bp_filter_infosource')
    bp_filter_infosource.iterables = ('bp_freqs', bp_freq_list)

    # EXTRACTION METHOD ITERATOR
    extraction_method_infosource = Node(util.IdentityInterface(fields=['extraction_method']),
                                        name='extraction_method_infosource')
    extraction_method_infosource.iterables = ('extraction_method', extraction_methods_list)



    def create_file_list_fct(subjects_list, base_path, parcellation, bp_freqs, extraction_method):
        import os

        file_list = []
        for s in subjects_list:
            file_list.append(os.path.join(base_path, s, 'metrics/con_mat/matrix',
                                                       'bp_%s.%s'%(bp_freqs),
                            parcellation, extraction_method, 'matrix.pkl'))
        return file_list

    create_file_list = Node(util.Function(input_names=['subjects_list', 'base_path', 'parcellation', 'bp_freqs', 'extraction_method'],
                                       output_names=['file_list'],
                                       function=create_file_list_fct),
                         name='create_file_list')
    create_file_list.inputs.subjects_list = subjects_list
    create_file_list.inputs.base_path = preprocessed_data_dir
    wf.connect(parcellation_infosource, 'parcellation', create_file_list, 'parcellation')
    wf.connect(bp_filter_infosource, 'bp_freqs', create_file_list, 'bp_freqs')
    wf.connect(extraction_method_infosource, 'extraction_method', create_file_list, 'extraction_method')




    aggregate = Node(util.Function(input_names=['file_list', 'out_filename'],
                                       output_names=['merged_file'],
                                       function=aggregate_data),
                         name='aggregate')
    aggregate.inputs.out_filename = 'matrix.pkl'
    wf.connect(create_file_list, 'file_list', aggregate, 'file_list')



    def plot_matrix_fct(in_file):
        import pickle, os
        import pylab as plt
        import numpy as np


        with open(in_file, 'r') as f:
            matrix_dict = pickle.load(f)

        out_file_list = []
        for m_type in matrix_dict.keys():
            mean_matrix = np.mean(matrix_dict[m_type], axis=0)
            fig = plt.imshow(mean_matrix, interpolation='nearest')
            plt.title(in_file)

            out_file = os.path.join(os.getcwd(), m_type+'.png')
            out_file_list.append(out_file)
            plt.savefig(out_file)

        return out_file_list

    plot_matrix = Node(util.Function(input_names=['in_file'],
                                       output_names=['out_file_list'],
                                       function=plot_matrix_fct),
                         name='plot_matrix')
    wf.connect(aggregate, 'merged_file', plot_matrix, 'in_file')
    wf.connect(plot_matrix, 'out_file_list', ds, 'group_mats.@groupmats')


    #####################################
    # RUN WF
    #####################################
    wf.write_graph(dotfilename=wf.name, graph2use='colored', format='pdf')  # 'hierarchical')
    wf.write_graph(dotfilename=wf.name, graph2use='orig', format='pdf')
    wf.write_graph(dotfilename=wf.name, graph2use='flat', format='pdf')

    if plugin_name == 'CondorDAGMan':
        wf.run(plugin=plugin_name)
    if plugin_name == 'MultiProc':
        wf.run(plugin=plugin_name, plugin_args={'n_procs': use_n_procs})
