#!/bin/bash

# $1 - file with urls
# $2 - number of urls to download
# $3 - folder to store files

#./upload.sh index/urls.txt 20 index/

urls=$(grep  -v '^#' $1 | grep -o '[^;]\+pdf$')  # load all not commented lines ending with pdf

download_max=$2
download_num=0

cd $3

for line in $urls
do
  #echo $line
  filename=$(echo $line | grep -o '[^/]\+\.[A-Za-z]\+$')
  #echo $filename
  if [ ! -s "${filename}.txt" ]; then
    echo Downloading $line
    wget $line
    ocrmypdf -l rus --sidecar "${filename}.txt" --force-ocr "${filename}" "texted_${filename}"
    sed -i '/^ *$/d' "${filename}.txt" 
    rm "${filename}" "texted_${filename}"
    ((download_num++))
    echo $download_num documents downloaded
    if ((download_num >= download_max)) 
    then
      echo Stop downloading as reached maximum $download_max
      break
    fi  
  else  
    echo File $filename text exists
  fi
done