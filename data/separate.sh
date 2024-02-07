#!/bin/bash
counter=1
cp $1 $1_temp
while [ -s $1_temp ]; do
  sed -E '/^=+$/Q' $1_temp > $1_part_$counter
  sed -Ei '1,/^=+/d' $1_temp
  ((counter++))
done

rm $1_temp

