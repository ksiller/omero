#@ String (label="Omero User") username
#@ String (label="Omero Password", style="password") password
#@ String (label="Omero Server", value="omero.hpc.virginia.edu") host
#@ Integer (label="Omero Port", value=4064) port
#@ Integer (label="Omero Group ID", min=-1, value=-1) group_id
#@ String (label="Target", value="Image", choices = ["Image", "Dataset", "Project"]) target_type
#@ Integer (label="Target ID", min=-1, value=-1) target_id


# Basic Java and ImageJ dependencies
from ij import IJ
from ij.measure import ResultsTable
from java.lang import Long
from java.lang import String
from java.util import ArrayList

# Basic Python packages
import os
import tempfile
import random

# Omero dependencies
import omero
from omero.log import SimpleLogger
from omero.gateway import Gateway
from omero.gateway import LoginCredentials
from omero.gateway import SecurityContext
from omero.gateway.exception import DSAccessException
from omero.gateway.exception import DSOutOfServiceException
from omero.gateway.facility import BrowseFacility
from omero.gateway.facility import DataManagerFacility
from omero.gateway.facility import TablesFacility
from omero.gateway.model import ExperimenterData;
from omero.gateway.model import FileAnnotationData
from omero.gateway.model import TableData
from omero.gateway.model import TableDataColumn
from omero.gateway.model import ProjectData
from omero.gateway.model import DatasetData
from omero.gateway.model import ImageData
from omero.grid import LongColumn
from omero.grid import StringColumn
from omero.model import ChecksumAlgorithmI
from omero.model import FileAnnotationI
from omero.model import ProjectI
from omero.model import DatasetI
from omero.model import ImageI
from omero.model import OriginalFileI
from omero.model.enums import ChecksumAlgorithmSHA1160

from omero.model import DatasetAnnotationLinkI
from omero.rtypes import rstring
from omero.rtypes import rlong


def connect(group_id, username, password, host, port):    
    """Omero Connect with credentials and simpleLogger"""
    cred = LoginCredentials()
    if group_id != -1:
    	cred.setGroupID(group_id)
    cred.getServer().setHostname(host)
    cred.getServer().setPort(port)
    cred.getUser().setUsername(username)
    cred.getUser().setPassword(password)
    simpleLogger = SimpleLogger()
    gateway = Gateway(simpleLogger)
    e = gateway.connect(cred)
    return gateway


def upload_csv_to_omero(ctx, file, tablename, target_id, target_type="Project"):
    """Upload the CSV file and attach it to the specified object"""
    print file
    print file.name
    svc = gateway.getFacility(DataManagerFacility)
    file_size = os.path.getsize(file.name)
    original_file = OriginalFileI()
    original_file.setName(rstring(tablename))
    original_file.setPath(rstring(file.name))
    original_file.setSize(rlong(file_size))

    checksum_algorithm = ChecksumAlgorithmI()
    checksum_algorithm.setValue(rstring(ChecksumAlgorithmSHA1160.value))
    original_file.setHasher(checksum_algorithm)
    original_file.setMimetype(rstring("text/csv"))
    original_file = svc.saveAndReturnObject(ctx, original_file)
    store = gateway.getRawFileService(ctx)

    # Open file and read stream
    store.setFileId(original_file.getId().getValue())
    print original_file.getId().getValue()
    try:
        store.setFileId(original_file.getId().getValue())
        with open(file.name, 'rb') as stream:
            buf = 10000
            for pos in range(0, long(file_size), buf):
                block = None
                if file_size-pos < buf:
                    block_size = file_size-pos
                else:
                    block_size = buf
                stream.seek(pos)
                block = stream.read(block_size)
                store.write(block, pos, block_size)

        original_file = store.save()
    finally:
        store.close()

    # create the file annotation
    namespace = "training.demo"
    fa = FileAnnotationI()
    fa.setFile(original_file)
    fa.setNs(rstring(namespace))

    if target_type == "Project":
        target_obj = ProjectData(ProjectI(target_id, False))
    elif target_type == "Dataset":	
        target_obj = DatasetData(DatasetI(target_id, False))
    elif target_type == "Image":	
        target_obj = ImageData(ImageI(target_id, False))

    svc.attachAnnotation(ctx, FileAnnotationData(fa), target_obj)
    

def create_mock_resultstable():
	"""Creates small ResultsTable with fictive values"""
	# Create a ImageJ ResultsTable, convert it into Omero table object, upload and link it to target object
	imp = IJ.openImage("http://imagej.nih.gov/ij/images/blobs.gif")
	imp.show()
	mask = imp.duplicate()
	IJ.run(mask, "Median...", "radius=2")
	IJ.run(mask, "Options...", "iterations=1 count=1 black")
	IJ.setAutoThreshold(mask, "Default")
	IJ.run(mask, "Convert to Mask", "")
	IJ.run(mask, "Watershed", "")
	IJ.run(mask, "Set Measurements...", "area mean min centroid integrated display redirect=%s decimal=3" % imp.getTitle())
	IJ.run(mask, "Analyze Particles...", "size=0-Infinity display exclude clear summarize add")
	imp.close()
	
	rt = ResultsTable.getResultsTable()
	rt.show("Results")
	return rt


# Main code
gateway = connect(group_id, username, password, host, port)
currentGroupId = gateway.getLoggedInUser().getGroupId()
ctx = SecurityContext(currentGroupId)

# create a ResultsTable
rt = create_mock_resultstable()

# save ResultsTable to tmp .csv file, upload it to Omero, then delete the local file
tmp_dir = tempfile.gettempdir()
file = tempfile.TemporaryFile(mode='wb', prefix='results_', suffix='.csv', dir=tmp_dir)
rt.saveAs(file.name)
upload_csv_to_omero(ctx, file, "Results.csv", target_id, target_type)
os.remove(file.name)

gateway.disconnect()	


