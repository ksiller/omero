#@ String (label="Omero User") username
#@ String (label="Omero Password", style="password") password
#@ String (label="Omero Server", value="omero.hpc.virginia.edu") server
#@ Integer (label="Omero Port", value=4064) server_port
#@ Integer (label="Omero Group ID", min=-1, value=-1) group_id
#@ Integer (label="Omero Project ID", min=-1, value=-1) project_id
#@ String (label="New Dataset", value="new dataset") dataset_name

# Basic Java and ImageJ dependencies
from ij.measure import ResultsTable
from java.lang import Long
from java.lang import String
from java.util import ArrayList

# Omero dependencies
import omero
from omero.gateway import Gateway
from omero.gateway import LoginCredentials
from omero.gateway import SecurityContext
from omero.gateway.facility import DataManagerFacility
from omero.gateway.exception import DSAccessException
from omero.gateway.exception import DSOutOfServiceException
from omero.gateway.facility import BrowseFacility
from omero.model import ProjectDatasetLinkI
from omero.model import ProjectI
from omero.log import SimpleLogger
from omero.rtypes import rstring

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
    e = gateway.connect(cred)
    return gateway


def create_new_dataset(ctx, project_id, ds_name):
    dataset_obj = omero.model.DatasetI()
    dataset_obj.setName(rstring(ds_name))
    dataset_obj = gateway.getUpdateService(ctx).saveAndReturnObject(dataset_obj)
    dataset_id = dataset_obj.getId().getValue()

    dm = gateway.getFacility(DataManagerFacility)
    link = ProjectDatasetLinkI();
    link.setChild(dataset_obj);
    link.setParent(ProjectI(project_id, False));
    r = dm.saveAndReturnObject(ctx, link);
    return dataset_id


gateway = connect(group_id, username, password, server, server_port)
currentGroupId = gateway.getLoggedInUser().getGroupId()
ctx = SecurityContext(currentGroupId)

dataset_id = create_new_dataset(ctx, project_id, dataset_name)
print "New dataset, Id:", dataset_id

gateway.disconnect()