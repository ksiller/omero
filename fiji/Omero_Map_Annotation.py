#@ String (label="Omero User") username
#@ String (label="Omero Password", style="password") password
#@ String (label="Omero Server", value="omero.hpc.virginia.edu") server
#@ Integer (label="Omero Port", value=4064) port
#@ Integer (label="Omero Group ID", min=-1, value=-1) group_id
#@ String (label="Target", value="Image", choices = ["Image", "Dataset", "Project"]) target_type
#@ Integer (label="Target ID", min=-1, value=-1) target_id

# Basic Java and ImageJ dependencies
from ij.measure import ResultsTable
from java.lang import Double
from java.util import ArrayList
from ij import IJ
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable

# Omero dependencies
import omero
from omero.log import SimpleLogger
from omero.gateway import Gateway
from omero.gateway import LoginCredentials
from omero.gateway import SecurityContext
from omero.gateway.model import ExperimenterData;

from omero.gateway.facility import DataManagerFacility
from omero.gateway.model import MapAnnotationData
from omero.gateway.model import ProjectData
from omero.gateway.model import DatasetData
from omero.gateway.model import ImageData
from omero.model import NamedValue
from omero.model import ProjectDatasetLinkI
from omero.model import ProjectI
from omero.model import DatasetI
from omero.model import ImageI


def connect(group_id, username, password, server, port):    
    """Omero Connect with credentials and simpleLogger"""
    cred = LoginCredentials()
    if group_id != -1:
    	cred.setGroupID(group_id)
    cred.getServer().setHostname(server)
    cred.getServer().setPort(port)
    cred.getUser().setUsername(username)
    cred.getUser().setPassword(password)
    simpleLogger = SimpleLogger()
    gateway = Gateway(simpleLogger)
    e = gateway.connect(cred)
    return gateway


def create_map_annotation(ctx, annotation, target_id, target_type="Project"):
    """Creates a map annotation, uploads it to Omero, and links it to target object"""
    # populate new MapAnnotationData object with dictionary
    result = ArrayList()
    for item in annotation:
        # add key:value pairs; both need to be strings
        result.add(NamedValue(str(item), str(annotation[item])))
    data = MapAnnotationData()
    data.setContent(result);
    data.setDescription("Demo Example");

    #Use the following namespace if you want the annotation to be editable in the webclient and insight
    data.setNameSpace(MapAnnotationData.NS_CLIENT_CREATED);
    dm = gateway.getFacility(DataManagerFacility);
    target_obj = None

    # use the appropriate target DataObject and attach the MapAnnotationData object to it
    if target_type == "Project":
        target_obj = ProjectData(ProjectI(target_id, False))
    elif target_type == "Dataset":	
        target_obj = DatasetData(DatasetI(target_id, False))
    elif target_type == "Image":	
        target_obj = ImageData(ImageI(target_id, False))
    result = dm.attachAnnotation(ctx, data, target_obj);
    return result


# Main code
gateway = connect(group_id, username, password, server, port)
currentGroupId = gateway.getLoggedInUser().getGroupId()
ctx = SecurityContext(currentGroupId)	

# create a dictionary with key:value pairs
annotation = {'Temperature': 25.3, 'Sample': 'control', 'Object count': 34}

result = create_map_annotation(ctx, annotation, target_id, target_type=target_type)
print "Annotation %s exported to Omero." % annotation

gateway.disconnect()