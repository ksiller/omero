#@ String (label="Omero User") username
#@ String (label="Omero Password", style="password") password
#@ String (label="Omero Server", value="omero.hpc.virginia.edu") server
#@ Integer (label="Omero Port", value=4064) server_port
#@ Integer (label="Omero Group ID", min=-1, value=-1) group_id


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
from omero.gateway.exception import DSAccessException
from omero.gateway.exception import DSOutOfServiceException
from omero.gateway.facility import BrowseFacility
from omero.log import SimpleLogger



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


def get_projects_datasets(gateway):
	results = []
	proj_dict = {}
	ds_dict = {}
	groupid = gateway.getLoggedInUser().getGroupId()
	ctx = SecurityContext(groupid)
	containerService = gateway.getPojosService(ctx)

	# Read datasets in all projects
	projects = containerService.loadContainerHierarchy("Project", None, None) # allowed: 'Project", "Dataset", "Screen", "Plate"
	for p in projects:                # omero.model.ProjectI
		p_id = p.getId().getValue()
		p_name = p.getName().getValue()
		proj_dict[p_id] = p_name
		for d in p.linkedDatasetList():
			ds_id = d.getId().getValue()
			ds_name = d.getName().getValue()
			results.append({
				'Project Id': p_id,
				'Project Name': p_name,
				'Dataset Id': ds_id,
				'Dataset Name': ds_name,
				'Group Id': groupid,
			})
			ds_dict[ds_id] = ds_name     

	# read datasets not linked to any project 
	ds_in_proj = [p['Dataset Id'] for p in results]
	ds = containerService.loadContainerHierarchy("Dataset", None, None)
	for d in ds:                # omero.model.ProjectI
		ds_id = d.getId().getValue()
		ds_name = d.getName().getValue()
		if ds_id not in ds_in_proj:
			ds_dict[ds_id] = ds_name
			results.append({
				'Project Id': '--',
				'Project Name': '--',
				'Dataset Id': ds_id,
				'Dataset Name': ds_name,
				'Group Id': groupid,
			})
	return results, proj_dict, ds_dict         


def get_images(gateway, datasets, orphaned=True):
	'''Return all image ids and image names for provided dataset ids'''
	browse = gateway.getFacility(BrowseFacility)
	experimenter = gateway.getLoggedInUser()
	ctx = SecurityContext(experimenter.getGroupId())
	images = []
	for dataset_id in datasets:
		ids = ArrayList(1)
		ids.add(Long(dataset_id))
		j = browse.getImagesForDatasets(ctx, ids).iterator()
		while j.hasNext():
		    image = j.next()
		    images.append({
		        'Image Id': String.valueOf(image.getId()),
		        'Image Name': image.getName(),
		        'Dataset Id': dataset_id,
		        'Dataset Name': datasets[dataset_id],
		    })
	if orphaned:
		orphans = browse.getOrphanedImages(ctx, ctx.getExperimenter()) # need to pass user id (long)
		for image in orphans:
			images.append({
				'Image Id': String.valueOf(image.getId()),
				'Image Name': image.getName(),
				'Dataset Id': -1,
		        'Dataset Name': '<Orphaned>',
			})	
	return images


def show_as_table(title, data, order=[]):
    table = ResultsTable()
    for d in data:
        table.incrementCounter()
        order = [k for k in order]
        order.extend([k for k in d.keys() if not d in order])
        for k in order:
        	table.addValue(k, d[k])
    table.show(title)


# Main code

gateway = connect(group_id, username, password, server, server_port)

groups, current_group = get_groups(gateway)
show_as_table("My Groups", groups, order=['Id', 'Name'])

all_data,_,datasets = get_projects_datasets(gateway)
show_as_table("Projects and Datasets - Group: %s" % current_group, all_data, order=['Group Id', 'Dataset Id', 'Dataset Name', 'Project Name', 'Project Id'])

# created sorted list of unique dataset ids
image_ids = get_images(gateway, datasets, orphaned=True)
show_as_table("Images - Group: %s" % current_group, image_ids, order=['Dataset Id', 'Dataset Name', 'Image Id', 'Image Name'])

gateway.disconnect()	


