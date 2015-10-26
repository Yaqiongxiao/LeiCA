#!/usr/bin/env bash

# script backs up folders in resutls folder that either start with 0* or with A*
# if A*: names are alterd: first zero is removed: A012... -> A12...
# (Grenze ist 21, aktuell heisst ein Block z.B. prob.noid024.A1234567 .


source_path=/scr/adenauer2/Franz/LeiCA_NKI/results
target_path=/a/projects/noid024_leica-nki/probands

cd $source_path


for D in 0*; do
    cmd="rsync -av --no-o --no-g ${source_path}/${D}/ ${target_path}/${D}/"
    $cmd
done


# because /a cannot take IDs with more than 9 chars, the heading 0 (after the A) is cut
for D in A*; do
    short_id=A${D:2}
    cmd="rsync -av --no-o --no-g ${source_path}/${D}/ ${target_path}/${short_id}/"
    $cmd
done

