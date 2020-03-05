%%%%%%%%%

% Sample MATLAB Image Processing pipeline with OMERO

%%%%%%%%%
%% Log into OMERO

myUsername = 'YOUR_ID';
myPassword = 'YOUR_PASSWORD';

    
%%%%% Don't change anything in this section! %%%%%
    
client = loadOmero('omero.hpc.virginia.edu',4064);
    
session = client.createSession(myUsername, myPassword);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Specify the Project and Dataset containing raw data

projectID = 107;

datasetID = 163;
%% Each image is processed and analyzed, then exported back to OMERO

%%%%% Don't change anything below this line! %%%%%

dataset = getDatasets(session, datasetID, true);
datasetName = char(dataset.getName().getValue());
imageList = dataset(1).linkedImageList;
imageList = imageList.toArray.cell;

newdataset = createDataset(session, 'Colon Cancer Analysis', ...
    getProjects(session,projectID));

for i = 1:length(imageList)
    pixels = imageList{i}.getPrimaryPixels();
    name = char(imageList{i}.getName().getValue());
    store = session.createRawPixelsStore();
    store.setPixelsId(pixels.getId().getValue(),false);
    plane = store.getPlane(0,0,0);
    img = uint8(toMatrix(plane,pixels));
    
    type = 'uint8';
    
    newimg = uint8(contrastIncrease(img));
    newimg = uint8(binarizeImage(newimg));
    newname = strcat('b_',name);
    
    pixelsService = session.getPixelsService();
    pixelTypes = toMatlabList(session.getTypesService().allEnumerations('omero.model.PixelsType'));
    pixelTypeValues = arrayfun(@(x) char(x.getValue().getValue()),pixelTypes,'Unif',false);
    pixelType = pixelTypes(strcmp(pixelTypeValues, type));
    
    description = sprintf('Dimensions: 512 x 512 x 1 x 1 x 1');
    
    idNew = pixelsService.createImage(512,512,1,1,toJavaList(0:0,'java.lang.Integer'),pixelType,newname,description);

    imageNew = getImages(session, idNew.getValue());
    
    link = omero.model.DatasetImageLinkI;
    link.setChild(omero.model.ImageI(idNew,false));
    link.setParent(omero.model.DatasetI(newdataset.getId().getValue(),false));
    session.getUpdateService().saveAndReturnObject(link);
    
    pixels = imageNew.getPrimaryPixels();
    store = session.createRawPixelsStore();
    store.setPixelsId(pixels.getId().getValue(),false);
    byteArray = toByteArray(newimg, pixels);
    
    store.setPlane(byteArray,0,0,0);
    store.save();
    store.close();
    
    cc = bwconncomp(newimg,4);
    numCells = num2str(cc.NumObjects);
    
    mapAnnotation = writeMapAnnotation(session,'Count',numCells);
    
    link = linkAnnotation(session, mapAnnotation, 'image', idNew.getValue());
end

client.closeSession();


%%
function I3 = contrastIncrease(image)

    I = image;
    background = imopen(I,strel('disk',15));

    I2 = I - background;

    I3 = imadjust(I2);

end


function bw = binarizeImage(image)
    
    bw = imbinarize(image);
    bw = bwareaopen(bw, 10)*255;

end
