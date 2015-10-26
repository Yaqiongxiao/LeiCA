from metrics.utils import calc_variability

__author__ = 'franzliem'


def calc_local_metrics(cfg):
    import os
    from nipype import config
    from nipype.pipeline.engine import Node, Workflow, MapNode
    import nipype.interfaces.utility as util
    import nipype.interfaces.io as nio
    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.freesurfer as freesurfer

    import CPAC.alff.alff as cpac_alff
    import CPAC.reho.reho as cpac_reho
    import CPAC.utils.utils as cpac_utils
    import CPAC.vmhc.vmhc as cpac_vmhc
    import CPAC.registration.registration as cpac_registration
    import CPAC.network_centrality.z_score as cpac_centrality_z_score

    import utils as calc_metrics_utils


    # INPUT PARAMETERS
    dicom_dir = cfg['dicom_dir']
    preprocessed_data_dir = cfg['preprocessed_data_dir']

    working_dir = cfg['working_dir']
    freesurfer_dir = cfg['freesurfer_dir']
    template_dir = cfg['template_dir']
    script_dir = cfg['script_dir']
    ds_dir = cfg['ds_dir']

    subject_id = cfg['subject_id']
    TR_list = cfg['TR_list']

    vols_to_drop = cfg['vols_to_drop']
    rois_list = cfg['rois_list']
    lp_cutoff_freq = cfg['lp_cutoff_freq']
    hp_cutoff_freq = cfg['hp_cutoff_freq']
    use_fs_brainmask = cfg['use_fs_brainmask']

    use_n_procs = cfg['use_n_procs']
    plugin_name = cfg['plugin_name']



    #####################################
    # GENERAL SETTINGS
    #####################################
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
    freesurfer.FSCommand.set_default_subjects_dir(freesurfer_dir)

    wf = Workflow(name='LeiCA_metrics')
    wf.base_dir = os.path.join(working_dir)

    nipype_cfg = dict(logging=dict(workflow_level='DEBUG'), execution={'stop_on_first_crash': True,
                                                                       'remove_unnecessary_outputs': True,
                                                                       'job_finished_timeout': 120})
    config.update_config(nipype_cfg)
    wf.config['execution']['crashdump_dir'] = os.path.join(working_dir, 'crash')

    ds = Node(nio.DataSink(base_directory=ds_dir), name='ds')
    ds.inputs.substitutions = [('_TR_id_', 'TR_')]
    ds.inputs.regexp_substitutions = [('_variabilty_MNIspace_3mm[0-9]*/', ''), ('_z_score[0-9]*/', '')]


    #####################################
    # SET ITERATORS
    #####################################
    # GET SCAN TR_ID ITERATOR
    scan_infosource = Node(util.IdentityInterface(fields=['TR_id']), name='scan_infosource')
    scan_infosource.iterables = ('TR_id', TR_list)



    # get atlas data
    templates_atlases = {  # 'GM_mask_MNI_2mm': 'SPM_GM/SPM_GM_mask_2mm.nii.gz',
                           # 'GM_mask_MNI_3mm': 'SPM_GM/SPM_GM_mask_3mm.nii.gz',
                           'FSL_MNI_3mm_template': 'MNI152_T1_3mm_brain.nii.gz',
                           'vmhc_symm_brain': 'cpac_image_resources/symmetric/MNI152_T1_2mm_brain_symmetric.nii.gz',
                           'vmhc_symm_brain_3mm': 'cpac_image_resources/symmetric/MNI152_T1_3mm_brain_symmetric.nii.gz',
                           'vmhc_symm_skull': 'cpac_image_resources/symmetric/MNI152_T1_2mm_symmetric.nii.gz',
                           'vmhc_symm_brain_mask_dil': 'cpac_image_resources/symmetric/MNI152_T1_2mm_brain_mask_symmetric_dil.nii.gz',
                           'vmhc_config_file_2mm': 'cpac_image_resources/symmetric/T1_2_MNI152_2mm_symmetric.cnf'
                           }

    selectfiles_anat_templates = Node(nio.SelectFiles(templates_atlases,
                                                      base_directory=template_dir),
                                      name="selectfiles_anat_templates")


    # GET SUBJECT SPECIFIC FUNCTIONAL AND STRUCTURAL DATA
    selectfiles_templates = {
        'epi_2_MNI_warp': '{subject_id}/rsfMRI_preprocessing/registration/epi_2_MNI_warp/TR_{TR_id}/*.nii.gz',
        'epi_mask': '{subject_id}/rsfMRI_preprocessing/masks/brain_mask_epiSpace/TR_{TR_id}/*.nii.gz',
        'preproc_epi_full_spectrum': '{subject_id}/rsfMRI_preprocessing/epis/01_denoised/TR_{TR_id}/*.nii.gz',
        'preproc_epi_bp': '{subject_id}/rsfMRI_preprocessing/epis/02_denoised_BP/TR_{TR_id}/*.nii.gz',
        'preproc_epi_bp_tNorm': '{subject_id}/rsfMRI_preprocessing/epis/03_denoised_BP_tNorm/TR_{TR_id}/*.nii.gz',
        'epi_2_struct_mat': '{subject_id}/rsfMRI_preprocessing/registration/epi_2_struct_mat/TR_{TR_id}/*.mat',
        't1w': '{subject_id}/raw_niftis/sMRI/t1w_reoriented.nii.gz',
        't1w_brain': '{subject_id}/rsfMRI_preprocessing/struct_prep/t1w_brain/t1w_reoriented_maths.nii.gz',
    }

    selectfiles = Node(nio.SelectFiles(selectfiles_templates,
                                       base_directory=preprocessed_data_dir),
                       name="selectfiles")
    wf.connect(scan_infosource, 'TR_id', selectfiles, 'TR_id')
    selectfiles.inputs.subject_id = subject_id



    # CREATE TRANSFORMATIONS
    # creat MNI 2 epi warp
    MNI_2_epi_warp = Node(fsl.InvWarp(), name='MNI_2_epi_warp')
    MNI_2_epi_warp.inputs.reference = fsl.Info.standard_image('MNI152_T1_2mm.nii.gz')
    wf.connect(selectfiles, 'epi_mask', MNI_2_epi_warp, 'reference')
    wf.connect(selectfiles, 'epi_2_MNI_warp', MNI_2_epi_warp, 'warp')


    # # CREATE GM MASK IN EPI SPACE
    # GM_mask_epiSpace = Node(fsl.ApplyWarp(), name='GM_mask_epiSpace')
    # GM_mask_epiSpace.inputs.out_file = 'GM_mask_epiSpace.nii.gz'
    #
    # wf.connect(selectfiles_anat_templates, 'GM_mask_MNI_2mm', GM_mask_epiSpace, 'in_file')
    # wf.connect(selectfiles, 'epi_mask', GM_mask_epiSpace, 'ref_file')
    # wf.connect(MNI_2_epi_warp, 'inverse_warp', GM_mask_epiSpace, 'field_file')
    # wf.connect(GM_mask_epiSpace, 'out_file', ds, 'GM_mask_epiSpace')



    # fixme
    # # CREATE TS IN MNI SPACE
    # # is it ok to apply the 2mm warpfield to the 3mm template?
    # # seems ok: https://www.jiscmail.ac.uk/cgi-bin/webadmin?A2=ind0904&L=FSL&P=R14011&1=FSL&9=A&J=on&d=No+Match%3BMatch%3BMatches&z=4
    # epi_bp_MNIspace_3mm = Node(fsl.ApplyWarp(), name='epi_bp_MNIspace_3mm')
    # epi_bp_MNIspace_3mm.inputs.interp = 'spline'
    # epi_bp_MNIspace_3mm.plugin_args = {'submit_specs': 'request_memory = 4000'}
    # wf.connect(selectfiles_anat_templates, 'FSL_MNI_3mm_template', epi_bp_MNIspace_3mm, 'ref_file')
    # wf.connect(selectfiles, 'preproc_epi_bp', epi_bp_MNIspace_3mm, 'in_file')
    # wf.connect(selectfiles, 'epi_2_MNI_warp', epi_bp_MNIspace_3mm, 'field_file')


    # CREATE EPI MASK IN MNI SPACE
    epi_mask_MNIspace_3mm = Node(fsl.ApplyWarp(), name='epi_mask_MNIspace_3mm')
    epi_mask_MNIspace_3mm.inputs.interp = 'nn'
    epi_mask_MNIspace_3mm.plugin_args = {'submit_specs': 'request_memory = 4000'}
    wf.connect(selectfiles_anat_templates, 'FSL_MNI_3mm_template', epi_mask_MNIspace_3mm, 'ref_file')
    wf.connect(selectfiles, 'epi_mask', epi_mask_MNIspace_3mm, 'in_file')
    wf.connect(selectfiles, 'epi_2_MNI_warp', epi_mask_MNIspace_3mm, 'field_file')
    wf.connect(epi_mask_MNIspace_3mm, 'out_file', ds, 'epi_mask_MNIspace_3mm')


    #####################
    # CALCULATE METRICS
    #####################

    # f/ALFF
    alff = cpac_alff.create_alff('alff')
    alff.inputs.hp_input.hp = 0.01
    alff.inputs.lp_input.lp = 0.1
    wf.connect(selectfiles, 'preproc_epi_full_spectrum', alff, 'inputspec.rest_res')
    # wf.connect(GM_mask_epiSpace, 'out_file', alff, 'inputspec.rest_mask')
    wf.connect(selectfiles, 'epi_mask', alff, 'inputspec.rest_mask')
    wf.connect(alff, 'outputspec.alff_img', ds, 'alff.alff')
    wf.connect(alff, 'outputspec.falff_img', ds, 'alff.falff')



    # f/ALFF 2 MNI
    # fixme spline or default?
    alff_MNIspace_3mm = Node(fsl.ApplyWarp(), name='alff_MNIspace_3mm')
    alff_MNIspace_3mm.inputs.interp = 'spline'
    alff_MNIspace_3mm.plugin_args = {'submit_specs': 'request_memory = 4000'}
    wf.connect(selectfiles_anat_templates, 'FSL_MNI_3mm_template', alff_MNIspace_3mm, 'ref_file')
    wf.connect(alff, 'outputspec.alff_img', alff_MNIspace_3mm, 'in_file')
    wf.connect(selectfiles, 'epi_2_MNI_warp', alff_MNIspace_3mm, 'field_file')
    wf.connect(alff_MNIspace_3mm, 'out_file', ds, 'alff.alff_MNI_3mm')

    falff_MNIspace_3mm = Node(fsl.ApplyWarp(), name='falff_MNIspace_3mm')
    falff_MNIspace_3mm.inputs.interp = 'spline'
    falff_MNIspace_3mm.plugin_args = {'submit_specs': 'request_memory = 4000'}
    wf.connect(selectfiles_anat_templates, 'FSL_MNI_3mm_template', falff_MNIspace_3mm, 'ref_file')
    wf.connect(alff, 'outputspec.falff_img', falff_MNIspace_3mm, 'in_file')
    wf.connect(selectfiles, 'epi_2_MNI_warp', falff_MNIspace_3mm, 'field_file')
    wf.connect(falff_MNIspace_3mm, 'out_file', ds, 'alff.falff_MNI_3mm')



    # f/ALFF_MNI Z-SCORE
    alff_MNIspace_3mm_Z = cpac_utils.get_zscore(input_name='alff_MNIspace_3mm', wf_name='alff_MNIspace_3mm_Z')
    wf.connect(alff_MNIspace_3mm, 'out_file', alff_MNIspace_3mm_Z, 'inputspec.input_file')
    # wf.connect(selectfiles_anat_templates, 'GM_mask_MNI_3mm', alff_MNIspace_3mm_Z, 'inputspec.mask_file')
    wf.connect(epi_mask_MNIspace_3mm, 'out_file', alff_MNIspace_3mm_Z, 'inputspec.mask_file')
    wf.connect(alff_MNIspace_3mm_Z, 'outputspec.z_score_img', ds, 'alff.alff_MNI_3mm_Z')

    falff_MNIspace_3mm_Z = cpac_utils.get_zscore(input_name='falff_MNIspace_3mm', wf_name='falff_MNIspace_3mm_Z')
    wf.connect(falff_MNIspace_3mm, 'out_file', falff_MNIspace_3mm_Z, 'inputspec.input_file')
    # wf.connect(selectfiles_anat_templates, 'GM_mask_MNI_3mm', falff_MNIspace_3mm_Z, 'inputspec.mask_file')
    wf.connect(epi_mask_MNIspace_3mm, 'out_file', falff_MNIspace_3mm_Z, 'inputspec.mask_file')
    wf.connect(falff_MNIspace_3mm_Z, 'outputspec.z_score_img', ds, 'alff.falff_MNI_3mm_Z')


    # f/ALFF_MNI STANDARDIZE BY MEAN
    alff_MNIspace_3mm_standardized_mean = calc_metrics_utils.standardize_divide_by_mean(
        wf_name='alff_MNIspace_3mm_standardized_mean')
    wf.connect(alff_MNIspace_3mm, 'out_file', alff_MNIspace_3mm_standardized_mean, 'inputnode.in_file')
    wf.connect(epi_mask_MNIspace_3mm, 'out_file', alff_MNIspace_3mm_standardized_mean, 'inputnode.mask_file')
    wf.connect(alff_MNIspace_3mm_standardized_mean, 'outputnode.out_file', ds, 'alff.alff_MNI_3mm_standardized_mean')

    falff_MNIspace_3mm_standardized_mean = calc_metrics_utils.standardize_divide_by_mean(
        wf_name='falff_MNIspace_3mm_standardized_mean')
    wf.connect(falff_MNIspace_3mm, 'out_file', falff_MNIspace_3mm_standardized_mean, 'inputnode.in_file')
    wf.connect(epi_mask_MNIspace_3mm, 'out_file', falff_MNIspace_3mm_standardized_mean, 'inputnode.mask_file')
    wf.connect(falff_MNIspace_3mm_standardized_mean, 'outputnode.out_file', ds, 'alff.falff_MNI_3mm_standardized_mean')





    # REHO
    reho = cpac_reho.create_reho()
    reho.inputs.inputspec.cluster_size = 27
    wf.connect(selectfiles, 'preproc_epi_bp', reho, 'inputspec.rest_res_filt')
    # wf.connect(GM_mask_epiSpace, 'out_file', reho, 'inputspec.rest_mask')
    wf.connect(selectfiles, 'epi_mask', reho, 'inputspec.rest_mask')
    wf.connect(reho, 'outputspec.raw_reho_map', ds, 'reho.reho')



    # REHO 2 MNI
    # fixme spline or default?
    reho_MNIspace_3mm = Node(fsl.ApplyWarp(), name='reho_MNIspace_3mm')
    reho_MNIspace_3mm.inputs.interp = 'spline'
    reho_MNIspace_3mm.plugin_args = {'submit_specs': 'request_memory = 4000'}
    wf.connect(selectfiles_anat_templates, 'FSL_MNI_3mm_template', reho_MNIspace_3mm, 'ref_file')
    wf.connect(reho, 'outputspec.raw_reho_map', reho_MNIspace_3mm, 'in_file')
    wf.connect(selectfiles, 'epi_2_MNI_warp', reho_MNIspace_3mm, 'field_file')
    wf.connect(reho_MNIspace_3mm, 'out_file', ds, 'reho.reho_MNI_3mm')



    # REHO_MNI Z-SCORE
    reho_MNIspace_3mm_Z = cpac_utils.get_zscore(input_name='reho_MNIspace_3mm', wf_name='reho_MNIspace_3mm_Z')
    wf.connect(alff_MNIspace_3mm, 'out_file', reho_MNIspace_3mm_Z, 'inputspec.input_file')
    # wf.connect(selectfiles_anat_templates, 'GM_mask_MNI_3mm', reho_MNIspace_3mm_Z, 'inputspec.mask_file')
    wf.connect(epi_mask_MNIspace_3mm, 'out_file', reho_MNIspace_3mm_Z, 'inputspec.mask_file')
    wf.connect(reho_MNIspace_3mm_Z, 'outputspec.z_score_img', ds, 'reho.reho_MNI_3mm_Z')



    # REHO_MNI STANDARDIZE BY MEAN
    reho_MNIspace_3mm_standardized_mean = calc_metrics_utils.standardize_divide_by_mean(
        wf_name='reho_MNIspace_3mm_standardized_mean')
    wf.connect(reho_MNIspace_3mm, 'out_file', reho_MNIspace_3mm_standardized_mean, 'inputnode.in_file')
    wf.connect(epi_mask_MNIspace_3mm, 'out_file', reho_MNIspace_3mm_standardized_mean, 'inputnode.mask_file')
    wf.connect(reho_MNIspace_3mm_standardized_mean, 'outputnode.out_file', ds, 'reho.reho_MNI_3mm_standardized_mean')



    # VMHC
    # create registration to symmetrical MNI template
    struct_2_MNI_symm = cpac_registration.create_nonlinear_register(name='struct_2_MNI_symm')
    wf.connect(selectfiles_anat_templates, 'vmhc_config_file_2mm', struct_2_MNI_symm, 'inputspec.fnirt_config')
    wf.connect(selectfiles_anat_templates, 'vmhc_symm_brain', struct_2_MNI_symm, 'inputspec.reference_brain')
    wf.connect(selectfiles_anat_templates, 'vmhc_symm_skull', struct_2_MNI_symm, 'inputspec.reference_skull')
    wf.connect(selectfiles_anat_templates, 'vmhc_symm_brain_mask_dil', struct_2_MNI_symm, 'inputspec.ref_mask')
    wf.connect(selectfiles, 't1w', struct_2_MNI_symm, 'inputspec.input_skull')
    wf.connect(selectfiles, 't1w_brain', struct_2_MNI_symm, 'inputspec.input_brain')

    wf.connect(struct_2_MNI_symm, 'outputspec.output_brain', ds, 'vmhc.symm_reg.@output_brain')
    wf.connect(struct_2_MNI_symm, 'outputspec.linear_xfm', ds, 'vmhc.symm_reg.@linear_xfm')
    wf.connect(struct_2_MNI_symm, 'outputspec.invlinear_xfm', ds, 'vmhc.symm_reg.@invlinear_xfm')
    wf.connect(struct_2_MNI_symm, 'outputspec.nonlinear_xfm', ds, 'vmhc.symm_reg.@nonlinear_xfm')



    # fixme
    vmhc = cpac_vmhc.create_vmhc(use_ants=False, name='vmhc')
    vmhc.inputs.fwhm_input.fwhm = 4
    wf.connect(selectfiles_anat_templates, 'vmhc_symm_brain_3mm', vmhc, 'inputspec.standard_for_func')
    wf.connect(selectfiles, 'preproc_epi_bp_tNorm', vmhc, 'inputspec.rest_res')
    wf.connect(selectfiles, 'epi_2_struct_mat', vmhc, 'inputspec.example_func2highres_mat')
    wf.connect(struct_2_MNI_symm, 'outputspec.nonlinear_xfm', vmhc, 'inputspec.fnirt_nonlinear_warp')
    # wf.connect(GM_mask_epiSpace, 'out_file', vmhc, 'inputspec.rest_mask')
    wf.connect(selectfiles, 'epi_mask', vmhc, 'inputspec.rest_mask')

    wf.connect(vmhc, 'outputspec.rest_res_2symmstandard', ds, 'vmhc.rest_res_2symmstandard')
    wf.connect(vmhc, 'outputspec.VMHC_FWHM_img', ds, 'vmhc.VMHC_FWHM_img')
    wf.connect(vmhc, 'outputspec.VMHC_Z_FWHM_img', ds, 'vmhc.VMHC_Z_FWHM_img')
    wf.connect(vmhc, 'outputspec.VMHC_Z_stat_FWHM_img', ds, 'vmhc.VMHC_Z_stat_FWHM_img')



    # VARIABILITY SCORES
    variability = Node(util.Function(input_names=['in_file'],
                                     output_names=['out_file_list'],
                                     function=calc_metrics_utils.calc_variability),
                       name='variability')
    wf.connect(selectfiles, 'preproc_epi_bp', variability, 'in_file')
    wf.connect(variability, 'out_file_list', ds, 'variability.subjectSpace.@out_files')


    # #fixme spline?
    variabilty_MNIspace_3mm = MapNode(fsl.ApplyWarp(), iterfield=['in_file'], name='variabilty_MNIspace_3mm')
    variabilty_MNIspace_3mm.inputs.interp = 'spline'
    variabilty_MNIspace_3mm.plugin_args = {'submit_specs': 'request_memory = 4000'}
    wf.connect(selectfiles_anat_templates, 'FSL_MNI_3mm_template', variabilty_MNIspace_3mm, 'ref_file')
    wf.connect(selectfiles, 'epi_2_MNI_warp', variabilty_MNIspace_3mm, 'field_file')
    wf.connect(variability, 'out_file_list', variabilty_MNIspace_3mm, 'in_file')
    wf.connect(variabilty_MNIspace_3mm, 'out_file', ds, 'variability.MNI_3mm.@out_file')


    # CALC Z SCORE
    variabilty_MNIspace_3mm_Z = cpac_centrality_z_score.get_cent_zscore(wf_name='variabilty_MNIspace_3mm_Z')
    wf.connect(variabilty_MNIspace_3mm, 'out_file', variabilty_MNIspace_3mm_Z, 'inputspec.input_file')
    # wf.connect(selectfiles_anat_templates, 'GM_mask_MNI_3mm', variabilty_MNIspace_3mm_Z, 'inputspec.mask_file')
    wf.connect(epi_mask_MNIspace_3mm, 'out_file', variabilty_MNIspace_3mm_Z, 'inputspec.mask_file')
    wf.connect(variabilty_MNIspace_3mm_Z, 'outputspec.z_score_img', ds, 'variability.MNI_3mm_Z.@out_file')



    # STANDARDIZE BY MEAN
    variabilty_MNIspace_3mm_standardized_mean = calc_metrics_utils.standardize_divide_by_mean(
        wf_name='variabilty_MNIspace_3mm_standardized_mean')
    wf.connect(variabilty_MNIspace_3mm, 'out_file', variabilty_MNIspace_3mm_standardized_mean, 'inputnode.in_file')
    wf.connect(epi_mask_MNIspace_3mm, 'out_file', variabilty_MNIspace_3mm_standardized_mean, 'inputnode.mask_file')
    wf.connect(variabilty_MNIspace_3mm_standardized_mean, 'outputnode.out_file', ds,
               'variability.MNI_3mm_standardized_mean.@out_file')

    wf.write_graph(dotfilename=wf.name, graph2use='colored', format='pdf')  # 'hierarchical')
    wf.write_graph(dotfilename=wf.name, graph2use='orig', format='pdf')
    wf.write_graph(dotfilename=wf.name, graph2use='flat', format='pdf')

    if plugin_name == 'CondorDAGMan':
        wf.run(plugin=plugin_name)
    if plugin_name == 'MultiProc':
        wf.run(plugin=plugin_name, plugin_args={'n_procs': use_n_procs})


def calc_centrality_metrics(cfg):
    import os
    from nipype import config
    from nipype.pipeline.engine import Node, Workflow
    import nipype.interfaces.utility as util
    import nipype.interfaces.io as nio
    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.freesurfer as freesurfer

    import CPAC.network_centrality.resting_state_centrality as cpac_centrality
    import CPAC.network_centrality.z_score as cpac_centrality_z_score


    # INPUT PARAMETERS
    dicom_dir = cfg['dicom_dir']
    preprocessed_data_dir = cfg['preprocessed_data_dir']

    working_dir = cfg['working_dir']
    freesurfer_dir = cfg['freesurfer_dir']
    template_dir = cfg['template_dir']
    script_dir = cfg['script_dir']
    ds_dir = cfg['ds_dir']

    subjects_list = cfg['subjects_list']
    TR_list = cfg['TR_list']

    use_n_procs = cfg['use_n_procs']
    plugin_name = cfg['plugin_name']



    #####################################
    # GENERAL SETTINGS
    #####################################
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
    freesurfer.FSCommand.set_default_subjects_dir(freesurfer_dir)

    wf = Workflow(name='LeiCA_metrics')
    wf.base_dir = os.path.join(working_dir)

    nipype_cfg = dict(logging=dict(workflow_level='DEBUG'), execution={'stop_on_first_crash': False,
                                                                       'remove_unnecessary_outputs': True,
                                                                       'job_finished_timeout': 120})
    config.update_config(nipype_cfg)
    wf.config['execution']['crashdump_dir'] = os.path.join(working_dir, 'crash')

    ds = Node(nio.DataSink(), name='ds')
    ds.inputs.substitutions = [('_TR_id_', 'TR_')]
    ds.inputs.regexp_substitutions = [('_subject_id_[A0-9]*/', ''), (
    '_z_score[0-9]*/', '')]  # , #('dc/_TR_id_[0-9]*/', ''), ('evc/_TR_id_[0-9]*/','')]

    #####################################
    # SET ITERATORS
    #####################################
    # GET SCAN TR_ID ITERATOR
    scan_infosource = Node(util.IdentityInterface(fields=['TR_id']), name='scan_infosource')
    scan_infosource.iterables = ('TR_id', TR_list)

    subjects_infosource = Node(util.IdentityInterface(fields=['subject_id']), name='subjects_infosource')
    subjects_infosource.iterables = ('subject_id', subjects_list)

    def add_subject_id_to_ds_dir_fct(subject_id, ds_path):
        import os
        out_path = os.path.join(ds_path, subject_id)
        return out_path

    add_subject_id_to_ds_dir = Node(util.Function(input_names=['subject_id', 'ds_path'],
                                                  output_names=['out_path'],
                                                  function=add_subject_id_to_ds_dir_fct),
                                    name='add_subject_id_to_ds_dir')
    wf.connect(subjects_infosource, 'subject_id', add_subject_id_to_ds_dir, 'subject_id')
    add_subject_id_to_ds_dir.inputs.ds_path = ds_dir

    wf.connect(add_subject_id_to_ds_dir, 'out_path', ds, 'base_directory')


    # get atlas data
    templates_atlases = {'GM_mask_MNI_2mm': 'SPM_GM/SPM_GM_mask_2mm.nii.gz',
                         'GM_mask_MNI_3mm': 'SPM_GM/SPM_GM_mask_3mm.nii.gz',
                         'FSL_MNI_3mm_template': 'MNI152_T1_3mm_brain.nii.gz',
                         'vmhc_symm_brain': 'cpac_image_resources/symmetric/MNI152_T1_2mm_brain_symmetric.nii.gz',
                         'vmhc_symm_brain_3mm': 'cpac_image_resources/symmetric/MNI152_T1_3mm_brain_symmetric.nii.gz',
                         'vmhc_symm_skull': 'cpac_image_resources/symmetric/MNI152_T1_2mm_symmetric.nii.gz',
                         'vmhc_symm_brain_mask_dil': 'cpac_image_resources/symmetric/MNI152_T1_2mm_brain_mask_symmetric_dil.nii.gz',
                         'vmhc_config_file_2mm': 'cpac_image_resources/symmetric/T1_2_MNI152_2mm_symmetric.cnf'
                         }

    selectfiles_anat_templates = Node(nio.SelectFiles(templates_atlases,
                                                      base_directory=template_dir),
                                      name="selectfiles_anat_templates")


    # GET SUBJECT SPECIFIC FUNCTIONAL AND STRUCTURAL DATA
    selectfiles_templates = {
        'epi_2_MNI_warp': '{subject_id}/rsfMRI_preprocessing/registration/epi_2_MNI_warp/TR_{TR_id}/*.nii.gz',
        'epi_mask': '{subject_id}/rsfMRI_preprocessing/masks/brain_mask_epiSpace/TR_{TR_id}/*.nii.gz',
        'preproc_epi_full_spectrum': '{subject_id}/rsfMRI_preprocessing/epis/01_denoised/TR_{TR_id}/*.nii.gz',
        'preproc_epi_bp': '{subject_id}/rsfMRI_preprocessing/epis/02_denoised_BP/TR_{TR_id}/*.nii.gz',
        'preproc_epi_bp_tNorm': '{subject_id}/rsfMRI_preprocessing/epis/03_denoised_BP_tNorm/TR_{TR_id}/*.nii.gz',
        'epi_2_struct_mat': '{subject_id}/rsfMRI_preprocessing/registration/epi_2_struct_mat/TR_{TR_id}/*.mat',
        't1w': '{subject_id}/raw_niftis/sMRI/t1w_reoriented.nii.gz',
        't1w_brain': '{subject_id}/rsfMRI_preprocessing/struct_prep/t1w_brain/t1w_reoriented_maths.nii.gz',
        'epi_bp_tNorm_MNIspace_3mm': '{subject_id}/rsfMRI_preprocessing/epis_MNI_3mm/03_denoised_BP_tNorm/TR_645/residual_filt_norm_warp.nii.gz'
    }

    selectfiles = Node(nio.SelectFiles(selectfiles_templates,
                                       base_directory=preprocessed_data_dir),
                       name="selectfiles")
    wf.connect(scan_infosource, 'TR_id', selectfiles, 'TR_id')
    wf.connect(subjects_infosource, 'subject_id', selectfiles, 'subject_id')
    # selectfiles.inputs.subject_id = subject_id

    # CREATE TRANSFORMATIONS
    # creat MNI 2 epi warp
    MNI_2_epi_warp = Node(fsl.InvWarp(), name='MNI_2_epi_warp')
    MNI_2_epi_warp.inputs.reference = fsl.Info.standard_image('MNI152_T1_2mm.nii.gz')
    wf.connect(selectfiles, 'epi_mask', MNI_2_epi_warp, 'reference')
    wf.connect(selectfiles, 'epi_2_MNI_warp', MNI_2_epi_warp, 'warp')

    #####################
    # CALCULATE METRICS
    #####################

    # DEGREE
    # fixme
    # a_mem = 5
    # fixme
    a_mem = 20
    dc = cpac_centrality.create_resting_state_graphs(allocated_memory=a_mem,
                                                     wf_name='dc')  # allocated_memory = a_mem, wf_name = 'dc')
    # dc.plugin_args = {'submit_specs': 'request_memory = 6000'}
    # fixme
    dc.plugin_args = {'submit_specs': 'request_memory = 20000'}

    dc.inputs.inputspec.method_option = 0  # 0 for degree centrality, 1 for eigenvector centrality, 2 for lFCD
    dc.inputs.inputspec.threshold_option = 0  # 0 for probability p_value, 1 for sparsity threshold, any other for threshold value
    dc.inputs.inputspec.threshold = 0.0001
    dc.inputs.inputspec.weight_options = [True,
                                          True]  # list of two booleans for binarize and weighted options respectively
    wf.connect(selectfiles, 'epi_bp_tNorm_MNIspace_3mm', dc, 'inputspec.subject')
    wf.connect(selectfiles_anat_templates, 'GM_mask_MNI_3mm', dc, 'inputspec.template')
    wf.connect(dc, 'outputspec.centrality_outputs', ds, 'metrics.centrality.dc.@centrality_outputs')
    wf.connect(dc, 'outputspec.correlation_matrix', ds, 'metrics.centrality.dc.@correlation_matrix')
    wf.connect(dc, 'outputspec.graph_outputs', ds, 'metrics.centrality.dc.@graph_outputs')

    # DC Z-SCORE
    dc_Z = cpac_centrality_z_score.get_cent_zscore(wf_name='dc_Z')
    wf.connect(dc, 'outputspec.centrality_outputs', dc_Z, 'inputspec.input_file')
    wf.connect(selectfiles_anat_templates, 'GM_mask_MNI_3mm', dc_Z, 'inputspec.mask_file')
    wf.connect(dc_Z, 'outputspec.z_score_img', ds, 'metrics.centrality.dc_z.@output')

    a_mem = 20
    evc = cpac_centrality.create_resting_state_graphs(allocated_memory=a_mem, wf_name='evc')
    evc.plugin_args = {'submit_specs': 'request_memory = 20000'}

    evc.inputs.inputspec.method_option = 1  # 0 for degree centrality, 1 for eigenvector centrality, 2 for lFCD
    evc.inputs.inputspec.threshold_option = 0  # 0 for probability p_value, 1 for sparsity threshold, any other for threshold value
    evc.inputs.inputspec.threshold = 0.0001
    evc.inputs.inputspec.weight_options = [True,
                                           True]  # list of two booleans for binarize and weighted options respectively
    wf.connect(selectfiles, 'epi_bp_tNorm_MNIspace_3mm', evc, 'inputspec.subject')
    wf.connect(selectfiles_anat_templates, 'GM_mask_MNI_3mm', evc, 'inputspec.template')
    wf.connect(evc, 'outputspec.centrality_outputs', ds, 'metrics.centrality.evc.@centrality_outputs')
    wf.connect(evc, 'outputspec.correlation_matrix', ds, 'metrics.centrality.evc.@correlation_matrix')
    wf.connect(evc, 'outputspec.graph_outputs', ds, 'metrics.centrality.evc.@graph_outputs')

    # EVC Z-SCORE
    evc_Z = cpac_centrality_z_score.get_cent_zscore(wf_name='evc_Z')
    wf.connect(evc, 'outputspec.centrality_outputs', evc_Z, 'inputspec.input_file')
    wf.connect(selectfiles_anat_templates, 'GM_mask_MNI_3mm', evc_Z, 'inputspec.mask_file')
    wf.connect(evc_Z, 'outputspec.z_score_img', ds, 'metrics.centrality.evc_z.@output')

    wf.write_graph(dotfilename=wf.name, graph2use='colored', format='pdf')  # 'hierarchical')
    wf.write_graph(dotfilename=wf.name, graph2use='orig', format='pdf')
    wf.write_graph(dotfilename=wf.name, graph2use='flat', format='pdf')

    if plugin_name == 'CondorDAGMan':
        wf.run(plugin=plugin_name)
    if plugin_name == 'MultiProc':
        wf.run(plugin=plugin_name, plugin_args={'n_procs': use_n_procs})
