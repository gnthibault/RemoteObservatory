#!/bin/bash

im_dir=/home/gnthibault/Documents/club_astro/im_dir2
im_ext=".JPG"
solve_cmd=/home/gnthibault/projects/RemoteObservatory/scripts/solve_field.sh
# Replace space
#for f in *\ *; do mv "$f" "${f// /_}"; done

# Field of a 24x36:
#        Horizontal Vertical Diagonal
# 50mm:  39.6       27.0     46.8
# 135mm: 15.2       10.2     18.2
# 200mm: 10.3       6.9      12.3

# Solve 50mm
LOW_SCALE=27.0
HIGH_SCALE=46.8
im_path=$im_dir/50mm
find $im_path -name "*$im_ext" | while read f;
do
 echo "Solving $f"
 $solve_cmd --cpulimit 180 --no-verify --crpix-center --match none --corr none --wcs none --downsample 1 --overwrite --skip-solved --scale-low $LOW_SCALE --scale-high $HIGH_SCALE --scale-units degwidth --new-fits "${f%$im_ext}.fits" "$f"
done

# Solve 135mm
LOW_SCALE=10.2
HIGH_SCALE=18.2
im_path=$im_dir/135mm
find $im_path -name "*$im_ext" | while read f;
do
  echo "Solving $f"
  $solve_cmd --cpulimit 180 --no-verify --crpix-center --match none --corr none --wcs none --downsample 1 --overwrite --skip-solved --scale-low $LOW_SCALE --scale-high $HIGH_SCALE --scale-units degwidth --new-fits "${f%$im_ext}.fits" "$f"
done

# Solve 200mm
LOW_SCALE=6.9
HIGH_SCALE=12.3
im_path=$im_dir/200mm
find $im_path -name "*$im_ext" | while read f;
do
  echo "Solving $f"
  $solve_cmd --cpulimit 180 --no-verify --crpix-center --match none --corr none --wcs none --downsample 1 --overwrite --skip-solved --scale-low $LOW_SCALE --scale-high $HIGH_SCALE --scale-units degwidth --new-fits "${f%$im_ext}.fits" "$f"
done


