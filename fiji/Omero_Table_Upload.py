#@ String (label="Omero User") username
#@ String (label="Omero Password", style="password") password
#@ String (label="Omero Server", value="omero.hpc.virginia.edu") server
#@ Integer (label="Omero Port", value=4064) port
#@ Integer (label="Omero Group ID", min=-1, value=-1) group_id
#@ String (label="Target", value="Image", choices = ["Image", "Dataset", "Project"]) target_type
#@ Integer (label="Target ID", min=-1, value=-1) target_id


# Basic Java and ImageJ dependencies
from ij.measure import ResultsTable
from java.lang import Long
from java.lang import String
from java.lang import Double
from java.util import ArrayList

from ij import IJ
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable

# Omero dependencies
import omero
import random
from omero.log import SimpleLogger
from omero.gateway import Gateway
from omero.gateway import LoginCredentials
from omero.gateway import SecurityContext
from omero.gateway.exception import DSAccessException
from omero.gateway.exception import DSOutOfServiceException
from omero.gateway.facility import BrowseFacility
from omero.gateway.facility import TablesFacility
from omero.gateway.model import ExperimenterData;
from omero.gateway.model import FileAnnotationData
from omero.gateway.model import ProjectData
from omero.gateway.model import DatasetData
from omero.gateway.model import ImageData
from omero.gateway.model import TableData
from omero.gateway.model import TableDataColumn
from omero.model import ProjectI
from omero.model import DatasetI
from omero.model import ImageI
from omero.model import FileAnnotationI
from omero.model import DatasetAnnotationLinkI
from omero.grid import LongColumn
from omero.grid import StringColumn


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

"""
def get_groups(gateway):
	currentGroupId = gateway.getLoggedInUser().getGroupId()
	ctx = SecurityContext(currentGroupId)
	adminService = gateway.getAdminService(ctx, True)
	uid = adminService.lookupExperimenter(username)
	groups = []
	for g in sorted(adminService.getMemberOfGroupIds(uid)):
		groupname = str(adminService.getGroup(g).getName().getValue())
		groups.append({
		    'Id': g,
		    'Name': groupname,
		})
		if g == currentGroupId:
			currentGroup = groupname     
	return groups, currentGroup
"""


def create_table(gatway):
	currentGroupId = gateway.getLoggedInUser().getGroupId()
	ctx = SecurityContext(currentGroupId)

	fac = gateway.getFacility(TablesFacility)
	table_name = "TablesDemo:%s" % str(random.randint(1,1000))
	col1 = omero.grid.LongColumn('Uid', 'testLong', [])
	col2 = omero.grid.StringColumn('MyStringColumnInit', '', 64, [])
	columns = [col1, col2]
	
	resources = gateway.getSharedResources(ctx)
	repository_id = resources.repositories().descriptions[0].getId().getValue()
	table = resources.newTable(repository_id, table_name)
	table.initialize(columns)

	# Add data to the table
	ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
	strings = ["one", "two", "three", "four", "five",
	           "six", "seven", "eight", "nine", "ten"]
	data1 = omero.grid.LongColumn('Uid', 'test Long', ids)
	data2 = omero.grid.StringColumn('MyStringColumn', '', 64, strings)
	data = [data1, data2]
	table.addData(data)
	table.close()        

	return table


def link_table_to_object(gateway, table, target_id, target_type="Project"):
    """Links an Omero table object to an existing target object"""
    orig_file = table.getOriginalFile()
    orig_file_id = orig_file.id.getValue()

    file_ann = omero.model.FileAnnotationI()
    file_ann.setFile(omero.model.OriginalFileI(orig_file_id, False))
    file_ann = gateway.getUpdateService(ctx).saveAndReturnObject(file_ann)
    
    # use the appropriate target DataObject and attach the MapAnnotationData object to it
    if target_type == "Project":
        link = omero.model.ProjectAnnotationLinkI()
        link.setParent(omero.model.ProjectI(target_id, False))
    elif target_type == "Dataset":	
        link = omero.model.DatasetAnnotationLinkI()
        link.setParent(omero.model.DatasetI(target_id, False))
    elif target_type == "Image":	
        link = omero.model.ImageAnnotationLinkI()
        link.setParent(omero.model.ImageI(target_id, False))
    link.setChild(omero.model.FileAnnotationI(file_ann.getId().getValue(), False))
    
    return gateway.getUpdateService(ctx).saveAndReturnObject(link)


def upload_rt_as_omero_table(rt, ctx, target_id, target_type, roivec=[]):
    "Convert results into an OMERO table"
    roivec_cols = ['ROI-id', 'Shape-id', 'Z', 'C', 'T']
    length = len(roivec_cols)
    no_of_columns = rt.getLastColumn() + length
    no_of_rows = rt.size()

    data = [[Double(0) for x in range(no_of_rows)] for y in range(no_of_columns)]
    columns = [TableDataColumn] * no_of_columns

    for c in range(0, no_of_columns):
        if c < length:
            colname = roivec_cols[c]
            rows = [Double(i[c]) for i in roivec]
            columns[c] = TableDataColumn(colname, c, Double)
        else:
            colname = rt.getColumnHeading(c-length)
            rows = rt.getColumnAsDoubles(c-length)
            columns[c] = TableDataColumn(colname, c, Double)

        if rows is None:
            continue
        for r in range(0, len(rows)):
            data[c][r] = rows[r]

    table_data = TableData(columns, data)
    browse = gateway.getFacility(BrowseFacility)
     # use the appropriate target DataObject and attach the MapAnnotationData object to it
    if target_type == "Project":
        target_obj = ProjectData(ProjectI(target_id, False))
    elif target_type == "Dataset":	
        target_obj = DatasetData(DatasetI(target_id, False))
    elif target_type == "Image":	
        target_obj = browse.getImage(ctx, long(target_id))
   
    table_facility = gateway.getFacility(TablesFacility)
    table_facility.addTable(ctx, target_obj, "Table_from_Fiji", table_data)


# Main code
gateway = connect(group_id, username, password, server, port)
currentGroupId = gateway.getLoggedInUser().getGroupId()
ctx = SecurityContext(currentGroupId)

# 1. Create a Omero Table obkect, upload, and link it to target object
table = create_table(gateway)
link_table_to_object(gateway, table, target_id, target_type)

# 2. Create a ImageJ ResultsTable, convert it into Omero table object, upload and link it to target object
imp = IJ.openImage("http://imagej.nih.gov/ij/images/blobs.gif");
IJ.run(imp, "8-bit", "")
# white might be required depending on the version of Fiji
IJ.run(imp, "Auto Threshold", "method=MaxEntropy stack")
IJ.run(imp, "Analyze Particles...", "size=10-Infinity pixel display clear add stack");
IJ.run("Set Measurements...", "area mean standard modal min centroid center \
        perimeter bounding fit shape feret's integrated median skewness \
        kurtosis area_fraction stack display redirect=None decimal=3")
imp.close()

rt = ResultsTable.getResultsTable()
upload_rt_as_omero_table(rt, ctx, target_id, target_type,)
print "ResultsTable uploaded as Omero Table object."

gateway.disconnect()	


