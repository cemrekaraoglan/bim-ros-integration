#Import of the necessary packages
import json
import asyncio
import websockets
from pathlib import Path
from rdflib.plugins.sparql import prepareQuery
from rdflib import Graph, URIRef, Namespace
import stardog
import json
import os
import re

#Setup connection details
conn_details = {
  'endpoint': 'https://server.ip.rwth-aachen.de/ioc/stardog',
  'username': 'PDP_USER_DEBUG',
  'password': 'PDPDEBUG'
}

# read the contents of the file "PDP_TS_01.ttl"
script_path = Path(__file__, '..').resolve()
with open(script_path.joinpath("PDP_TS_01.ttl")) as f:
    lines = f.readlines()

# find all lines that start with "@prefix"
prefix_lines = [line for line in lines if line.startswith("@prefix")]

# remove the dots at the end of the prefix lines
prefix_lines = [line.replace(".\n", "\n") for line in prefix_lines]

# replace "@prefix" with "PREFIX" in each element of the list
prefix_lines = ["PREFIX" + line[7:] for line in prefix_lines]

# remove the prefix lines from the original list of lines
data_lines = [line for line in lines if not line.startswith("@prefix")]

# join the prefix lines and the data lines
querystring = "\n".join(prefix_lines) + "\n INSERT DATA {\n" + "".join(data_lines) +"\n }"


#Print how query looks in the end            
print (querystring)

#Delete Everything
deletestring = """DELETE WHERE{?a ?b ?c.}"""
with stardog.Connection('PDP_TS_01', **conn_details) as conn:
    conn.begin()
    conn.update(deletestring)
    conn.commit()

#Send query to triple store 
with stardog.Connection('PDP_TS_01', **conn_details) as conn:
    conn.begin()
    conn.update(querystring)
    conn.commit()
    
#Print Json
print("done")

