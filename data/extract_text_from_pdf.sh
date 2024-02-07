#!/bin/bash

#OLDIFS=$IFS
#IFS=`echo -e "\n"`

cd $1

for file in *.pdf
do
  echo $file
  pdftotext $file ${file}.txt
  #ocrmypdf -l rus --sidecar "${filename}.txt" --force-ocr "${filename}" "texted_${filename}"
  #rm "texted_${filename}"
done

#IFS=$OLDIFS