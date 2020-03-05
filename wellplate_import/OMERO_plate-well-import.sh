#!/bin/bash

# OMERO Screen-Plate-Well Import Script

USER='YOUR_ID'
PASSWORD=''


IMAGES=/home/cag3fr/omero-demo/WormImages

PLATENAME='WormImages'
PLATEFILE="${PLATENAME}.txt"

cd $IMAGES

# Log into OMERO

omero login -s 'localhost' -p 4064 -u $USER -w $PASSWORD


# Create Plate in OMERO

python -c "from ImportToOmero import CreatePlate; PLATEID=CreatePlate('$PLATENAME','$USER','$PASSWORD')"

PLATEID=$(head -n 1 $PLATEFILE)



for i in *.png
do

	IMAGENAME="$i"
	WELLNUM="${i%.*}"
	
	IMAGEID=$(omero import $IMAGENAME)
	python -c "from ImportToOmero import CreateWell; CreateWell('$IMAGEID','$PLATEID','$WELLNUM','$USER','$PASSWORD')"
	
done

rm $PLATEFILE
