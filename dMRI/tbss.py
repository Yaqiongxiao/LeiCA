def run_tbss_wf(subject_id,
                working_dir,
                ds_dir,
                use_n_procs,
                plugin_name,
                dMRI_templates,
                in_path):
    import os
    from nipype import config
    from nipype.pipeline.engine import Node, Workflow, MapNode, JoinNode
    import nipype.interfaces.utility as util
    import nipype.interfaces.io as nio
    from nipype.interfaces import fsl
    from nipype.workflows.dmri.fsl.artifacts import hmc_pipeline, ecc_pipeline
    from nipype.workflows.dmri.fsl.utils import b0_average, extract_bval
    #from nipype.workflows.dmri.fsl.tbss import create_tbss_all, create_tbss_non_FA

    #####################################
    # GENERAL SETTINGS
    #####################################
    wf = Workflow(name='tbss_wf')
    wf.base_dir = os.path.join(working_dir)

    nipype_cfg = dict(logging=dict(workflow_level='DEBUG'), execution={'stop_on_first_crash': True,
                                                                       'remove_unnecessary_outputs': False,
                                                                       'job_finished_timeout': 15})
    config.update_config(nipype_cfg)
    wf.config['execution']['crashdump_dir'] = os.path.join(working_dir, 'crash')

    ds = Node(nio.DataSink(base_directory=ds_dir), name='ds')

    ds.inputs.regexp_substitutions = [
        ('_subject_id_[A0-9]*/', ''),
    ]


     # GET SUBJECT SPECIFIC FUNCTIONAL DATA
    selectfiles = Node(nio.SelectFiles(dMRI_templates, base_directory=in_path), name="selectfiles")
    selectfiles.inputs.subject_id = subject_id

    #####################################
    # WF
    #####################################


    # GET B0 MASK
    b0_4d_init_0 = Node(util.Function(input_names=['in_dwi', 'in_bval', 'b'], output_names=['out_file'],
        function=extract_bval), name='b0_4d_init_0')
    wf.connect(selectfiles, 'dMRI_data', b0_4d_init_0, 'in_dwi')
    wf.connect(selectfiles, 'bval_file', b0_4d_init_0, 'in_bval')
    b0_4d_init_0.inputs.b = 5

    first_b0 = Node(fsl.ExtractROI(t_min=0, t_size=1), name='first_b0')
    wf.connect(b0_4d_init_0, 'out_file', first_b0, 'in_file')

    flirt = Node(fsl.FLIRT(dof=6, out_file='b0_moco.nii.gz'), name='flirt')
    wf.connect(b0_4d_init_0, 'out_file', flirt, 'in_file')
    wf.connect(first_b0, 'roi_file', flirt, 'reference')

    mean_b0_moco_init_0 = Node(fsl.MeanImage(), name='mean_b0_moco_init_0')
    wf.connect(flirt, 'out_file', mean_b0_moco_init_0, 'in_file')

    b0_mask_init_0 = Node(fsl.BET(frac=0.3, mask=True, robust=True), name='b0_mask_init_0')
    wf.connect(mean_b0_moco_init_0, 'out_file', b0_mask_init_0, 'in_file')



    # HEAD MOTION CORRECTION PIPELINE
    hmc = hmc_pipeline()
    wf.connect(selectfiles, 'dMRI_data', hmc, 'inputnode.in_file')
    wf.connect(selectfiles, 'bval_file', hmc, 'inputnode.in_bval')
    wf.connect(selectfiles, 'bvec_file', hmc, 'inputnode.in_bvec')
    wf.connect(b0_mask_init_0, 'mask_file', hmc, 'inputnode.in_mask')
    hmc.inputs.inputnode.ref_num = 0

    wf.connect(hmc, 'outputnode.out_file', ds, 'moco')


    # GET UPDATED MEAN B0 AND MASK
    b0_4d_init_1 = b0_4d_init_0.clone('b0_4d_init_1')
    wf.connect(hmc, 'outputnode.out_file', b0_4d_init_1, 'in_dwi')
    wf.connect(selectfiles, 'bval_file', b0_4d_init_1, 'in_bval')

    mean_b0_moco_init_1 = mean_b0_moco_init_0.clone('mean_b0_moco_init_1')
    wf.connect(b0_4d_init_1, 'out_file', mean_b0_moco_init_1, 'in_file')

    b0_mask_init_1 = b0_mask_init_0.clone('b0_mask_init_1')
    wf.connect(mean_b0_moco_init_1, 'out_file', b0_mask_init_1, 'in_file')


    # EDDY
    ecc = ecc_pipeline()
    wf.connect(selectfiles, 'dMRI_data', ecc, 'inputnode.in_file')
    wf.connect(selectfiles, 'bval_file', ecc, 'inputnode.in_bval')
    wf.connect(b0_mask_init_1, 'mask_file', ecc, 'inputnode.in_mask')
    wf.connect(hmc, 'outputnode.out_xfms', ecc, 'inputnode.in_xfms')

    # GET UPDATED MEAN B0 AND MASK
    b0_4d = b0_4d_init_0.clone('b0_4d')
    wf.connect(ecc, 'outputnode.out_file', b0_4d, 'in_dwi')
    wf.connect(selectfiles, 'bval_file', b0_4d, 'in_bval')

    mean_b0_moco = mean_b0_moco_init_0.clone('mean_b0_moco')
    wf.connect(b0_4d, 'out_file', mean_b0_moco, 'in_file')

    b0_mask= b0_mask_init_0.clone('b0_mask')
    wf.connect(mean_b0_moco, 'out_file', b0_mask, 'in_file')



    # DTIFIT
    dtifit = Node(interface=fsl.DTIFit(), name='dtifit')
    wf.connect(ecc, 'outputnode.out_file', dtifit, 'dwi')
    wf.connect(b0_mask, 'mask_file', dtifit, 'mask')
    wf.connect(hmc, 'outputnode.out_bvec', dtifit, 'bvecs')
    wf.connect(selectfiles, 'bval_file', dtifit, 'bvals')






    ecc.inputs.inputnode.in_mask = 'mask.nii'

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
