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
    from nipype.interfaces import fsl, dipy

    from LeiCA.dMRI.nipype_11_workflows_dmri_fsl_snapshot.artifacts import hmc_pipeline, ecc_pipeline
    from LeiCA.dMRI.nipype_11_workflows_dmri_fsl_snapshot.utils import b0_average, extract_bval
    from LeiCA.dMRI.nipype_11_workflows_dmri_fsl_snapshot.tbss import create_tbss_all
    from nipype.workflows.dmri.dipy.denoise import nlmeans_pipeline
    from diffusion_utils import apply_hmc_and_ecc

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


    def _bvals_with_nodiff_0_fct(in_bval, lowbval):
        ''' returns bval file with 0 in place of lowbvals
        '''
        import os
        import numpy as np
        bvals = np.loadtxt(in_bval)
        bvals[bvals <= lowbval] = 0
        bval_file_zero = os.path.abspath('bval_0.bval')
        np.savetxt(bval_file_zero, bvals)
        return bval_file_zero

    # CREATE BVALS FILES WITH 0 IN LOWBVAL SLICES. FOR ECC ONLY
    bvals_with_nodiff_0 = Node(util.Function(input_names=['in_bval', 'lowbval'],
                                             output_names=['bval_file_zero'],
                                             function=_bvals_with_nodiff_0_fct), name='bvals_with_nodiff_0')
    wf.connect(selectfiles, 'bval_file', bvals_with_nodiff_0, 'in_bval')
    bvals_with_nodiff_0.inputs.lowbval = 5

    ##
    # GET B0 MASK
    b0_4d_init_0 = Node(util.Function(input_names=['in_dwi', 'in_bval', 'b'], output_names=['out_file'],
                                      function=extract_bval), name='b0_4d_init_0')
    wf.connect(selectfiles, 'dMRI_data', b0_4d_init_0, 'in_dwi')
    #wf.connect(selectfiles, 'bval_file', b0_4d_init_0, 'in_bval')
    wf.connect(bvals_with_nodiff_0, 'bval_file_zero', b0_4d_init_0, 'in_bval')
    b0_4d_init_0.inputs.b = 'nodiff'

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
    #wf.connect(selectfiles, 'bval_file', hmc, 'inputnode.in_bval')
    wf.connect(bvals_with_nodiff_0, 'bval_file_zero', hmc, 'inputnode.in_bval')
    wf.connect(selectfiles, 'bvec_file', hmc, 'inputnode.in_bvec')
    wf.connect(b0_mask_init_0, 'mask_file', hmc, 'inputnode.in_mask')
    hmc.inputs.inputnode.ref_num = 0

    wf.connect(hmc, 'outputnode.out_file', ds, 'moco')


    # GET UPDATED MEAN B0 AND MASK
    b0_4d_init_1 = b0_4d_init_0.clone('b0_4d_init_1')
    wf.connect(hmc, 'outputnode.out_file', b0_4d_init_1, 'in_dwi')
    #wf.connect(selectfiles, 'bval_file', b0_4d_init_1, 'in_bval')
    wf.connect(bvals_with_nodiff_0, 'bval_file_zero', b0_4d_init_1, 'in_bval')

    mean_b0_moco_init_1 = mean_b0_moco_init_0.clone('mean_b0_moco_init_1')
    wf.connect(b0_4d_init_1, 'out_file', mean_b0_moco_init_1, 'in_file')

    b0_mask_init_1 = b0_mask_init_0.clone('b0_mask_init_1')
    wf.connect(mean_b0_moco_init_1, 'out_file', b0_mask_init_1, 'in_file')


    # EDDY
    ecc = ecc_pipeline()
    wf.connect(selectfiles, 'dMRI_data', ecc, 'inputnode.in_file')
    #wf.connect(selectfiles, 'bval_file', ecc, 'inputnode.in_bval')
    wf.connect(bvals_with_nodiff_0, 'bval_file_zero', ecc, 'inputnode.in_bval')
    wf.connect(b0_mask_init_1, 'mask_file', ecc, 'inputnode.in_mask')
    wf.connect(hmc, 'outputnode.out_xfms', ecc, 'inputnode.in_xfms')

    wf.connect(ecc, 'outputnode.out_file', ds, 'ecc')


    combine_corrections = apply_hmc_and_ecc(name='combine_corrections')
    wf.connect(hmc, 'outputnode.out_xfms', combine_corrections, 'inputnode.in_hmc')
    wf.connect(ecc, 'outputnode.out_xfms', combine_corrections, 'inputnode.in_ecc')
    wf.connect(selectfiles, 'dMRI_data', combine_corrections, 'inputnode.in_dwi')

    wf.connect(combine_corrections, 'outputnode.out_file', ds, 'preprocessed')

    # GET UPDATED MEAN B0 AND MASK
    b0_4d = b0_4d_init_0.clone('b0_4d')
    wf.connect(combine_corrections, 'outputnode.out_file', b0_4d, 'in_dwi')
    #wf.connect(selectfiles, 'bval_file', b0_4d, 'in_bval')
    wf.connect(bvals_with_nodiff_0, 'bval_file_zero', b0_4d, 'in_bval')

    mean_b0_moco = mean_b0_moco_init_0.clone('mean_b0_moco')
    wf.connect(b0_4d, 'out_file', mean_b0_moco, 'in_file')

    b0_mask = b0_mask_init_0.clone('b0_mask')
    wf.connect(mean_b0_moco, 'out_file', b0_mask, 'in_file')

    # denoise = Node(dipy.Denoise(), name='denoise')
    # wf.connect(combine_corrections, 'outputnode.out_file', denoise, 'in_file')
    # wf.connect(b0_mask, 'mask_file', denoise, 'in_mask')
    # wf.connect(denoise, 'out_file', ds, 'denoised')

    # check if ok fixme
    denoise = nlmeans_pipeline()
    wf.connect(combine_corrections, 'outputnode.out_file', denoise, 'inputnode.in_file')
    wf.connect(b0_mask, 'mask_file', denoise, 'inputnode.in_mask')
    wf.connect(denoise, 'outputnode.out_file', ds, 'denoised')


    # DTIFIT
    dtifit = Node(interface=fsl.DTIFit(), name='dtifit')
    wf.connect(combine_corrections, 'outputnode.out_file', dtifit, 'dwi')
    wf.connect(b0_mask, 'mask_file', dtifit, 'mask')
    wf.connect(hmc, 'outputnode.out_bvec', dtifit, 'bvecs')
    wf.connect(selectfiles, 'bval_file', dtifit, 'bvals')

    wf.connect(dtifit, 'FA', ds, 'dtifit.@FA')
    wf.connect(dtifit, 'L1', ds, 'dtifit.@L1')
    wf.connect(dtifit, 'L2', ds, 'dtifit.@L2')
    wf.connect(dtifit, 'L3', ds, 'dtifit.@L3')
    wf.connect(dtifit, 'MD', ds, 'dtifit.@MD')
    wf.connect(dtifit, 'MO', ds, 'dtifit.@MO')
    wf.connect(dtifit, 'S0', ds, 'dtifit.@S0')
    wf.connect(dtifit, 'V1', ds, 'dtifit.@V1')
    wf.connect(dtifit, 'V2', ds, 'dtifit.@V2')
    wf.connect(dtifit, 'V3', ds, 'dtifit.@V3')
    wf.connect(dtifit, 'tensor', ds, 'dtifit.@tensor')

    RD_sum = Node(fsl.ImageMaths(op_string='-add '), name='RD_sum')
    wf.connect(dtifit, 'L2', RD_sum, 'in_file')
    wf.connect(dtifit, 'L3', RD_sum, 'in_file2')

    RD = Node(fsl.ImageMaths(op_string='-div 2', out_file='RD.nii.gz'), name='RD')
    wf.connect(RD_sum, 'out_file', RD, 'in_file')
    wf.connect(RD, 'out_file', ds, 'dtifit.@RD')

    simple_ecc = Node(fsl.EddyCorrect(), name='simple_ecc')
    wf.connect(selectfiles, 'dMRI_data', simple_ecc, 'in_file')
    wf.connect(simple_ecc, 'eddy_corrected', ds, 'simple_ecc')


    # DTIFIT DENOISED
    dtifit_denoised = Node(interface=fsl.DTIFit(), name='dtifit_denoised')
    wf.connect(denoise, 'outputnode.out_file', dtifit_denoised, 'dwi')
    wf.connect(b0_mask, 'mask_file', dtifit_denoised, 'mask')
    wf.connect(hmc, 'outputnode.out_bvec', dtifit_denoised, 'bvecs')
    wf.connect(selectfiles, 'bval_file', dtifit_denoised, 'bvals')

    wf.connect(dtifit_denoised, 'FA', ds, 'dtifit_denoised.@FA')
    wf.connect(dtifit_denoised, 'L1', ds, 'dtifit_denoised.@L1')
    wf.connect(dtifit_denoised, 'L2', ds, 'dtifit_denoised.@L2')
    wf.connect(dtifit_denoised, 'L3', ds, 'dtifit_denoised.@L3')
    wf.connect(dtifit_denoised, 'MD', ds, 'dtifit_denoised.@MD')
    wf.connect(dtifit_denoised, 'MO', ds, 'dtifit_denoised.@MO')
    wf.connect(dtifit_denoised, 'S0', ds, 'dtifit_denoised.@S0')
    wf.connect(dtifit_denoised, 'V1', ds, 'dtifit_denoised.@V1')
    wf.connect(dtifit_denoised, 'V2', ds, 'dtifit_denoised.@V2')
    wf.connect(dtifit_denoised, 'V3', ds, 'dtifit_denoised.@V3')



    #
    def _file_to_list(in_file):
        if type(in_file) is not list:
            return [in_file]
        else:
            return in_file

    in_file_to_list = Node(util.Function(input_names=['in_file'], output_names=['out_file'], function=_file_to_list), name='in_file_to_list')
    wf.connect(dtifit, 'FA', in_file_to_list, 'in_file')

    # TBSS
    tbss = create_tbss_all(estimate_skeleton=False)
    tbss.inputs.inputnode.skeleton_thresh = 0.2
    wf.connect(in_file_to_list, 'out_file', tbss, 'inputnode.fa_list')

    wf.connect(tbss, 'outputall_node.mergefa_file3', ds, 'tbss.@mergefa')
    wf.connect(tbss, 'outputnode.projectedfa_file', ds, 'tbss.@projectedfa_file')
    wf.connect(tbss, 'outputnode.skeleton_file4', ds, 'tbss.@skeleton_file')
    wf.connect(tbss, 'outputnode.skeleton_mask', ds, 'tbss.@skeleton_mask')
    # outputnode.meanfa_file
    # outputnode.projectedfa_file
    # outputnode.skeleton_file
    # outputnode.skeleton_mask

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
