#!/bin/bash

#OLDIFS=$IFS
#IFS=`echo -e "\n"`

cd $1

for filename in *.pdf
do
  echo $filename
  ocrmypdf -l rus --sidecar "${filename}.txt" --force-ocr "${filename}" "texted_${filename}"
  rm "texted_${filename}"
done

#IFS=$OLDIFS