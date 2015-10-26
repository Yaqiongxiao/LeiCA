#!/usr/bin/env bash

# script backs up folders in resutls folder that either start with 0* or with A*
# if A*: names are alterd: first zero is removed: A012... -> A12...
# (Grenze ist 21, aktuell heisst ein Block z.B. prob.noid024.A1234567 .


source_path=/scr/adenauer2/Franz/LeiCA_NKI/results
target_path=/a/projects/noid024_leica-nki/probands

cd $source_path


for D in 0*; do
    echo "*************************************************"
    echo $D
    echo "*************************************************"

    if [ ! -d $target_path/$D ]; then
        echo "create new folder on /a ${D}"
        cmd="newvp2 -p noid024_leica-nki -o ${D}"
        echo $cmd
        ${cmd}
    fi

    cmd="rsync -av --no-o --no-g ${source_path}/${D}/ ${target_path}/${D}/"
    echo $cmd
    $cmd
done


22
# because /a cannot take IDs with more than 9 chars, the heading 0 (after the A) is cut
for D in A*; do
    short_id=A${D:2}
    if [ ! -d $target_path/$short_id ]; then
        cmd="newvp2 -p noid024_leica-nki -o $short_id"
        echo $cmd
        $cmd
    fi
done
22

# because /a cannot take IDs with more than 9 chars, the heading 0 (after the A) is cut
for D in A*; do
    echo "*************************************************"
    echo $D
    echo "*************************************************"

    short_id=A${D:2}

    if [ ! -d $target_path/$short_id ]; then
        echo "create new folder on /a ${D} -> ${short_id}"
        cmd="newvp2 -p noid024_leica-nki -o $short_id"
        echo $cmd
        $cmd
    fi

    cmd="rsync -av --no-o --no-g ${source_path}/${D}/ ${target_path}/${short_id}/"
    echo $cmd
    $cmd
done

