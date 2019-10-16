#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 22:32:25 2019

@author: cag3fr
"""

def CreatePlate(plateName,user,passwd):
    import sys
    sys.path.append('/home/cag3fr/omero_server/lib/python')

    import Ice
    import omero
    from omero.gateway import BlitzGateway
    import omero.scripts as scripts
    import omero.util.script_utils as script_utils
    from omero.rtypes import rint, rlong, rstring, robject, unwrap

    import pandas as pd
    import csv, operator
    import fnmatch
    import os
    import math
    
    # Dictionary of Well Number and Row/Column Number
    Well96_to_RowCol = {'A01':[0,0], 'A02':[0,1], 'A03':[0,2], 'A04':[0,3], 'A05':[0,4], 'A06':[0,5], 'A07':[0,6], 'A08':[0,7], 'A09':[0,8], 'A10':[0,9], 'A11':[0,10], 'A12':[0,11],
                        'B01':[1,0], 'B02':[1,1], 'B03':[1,2], 'B04':[1,3], 'B05':[1,4], 'B06':[1,5], 'B07':[1,6], 'B08':[1,7], 'B09':[1,8], 'B10':[1,9], 'B11':[1,10], 'B12':[1,11],
                        'C01':[2,0], 'C02':[2,1], 'C03':[2,2], 'C04':[2,3], 'C05':[2,4], 'C06':[2,5], 'C07':[2,6], 'C08':[2,7], 'C09':[2,8], 'C10':[2,9], 'C11':[2,10], 'C12':[2,11],
                        'D01':[3,0], 'D02':[3,1], 'D03':[3,2], 'D04':[3,3], 'D05':[3,4], 'D06':[3,5], 'D07':[3,6], 'D08':[3,7], 'D09':[3,8], 'D10':[3,9], 'D11':[3,10], 'D12':[3,11],
                        'E01':[4,0], 'E02':[4,1], 'E03':[4,2], 'E04':[4,3], 'E05':[4,4], 'E06':[4,5], 'E07':[4,6], 'E08':[4,7], 'E09':[4,8], 'E10':[4,9], 'E11':[4,10], 'E12':[4,11],
                        'F01':[5,0], 'F02':[5,1], 'F03':[5,2], 'F04':[5,3], 'F05':[5,4], 'F06':[5,5], 'F07':[5,6], 'F08':[5,7], 'F09':[5,8], 'F10':[5,9], 'F11':[5,10], 'F12':[5,11],
                        'G01':[6,0], 'G02':[6,1], 'G03':[6,2], 'G04':[6,3], 'G05':[6,4], 'G06':[6,5], 'G07':[6,6], 'G08':[6,7], 'G09':[6,8], 'G10':[6,9], 'G11':[6,10], 'G12':[6,11],
                        'H01':[7,0], 'H02':[7,1], 'H03':[7,2], 'H04':[7,3], 'H05':[7,4], 'H06':[7,5], 'H07':[7,6], 'H08':[7,7], 'H09':[7,8], 'H10':[7,9], 'H11':[7,10], 'H12':[7,11]}    
    


    
    
    #Create plate in omero

    conn = BlitzGateway(user, passwd, host="localhost", port=4064)
    conn.connect()
    updateService = conn.getUpdateService()
    
    plate = omero.model.PlateI()
    plate.name = omero.rtypes.RStringI(plateName)
    plate.columnNamingConvention = rstring("number")
    plate.rowNamingConvention = rstring("letter")
    plate = updateService.saveAndReturnObject(plate)
    plateId = plate.id.val
    plate = conn.getObject("Plate",plateId)


    conn.close()
    
    filename = plateName + ".txt"
    f = open(filename, "w")
    f.write(str(plateId))
    f.close()
    
    

def CreateWell(imageId,plateId,wellNum,user,passwd):
    import sys
    sys.path.append('/home/cag3fr/omero_server/lib/python')

    import Ice
    import omero
    from omero.gateway import BlitzGateway
    import omero.scripts as scripts
    import omero.util.script_utils as script_utils
    from omero.rtypes import rint, rlong, rstring, robject, unwrap

    import pandas as pd
    import csv, operator
    import fnmatch
    import os
    import math
    
    # Dictionary of Well Number and Row/Column Number
    Well96_to_RowCol = {'A01':[0,0], 'A02':[0,1], 'A03':[0,2], 'A04':[0,3], 'A05':[0,4], 'A06':[0,5], 'A07':[0,6], 'A08':[0,7], 'A09':[0,8], 'A10':[0,9], 'A11':[0,10], 'A12':[0,11],
                        'B01':[1,0], 'B02':[1,1], 'B03':[1,2], 'B04':[1,3], 'B05':[1,4], 'B06':[1,5], 'B07':[1,6], 'B08':[1,7], 'B09':[1,8], 'B10':[1,9], 'B11':[1,10], 'B12':[1,11],
                        'C01':[2,0], 'C02':[2,1], 'C03':[2,2], 'C04':[2,3], 'C05':[2,4], 'C06':[2,5], 'C07':[2,6], 'C08':[2,7], 'C09':[2,8], 'C10':[2,9], 'C11':[2,10], 'C12':[2,11],
                        'D01':[3,0], 'D02':[3,1], 'D03':[3,2], 'D04':[3,3], 'D05':[3,4], 'D06':[3,5], 'D07':[3,6], 'D08':[3,7], 'D09':[3,8], 'D10':[3,9], 'D11':[3,10], 'D12':[3,11],
                        'E01':[4,0], 'E02':[4,1], 'E03':[4,2], 'E04':[4,3], 'E05':[4,4], 'E06':[4,5], 'E07':[4,6], 'E08':[4,7], 'E09':[4,8], 'E10':[4,9], 'E11':[4,10], 'E12':[4,11],
                        'F01':[5,0], 'F02':[5,1], 'F03':[5,2], 'F04':[5,3], 'F05':[5,4], 'F06':[5,5], 'F07':[5,6], 'F08':[5,7], 'F09':[5,8], 'F10':[5,9], 'F11':[5,10], 'F12':[5,11],
                        'G01':[6,0], 'G02':[6,1], 'G03':[6,2], 'G04':[6,3], 'G05':[6,4], 'G06':[6,5], 'G07':[6,6], 'G08':[6,7], 'G09':[6,8], 'G10':[6,9], 'G11':[6,10], 'G12':[6,11],
                        'H01':[7,0], 'H02':[7,1], 'H03':[7,2], 'H04':[7,3], 'H05':[7,4], 'H06':[7,5], 'H07':[7,6], 'H08':[7,7], 'H09':[7,8], 'H10':[7,9], 'H11':[7,10], 'H12':[7,11]}    
    
    
    conn = BlitzGateway(user,passwd,host="localhost",port=4064)
    conn.connect()
    
    image = conn.getObject("Image",int(imageId[6:]))
    
    updateService = conn.getUpdateService()
    
    well = omero.model.WellI()
    well.plate = omero.model.PlateI(int(plateId), False)
    
    wellRowCol = Well96_to_RowCol.get(wellNum)
    well.column = rint(wellRowCol[1])
    well.row = rint(wellRowCol[0])
    
    ws = omero.model.WellSampleI()
    ws.image = omero.model.ImageI(image.id,False)
    ws.well = well
    well.addWellSample(ws)
    updateService.saveAndReturnObject(ws)
    
    conn.close()