def apply_all_corrections(name='UnwarpArtifacts'):
    """
    Combines two lists of linear transforms with the deformation field
    map obtained typically after the SDC process.
    Additionally, computes the corresponding bspline coefficients and
    the map of determinants of the jacobian.
    """

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['in_sdc', 'in_hmc', 'in_ecc', 'in_dwi']), name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_file', 'out_warp', 'out_coeff', 'out_jacobian']),
        name='outputnode')
    warps = pe.MapNode(fsl.ConvertWarp(relwarp=True),
                       iterfield=['premat', 'postmat'],
                       name='ConvertWarp')

    selref = pe.Node(niu.Select(index=[0]), name='Reference')

    split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
    unwarp = pe.MapNode(fsl.ApplyWarp(), iterfield=['in_file', 'field_file'],
                        name='UnwarpDWIs')

    coeffs = pe.MapNode(fsl.WarpUtils(out_format='spline'),
                        iterfield=['in_file'], name='CoeffComp')
    jacobian = pe.MapNode(fsl.WarpUtils(write_jacobian=True),
                          iterfield=['in_file'], name='JacobianComp')
    jacmult = pe.MapNode(fsl.MultiImageMaths(op_string='-mul %s'),
                         iterfield=['in_file', 'operand_files'],
                         name='ModulateDWIs')

    thres = pe.MapNode(fsl.Threshold(thresh=0.0), iterfield=['in_file'],
                       name='RemoveNegative')
    merge = pe.Node(fsl.Merge(dimension='t'), name='MergeDWIs')

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode,   warps,      [('in_sdc', 'warp1'),
                                   ('in_hmc', 'premat'),
                                   ('in_ecc', 'postmat'),
                                   ('in_dwi', 'reference')]),
        (inputnode,   split,      [('in_dwi', 'in_file')]),
        (split,       selref,     [('out_files', 'inlist')]),
        (warps,       unwarp,     [('out_file', 'field_file')]),
        (split,       unwarp,     [('out_files', 'in_file')]),
        (selref,      unwarp,     [('out', 'ref_file')]),
        (selref,      coeffs,     [('out', 'reference')]),
        (warps,       coeffs,     [('out_file', 'in_file')]),
        (selref,      jacobian,   [('out', 'reference')]),
        (coeffs,      jacobian,   [('out_file', 'in_file')]),
        (unwarp,      jacmult,    [('out_file', 'in_file')]),
        (jacobian,    jacmult,    [('out_jacobian', 'operand_files')]),
        (jacmult,     thres,      [('out_file', 'in_file')]),
        (thres,       merge,      [('out_file', 'in_files')]),
        (warps,       outputnode, [('out_file', 'out_warp')]),
        (coeffs,      outputnode, [('out_file', 'out_coeff')]),
        (jacobian,    outputnode, [('out_jacobian', 'out_jacobian')]),
        (merge,       outputnode, [('merged_file', 'out_file')])
    ])
    return wf
