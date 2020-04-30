#@ String (label="Omero User") username
#@ String (label="Omero Password", style="password") password
#@ String (label="Omero Server", value="omero.hpc.virginia.edu") server
#@ Integer (label="Omero Port", value=4064) server_port
#@ Integer (label="Omero Group ID", min=-1, value=-1) omero_group_id
#@ Integer (label="Omero Input Dataset ID", min=-1, value=-1) dataset_id
#@ String (label="Omero Output Dataset Name", value="Processed Images") target_ds_name
#@ Integer (label="Omero Output Project ID", min=-1, value=-1) project_id


import os
import tempfile
import shutil

from java.lang import Long
from java.lang import String
from java.lang.Long import longValue
from java.util import ArrayList
from jarray import array
from java.lang.reflect import Array
import java
from ij import IJ,ImagePlus
from ij.measure import ResultsTable
import loci.common
from loci.formats.in import DefaultMetadataOptions
from loci.formats.in import MetadataLevel
from loci.plugins.in import ImporterOptions

from loci.plugins.in import ImporterOptions

# Omero Dependencies
import omero
from omero.rtypes import rstring
from omero.gateway import Gateway
from omero.gateway import LoginCredentials
from omero.gateway import SecurityContext
from omero.gateway.facility import BrowseFacility
from omero.gateway.facility import DataManagerFacility
from omero.log import Logger
from omero.log import SimpleLogger
from omero.gateway.model import MapAnnotationData
from omero.gateway.model import ProjectData
from omero.gateway.model import DatasetData
from omero.gateway.model import ImageData
from omero.gateway.model import FileAnnotationData
from omero.model import FileAnnotationI
from omero.model import OriginalFileI
from omero.model import Pixels
from omero.model import NamedValue
from omero.model import ProjectDatasetLinkI
from omero.model import ProjectI
from omero.model import DatasetI
from omero.model import ImageI
from omero.model import ChecksumAlgorithmI
from omero.model.enums import ChecksumAlgorithmSHA1160

from ome.formats.importer import ImportConfig
from ome.formats.importer import OMEROWrapper
from ome.formats.importer import ImportLibrary
from ome.formats.importer import ImportCandidates
from ome.formats.importer.cli import ErrorHandler
from ome.formats.importer.cli import LoggingImportMonitor
from omero.rtypes import rlong


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
    command+="windowless=true "
    command+="splitWindows=false "
    command+="color_mode=Default view=[%s] stack_order=Default" % ImporterOptions.VIEW_HYPERSTACK
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


def create_map_annotation(ctx, annotation, target_id, target_type="Project"):
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
        target_obj = ImageData(ImageI(Long(target_id), False))
    result = dm.attachAnnotation(ctx, data, target_obj);
    return result


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
 

def process_file(imp):
	"""Run segmentation"""
	print "Processing", imp.getTitle()
	title = imp.getTitle().split('.')[:-1]
	title = '.'.join(title) + "_mask.ome.tiff"
	nimp = ImagePlus(title, imp.getStack().getProcessor(1))
	IJ.run(nimp, "Median...", "radius=3")
	IJ.run(nimp, "Auto Local Threshold", "method=Bernsen radius=15 parameter_1=0 parameter_2=0 white")
	IJ.run(nimp, "Watershed", "")

	IJ.run("Set Measurements...", "area mean standard centroid decimal=3")
	IJ.run(nimp, "Analyze Particles...", "size=50-Infinity summary exclude clear add")
	rt = ResultsTable.getResultsTable()
	rt.show("Results")

	imp.close()
	return nimp, rt 


def create_new_dataset(ctx, project_id, ds_name, ):
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

	
# Main code
gateway = connect(omero_group_id, username, password, server, server_port)
currentGroupId = gateway.getLoggedInUser().getGroupId()
ctx = SecurityContext(currentGroupId)

image_info = get_image_ids(gateway, dataset_id)
tmp_dir = tempfile.gettempdir()
print tmp_dir

target_ds_id = create_new_dataset(ctx, project_id, target_ds_name)
for info in image_info:
	imp = open_image(username, password, server, server_port, omero_group_id, info['Image Id'])
	processed_imp, rt = process_file(imp)

	# Save processed image locally in omero_tmp dir
	imgfile = tempfile.TemporaryFile(mode='wb', prefix='img_', suffix='.tiff', dir=tmp_dir)

	#filepath = os.path.join(tmp_dir, processed_imp.getTitle())
	options = "save=" + imgfile.name + " export compression=Uncompressed"
	IJ.run(processed_imp, "Bio-Formats Exporter", options)
	#ignore changes & close
	processed_imp.changes=False 
	processed_imp.close()

	# uploaad image to a target dataset
	upload_image(gateway, server, target_ds_id, [imgfile.name])

	# create annotation
	annotation = {
		"Cell count": rt.size()
	}	
	create_map_annotation(ctx, annotation, info['Image Id'], target_type="Image")

	# export ResultsTable to csv file and link to image object
	file = tempfile.TemporaryFile(mode='wb', prefix='results_', suffix='.csv', dir=tmp_dir)
	rt.saveAs(file.name)
	upload_csv_to_omero(ctx, file, "Results.csv", long(info['Image Id']), "Image")

# done, clean up	
shutil.rmtree(tmp_dir)
gateway.disconnect()	
print "Done.\n"

