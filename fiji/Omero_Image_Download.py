# @ String (label="Omero User") user
# @ String (label="Omero Password", style="password") pwd
# @ String (label="Omero Server", value="omero.hpc.virginia.edu") server
# @ Integer (label="Omero Port", value=4064) port
# @ Integer (label="Omero Group ID", min=-1, value=53) omero_group_id
# @ Integer (label="Image ID", value=2014) image_id

from ij import IJ
from loci.plugins.in import ImporterOptions
	 
# Main code
command="location=[OMERO] open=[omero:"
command+="server=%s\n" % server
command+="user=%s\n" % user
command+="port=%s\n" % port
command+="pass=%s\n" % pwd
if omero_group_id > -1:
	command+="groupID=%s\n" % omero_group_id
command+="iid=%s] " % image_id
command+="windowless=true view=\'%s\' " % ImporterOptions.VIEW_HYPERSTACK
IJ.runPlugIn("loci.plugins.LociImporter", command)
