# @ File (label="Input directory", style="directory") inputdir
# @ Float (label="Gaussian blur radius", value=2.0) radius 
# @ String (label="Omero User") user_id
# @ String (label="Omero Password", style="password") password
# @ String (label="Omero Server", value="omero.hpc.virginia.edu") host
# @ Integer (label="Omero Port", value=4064) server_port
# @ Integer (label="Omero Dataset ID", value=69) data_id

from ij import IJ
import os
from os import path

def process_file(f, radius):
	"""Opens a file and applies a Gaussian filter."""
	print "Processing", f
	imp = IJ.openImage(f)
	IJ.run(imp, "Gaussian Blur...", "sigma=%s" % str(radius));
	return imp

	 
# Main code
basecommand = "server=%s " % host
basecommand+= "port=%s " % server_port
basecommand+= "user=%s " % user_id
basecommand+= "password=%s " % password
basecommand+= "datasetid=%d " % data_id
basecommand+= "uploadimage=true uploadtables=false uploadrois=false updaterois=false tablenames= "

inputdir = str(inputdir)
if not path.isdir(inputdir):
    print inputdir, " does not exist or is not a directory."
else:
	filenames = os.listdir(inputdir)
	tif_files = [f for f in filenames if f.split(".")[-1] == "tif"]		# only .tif files
	for tif_file in tif_files:
		fullpath = path.join(inputdir, tif_file)
		imp = process_file(fullpath, radius)
		# need to show image for OMERO to pick it up
		imp.show()
		# export to OMERO
		IJ.run(imp, "OMERO... ", basecommand+"image=%s" % imp.getTitle())
		#ignore changes & close
		imp.changes=False 
		imp.close()
		#save_as_tif(outputdir, imp)
	print "Done.\n"