import json
import asyncio
import websockets
import stardog
from pathlib import Path
import uuid
from rdflib.plugins.sparql import prepareQuery
from rdflib import Graph, URIRef, Namespace

#Setup connection details
conn_details = {
  'endpoint': 'https://server.ip.rwth-aachen.de/ioc/stardog',
  'username': 'PDP_USER_DEBUG',
  'password': 'PDPDEBUG'
}

#For every Converted IFC that you have as .ttl file, this needs to be done:
#for ........

#first add the converted File to the database, not linked yet
#filename of the ttl, this should be the GUID of the converted File
script_path = Path(__file__, '..').resolve()
filename = "hereShouldBeAguid_1234.ttl"
with open(script_path.joinpath(filename)) as f:
    lines = f.readlines()

# some dumb stuff here
prefix_lines = [line for line in lines if line.startswith("@prefix")]
prefix_lines = [line.replace(".\n", "\n") for line in prefix_lines]
prefix_lines = ["PREFIX" + line[7:] for line in prefix_lines]
data_lines = [line for line in lines if not line.startswith("@prefix")]
addQuery = "\n".join(prefix_lines) + "\n INSERT DATA {\n" + "".join(data_lines) +"\n }"

#There is a bug in forward for INSERTING, so you have creds for stardog and INSERT directly.
print (addQuery)
with stardog.Connection('PDP_TS_01', **conn_details) as conn:
    conn.begin()
    conn.update(addQuery)
    conn.commit()

#your new element is now on the server, but its not connected to anything. Therefore we need a process


#create a new GUID for the process
elementName = filename.split(".")[0]
# this is the filename you load without .ttl , this should be a GUID
GUID =  str(uuid.uuid5(uuid.NAMESPACE_DNS,elementName))
processGUID = "<http://linkedbuildingdata.net/ifc/resources20221218_161821/Process_"+GUID+">"
#create the stuff you need to add
subProcessName = "CuttingProcess_"+elementName

#note that the where clause is first. here the top part searches for the old wall while the bottom part searches for the new proxy element we just added
createProcessAndLinkQuery = f"""
                    PREFIX schema: <http://schema.org/>
                    PREFIX seas:  <https://w3id.org/seas/>
                    PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
                    PREFIX ifc: <http://standards.buildingsmart.org/IFC/DEV/IFC4/ADD1/OWL#>
                    PREFIX ioc: <http://w3id.org/ioc#>

                    INSERT {{
                        {processGUID} a ioc:Process;
		                    ioc:hasProcessName "{subProcessName}";
		                    ioc:hasInputElement ?Wall;
                            ioc:hasOutputElement ?NewElement;
		                    ioc:hasParentProcess ?TopProcess.
                            }}
                    WHERE {{
                        ?TopProcess ioc:hasInputElement ?Wall .
                        ?Wall ifc:globalId_IfcRoot ?RootID .
                        ?RootID <https://w3id.org/express#hasString> "2XR7ZJ3vvFfQ0vDTZymAWo" .

                        ?NewElement ifc:globalId_IfcRoot ?RootID2 .
                        ?RootID2 <https://w3id.org/express#hasString> "{elementName}" .
                        }}
        """
print (createProcessAndLinkQuery)
#Now we add the process and its interconnection to the triple store
with stardog.Connection('PDP_TS_01', **conn_details) as conn:
    conn.begin()
    conn.update(createProcessAndLinkQuery)
    conn.commit()

#now for the last part we use the WEB-API again to create the processStatus
#the initial status is "open", the same command can be used to set it "running" and "done"
#we need the processGuid form above to state which one we want to set

desired_status="open"

async def get_update():
    uri = "wss://server.ip.rwth-aachen.de:443/ioc/ws"
    async with websockets.connect(uri) as websocket:
        usernameinput = "PDP-2023"
        passwordinput = "KxeCZD56L6"
        databaseinput = "PDP_TS_01"


        # This message needs to be triggered once for connection
        Connect_message = json.dumps({"header": {"name": usernameinput, "password": passwordinput},
                                      "body": {"database": databaseinput,
                                               "endpoint": "https://server.ip.rwth-aachen.de/ioc/stardog"}})
        await websocket.send(Connect_message)
        response = await websocket.recv()
        print("Received response: ", response)

        #Need to get rid of the <> , this is dumb btw
        processGUID_ = processGUID[1:]
        processGUID_ = processGUID_[:-1]
        # This is the Query Message
        Status_message = json.dumps({"header": {"name": usernameinput, "password": passwordinput},
                                   "body": {"req": "setProcessStatus", "param": {"processId": processGUID_, "status": desired_status}}})

        await websocket.send(Status_message)
        print("Sent message: ", Status_message)

        response = await websocket.recv()
        print("Received response: ", response)

asyncio.run(get_update())