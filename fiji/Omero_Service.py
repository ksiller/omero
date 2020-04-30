#@ OMEROService omeroService
#@ String (label="Omero User") username
#@ String (label="Omero Password", style="password") password
#@ String (label="Omero Server", value="omero.hpc.virginia.edu") server
#@ Integer (label="Omero Port", value=4064) server_port

from net.imagej.omero import OMEROLocation

client = omeroService.session(OMEROLocation(server, server_port, username, password)).getClient()
image = omeroService.downloadImage(client, 4443)