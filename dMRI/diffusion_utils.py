from __future__ import division
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import fsl


def apply_hmc_and_ecc(name='apply_hmc_and_ecc', out_file_name='dMRI_preprocessed.nii.gz'):
    """
    based on apply_all_corrections()
    Combines two lists of linear transforms
    """

    wf = pe.Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['in_hmc', 'in_ecc', 'in_dwi']), name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_file']),
        name='outputnode')

    combine_xfms = pe.MapNode(fsl.ConvertXFM(concat_xfm=True), iterfield=['in_file', 'in_file2'], name='combine_xfms')
    wf.connect(inputnode, 'in_hmc', combine_xfms, 'in_file')
    wf.connect(inputnode, 'in_ecc', combine_xfms, 'in_file2')

    selref = pe.Node(niu.Select(index=[0]), name='Reference')
    wf.connect(inputnode, 'in_dwi', selref, 'inlist')

    split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
    wf.connect(inputnode, 'in_dwi', split, 'in_file')

    apply_xfm = pe.MapNode(fsl.FLIRT(apply_xfm=True, interp='spline'), iterfield=['in_file', 'in_matrix_file'], name='apply_xfm')
    wf.connect(split, 'out_files', apply_xfm, 'in_file')
    wf.connect(selref, 'out', apply_xfm, 'reference')
    wf.connect(combine_xfms, 'out_file', apply_xfm, 'in_matrix_file')

    thres = pe.MapNode(fsl.Threshold(thresh=0.0), iterfield=['in_file'], name='RemoveNegative')
    wf.connect(apply_xfm, 'out_file', thres, 'in_file')

    merge = pe.Node(fsl.Merge(dimension='t', merged_file=out_file_name), name='MergeDWIs')
    wf.connect(thres, 'out_file', merge, 'in_files')

    wf.connect(merge, 'merged_file', outputnode, 'out_file')

    return wf
