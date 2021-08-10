# Incident ranking function #

This script takes a given TTI_External (or other) output file from given country (from this address: http://prod-orlandodatastore-vip.traffic.tt3.com:8080/ui/) and ranks importance of every message in there 
based on made up car position and series of conditions, to in the end produce short list, limited to given number of messages, of most important
messages from car position perspective.
Both original files and ranked, limited files can be visualized in Cancun (https://cancun.tomtomgroup.com/)

### Script takes as input: ###
* one of TTI output .xml files that need to be placed in "TTI_XMLs" folder
* input.json, which is collection of info needed for ranking messages, e.g.:
    * current car position (ccp)
    * inner radius around ccp
    * outer radius around ccp
    * file name (with or without ".xml") of TTI file that needs to be processed
    * limit of messages in processed file
    * score dictionaries that hold condition and value that message should receive for it
    
### Script needs: ###
* Python in at least 3.8 version (script written in [3.9.2](https://www.python.org/downloads/release/python-392/))
* `git clone https://github.com/JakubGrzywala-TomTom/Incident_ranking_function`
* `cd Incident_ranking_function`
* pandas and geopy external libraries installed (both in requirements.txt) by `pip install -r requirements.txt`
* **modification in xml standard library** (commenting out/removing two first lines in register_namespace function (line 1006 and 1007) in xml.etree.ElementTree) for ability to register xml namespaces called "ns*"

### Starting script (after setting up what it needs) ###
* TTI output .xml file in "TTI_XMLs" folder
* .json configuration file (called as you like)
* in command prompt (cmd/PyCharm terminal/whatever) in project's root folder write `py incident_ranking_function.py -f <your_configuration_file>.json`
(of course PyCharm configurations can be used, using that you will be asked for input .json file name)
* !!! configuration .json file has to be in root folder  
