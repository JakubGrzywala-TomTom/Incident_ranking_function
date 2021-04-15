<h1>Incident ranking function</h1>

This script takes a given TTI_External (or other) output file from given country and ranks importance of every message in there 
based on made up car position and series of conditions, to in the end produce short list, limited to given number of messages, of most important
messages from car position perspective.

Script takes as input:
* one of TTI .xml files that need to be placed in "TTI_XMLs" folder
* input.json, which is collection of info needed for ranking messages, e.g.:
    * current car position (ccp)
    * inner radius around ccp
    * outer radius around ccp
    * file name (without ".xml") of TTI file that needs to be processed
    * limit of messages in processed file
    * score dictionaries that hold condition and value that message should receive for it
    

Script needs:
* Python in at least 3.8 version (script written in 3.9.2)
* pandas and geopy external libraries installed (both in requirements.txt)
* **modification in xml standard library** (commenting out/removing two first lines in register_namespace function (line 1006 and 1007) in xml.etree.ElementTree) for ability to register xml namespaces called "ns*"
