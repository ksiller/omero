#@ String (label="Omero User") username
#@ String (label="Omero Password", style="password") password
#@ String (label="Omero Server", value="omero.hpc.virginia.edu") server
#@ Integer (label="Omero Port", value=4064) server_port
#@ Integer (label="Omero Group ID", min=-1, value=-1) omero_group_id
#@ Integer (label="Omero Dataset ID", min=-1, value=-1) dataset_id

import os
from os import path

from java.lang import Long
from java.lang import String
from java.lang.Long import longValue
from java.util import ArrayList
from jarray import array
from java.lang.reflect import Array
import java

# Omero Dependencies
import omero
from omero.gateway import Gateway
from omero.gateway import LoginCredentials
from omero.gateway import SecurityContext
from omero.gateway.facility import BrowseFacility
from omero.log import Logger
from omero.log import SimpleLogger
from omero.model import Pixels

from ome.formats.importer import ImportConfig
from ome.formats.importer import OMEROWrapper
from ome.formats.importer import ImportLibrary
from ome.formats.importer import ImportCandidates
from ome.formats.importer.cli import ErrorHandler
from ome.formats.importer.cli import LoggingImportMonitor
import loci.common
from loci.formats.in import DefaultMetadataOptions
from loci.formats.in import MetadataLevel
from loci.plugins.in import ImporterOptions
from ij import IJ


def connect(group_id, username, password, host, port):    
    '''Omero Connect with credentials and simpleLogger'''
    cred = LoginCredentials()
    if group_id != -1:
        cred.setGroupID(group_id)
    cred.getServer().setHostname(host)
    cred.getServer().setPort(port)
    cred.getUser().setUsername(username)
    cred.getUser().setPassword(password)
    simpleLogger = SimpleLogger()
    gateway = Gateway(simpleLogger)
    gateway.connect(cred)
    group_id = cred.getGroupID()
    return gateway


def open_image(username, password, host, server_port, group_id, image_id):
    command="location=[OMERO] open=[omero:"
    command+="server=%s\n" % server
    command+="user=%s\n" % username
    command+="port=%s\n" % server_port
    command+="pass=%s\n" % password
    if group_id > -1:
		command+="groupID=%s\n" % group_id
    command+="iid=%s] " % image_id
    command+="windowless=true view=\'%s\' " % ImporterOptions.VIEW_HYPERSTACK
    print "Opening image: id", image_id 
    IJ.runPlugIn("loci.plugins.LociImporter", command)
    imp = IJ.getImage()
    return imp


def upload_image(gateway, server, dataset_id, filepath):    
    user = gateway.getLoggedInUser()
    ctx = SecurityContext(user.getGroupId())
    sessionKey = gateway.getSessionId(user)
    
    config = ImportConfig()
    config.email.set("")
    config.sendFiles.set('true')
    config.sendReport.set('false')
    config.contOnError.set('false')
    config.debug.set('false')
    config.hostname.set(server)
    config.sessionKey.set(sessionKey)
    config.targetClass.set("omero.model.Dataset")
    config.targetId.set(dataset_id)
    loci.common.DebugTools.enableLogging("DEBUG")
    
    store = config.createStore()
    reader = OMEROWrapper(config)
    library = ImportLibrary(store,reader)
    errorHandler = ErrorHandler(config)
    
    library.addObserver(LoggingImportMonitor())
    candidates = ImportCandidates (reader, filepath, errorHandler)
    reader.setMetadataOptions(DefaultMetadataOptions(MetadataLevel.ALL))
    success = library.importCandidates(config, candidates)
    return success


def get_image_ids(gateway, dataset_id):
	"""Return all image ids for given dataset"""
	browse = gateway.getFacility(BrowseFacility)
	experimenter = gateway.getLoggedInUser()
	ctx = SecurityContext(experimenter.getGroupId())
	images = []
	ids = ArrayList(1)
	ids.add(Long(dataset_id))
	j = browse.getImagesForDatasets(ctx, ids).iterator()
	while j.hasNext():
	    image = j.next()
	    images.append({
	        'Image Id': String.valueOf(image.getId()),
	        'Image Name': image.getName(),
	        'Dataset Id': dataset_id,
	    })
	return images

	
def process_file(imp):
	"""Invert pixels."""
	print "Processing", imp.getTitle()
	IJ.run(imp, "Invert", "");
	return imp
	
# Main code

gateway = connect(omero_group_id, username, password, server, server_port)
image_info = get_image_ids(gateway, dataset_id)
tmp_dir = os.path.join(os.path.expanduser('~'), 'omero_tmp')
if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)
print tmp_dir
for info in image_info:
	imp = open_image(username, password, server, server_port, omero_group_id, info['Image Id'])
	imp = process_file(imp)

	# Save processed image locally in omero_tmp dir
	title = imp.getTitle().split('.')[:-1]
	title = '.'.join(title) + "_inverted.ome.tiff"
	print title
	filepath = os.path.join(tmp_dir, title)
	options = "save=" + filepath + " export compression=Uncompressed"
	IJ.run(imp, "Bio-Formats Exporter", options)
	#ignore changes & close
	imp.changes=False 
	imp.close()

	# export to OMERO
	upload_image(gateway, server, dataset_id, [filepath])

gateway.disconnect()	

print "Done.\n"

