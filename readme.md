
# ROS BIM INTEGRATION

ROS-BIM is a tool focuses on dynamic integration between ROS and IfcOwl ontology. The package imports the geometry of wall objects including the opening element which is inherited from window and door objects from the WebServer of IP, panelizes wall objects regarding standard gypsum board size and opening element edges. Later this panel geomety pushed into server as a element proxy and to ROS environment as a message to determine required gypsum board cut sizes. Then the robot movement is simulated and can be visualized with RVIZ. As the gypsum boards are being cut, ROS publishes a message about the fabrication process, the process has not started, the cut has started or cut has finished. This message goes to Server and marks the panels according to their fabrication status. 

## Dependencies
- ROS2 Humble
- Ifcopenshell
- PythonOCC
- Numpy
- Stl
- Scipy


# How to Install
Open the terminal and go to your ros2 workspace, then to source:
```
cd ~/<your_ros_ws>/src
```
Clone the repository: 

```
git clone -b <branch> <address>
```
Go to your <your_ros_ws> and run this commands to ros2 environment acknowledge your package:

```
cd ~/<your_ros_ws>
```

# How To Start

## Creating the Geometry from IFCOWL to IFC
```
conda env create -f myenv.yml
cd ~/<your_ros_ws>/src/slicer/slicer/wall_cut
python wall_cut.py
```
## Running the ROS2 Package
Build your package:
```
cd ~/<your_ros_ws>/
colcon build --packages-select slicer
```

Go to script folder:
```
cd <your_ros_ws>src/slicer/script
```
run the code

```
./pkg_launch.sh

```
to configure joystick 
```
ros2 topic echo joy
```

## Use of the Package

After the code is running and RVIZ window is open, you need to press button[0], usually the button with 1 on it to start cutting process. If this does not work run the joystick configuration code on terminal and determine the correct button. After you press the button, cut will start, cutting of gypsum board with robot will be visualized on RVIZ and update the server model on fabrication status of panels. 


## Configuration
In the package folder under config you can adapt the speed of the joints by changing scale factors. 
```
    scale_factor_joint1 : 0.02
    scale_factor_joint2 : 0.001
    scale_factor_joint3 : 0.02
```



## Query 

To carry out slicing processes dynamically and access&query data, the model is uploaded to the WebSocket Server, which is out of the scope of this project and provided by IP Chair. Model has been converted from IFC file to IFCOwl with the IFC2OWL repository provided by IP Chair, and pushed to the server. With the python script including username, password and database, IFCOwl model can be queried, data can be inserted or be deleted.

Query Example:

```  
reqinput = str('''
        PREFIX IFC: <http://standards.buildingsmart.org/IFC/DEV/IFC4/ADD1/OWL#>
        SELECT ?wall 
        WHERE {
            wall a IFC:IfcWall .
        }
    ''')

```
(https://www.w3.org/TR/rdf-sparql-query/)

### 1 - Query Geometry from the Server

In order to get the dimensions for the paneling process, ifcWall and related IfcOpeningElement geometry are queried and converted into obj format to use with ifcOpenShell.

Query Geometry:
```  
SELECT ?Opening ?OpeningGeo ?Wall ?WallGeo 
                    WHERE {
                        ?Opening geo:hasGeometry ?GeoN .
                        ?GeoN fog:asObj_v3.0-obj ?OpeningGeo .
                        ?Opening a ifc:IfcOpeningElement .

                        ?Wall geo:hasGeometry ?WallN .
                        ?Wall owl:sameAs ?ifcWall .
                        ?WallN fog:asObj_v3.0-obj ?WallGeo .
                        ?ifcWall a ifc:IfcWall .

                        ?Wall <https://linkebuildingdata.org/LBD#containsInBoundingBox> ?Opening .

                        }
```

### 2 - Linking the Fabrication Status

To be able to link fabrication status to IFCOwl model,at the beginning the project, parent "Process" class  inserted with SPARQL linked to related IfcWall and push to the server. "Process" class is Internet of Construction Onthology [IOC] (https://ip.pages.rwth-aachen.de/ioc/core/). Special thanks to Lukas Kirner from Individualized Production chair at RWTH Aachen University.


Insert Process:
```
INSERT{ <http://linkedbuildingdata.net/ifc/resources20221218_161821/TestProcess_01> ioc:hasInputElement ?Wall;
        ioc:hasProcessName "CuttingTest01".
    
                                                                                    }
WHERE {
        ?Wall ifc:globalId_IfcRoot ?RootID.
        ?RootID <https://w3id.org/express#hasString> "2XR7ZJ3vvFfQ0vDTZymAWo".
    }
```




## Panelization
The wall elements that we have the geometry of it including opening elements are panelized into elements according to standard gypsum board size and opening edges. OpenCascade and IfcOpenShell used to create element proxy for this wall elements to represent panelized walls, then converted to IfcOwl format with converter

## Robot 
Currently the robot is composed of three links, each moving either in X, Y or Z axis. When a message is received from the joystick, it moves in the stated direction to cut the gypsumboard in the stated dimension. 


## Updating the Server

Exported IFC file during panelization process is named as "guid.ifc" (with the guid number) for each component. IFC2OWL repository converts IFC files to the TTL files and stores it iteratively. IFCOwl files need to be pushed to the server. Before pushing a new panel to the server, the model in server is replace with "PDP_TS_01.ttl" which is unmodified file to avoid creating an overlapping Process class by using "pdp_Reset.py". 

After replacing model, actual IFCOwl file is pushed to the server by linking with the parent "Process" and creating subprocesses related to it by using "pdpSCRIPT.py". Subprocesses ("isReady", "isFinished", "isCancelled") are created as a Boolean which should be switched to True or False according to the message coming from ROS.


Creating Subprocesses:
```
#create a new GUID for the process
elementName = filename.split(".")[0]
# this is the filename you load without .ttl , this should be a GUID
GUID =  str(uuid.uuid5(uuid.NAMESPACE_DNS,elementName))
processGUID = "<http://linkedbuildingdata.net/ifc/resources20221218_161821/Process_"+GUID+">"
#create the stuff you need to add
subProcessName = "CuttingProcess_"+elementName
```
Inserting Subprocesses:
```
INSERT{ 
                        {statusinput} a ioc:Process;
		                    ioc:hasProcessName "CuttingTest01" .
		                    ioc:hasInputElement ?Wall;
		                    ioc:hasParentProcess ?Process;
		                    ioc:hasStatus <http://w3id.org/ioc#isReady> .
		                    ioc:hasStatus <http://w3id.org/ioc#isStarted> .
		                    ioc:hasStatus <http://w3id.org/ioc#isFinished> .                   
		                    ?Process ioc:hasOutputElement <NEWELEMENT> .
```

## Viewing the server

Updates on server can be visualized with Rhino/Grasshopper Plugin. Required plugins are provided in Slicer/Server_Visualization/Libraries folder, IOC plugin is provided by IP Chair RWTH Aachen, the others are fetched from website [Food 4 Rhino](https://www.food4rhino.com/en). After running Grasshopper go to 

File > Special Folders > Components Folder 

then copy the libraries folder here. After restarting Grasshopper you can start the grashopper code and see the process over the BIM Model. 

