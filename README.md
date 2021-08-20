# Incident ranking function

This script takes a given TTI_External output file from given country (from this address: http://prod-orlandodatastore-vip.traffic.tt3.com:8080/ui/) and ranks importance of every message 
based on made up car position and series of conditions, to in the end produce shorter .xml, limited to given number of most important
messages from car position perspective.
Both original files and ranked, limited files can be visualized in Cancun (https://cancun.tomtomgroup.com/)

## 1. Setup

### 1.1. Script setup (when working with PyCharm on Win 10):
Download and install:
* Python in at least 3.8 version (script written in [3.9.2](https://www.python.org/downloads/release/python-392/))
* Git version control system: https://git-scm.com/download/win

**In CMD:**  
Confirm installed python and git:  
`python --version` / `py --version`  
`git --version`

If versions are not displayed then add those lines to Environment variables table (if you used default install directories):  
C:\Users\\\<username\>\AppData\Local\Programs\Python\Python39\Scripts  
C:\Users\\\<username\>\AppData\Local\Programs\Python\Python39  
C:\Program Files\Git\cmd  
C:\Program Files\Git\bin\git.exe

If new to GIT, then set up your credentials with:  
`git config --global user.name "<Name> <Surname>"`  
`git config --global user.email <name>.<surname>@tomtom.com`

Change directory to that in which you want folder with Incident Ranking Function, e.g.:  
`cd PycharmProjects` (being in the C:\Users\\\<username\>\ already)

Clone github repo:  
`git clone https://github.com/JakubGrzywala-TomTom/Incident_ranking_function.git`

**In file explorer:**  
Rename cloned folder (top one) randomly, can be "Incident_ranking_function2" or whatever.

**Open PyCharm:**  
Create new PyCharm Project called the same as cloned repo originally -> "Incident_ranking_function".  
Project should be with new virtual environment (Virtualenv). Set up location of venv the same as whole project.  
Base interpreter: choose python 3.9 (3.8 at least).  
Wait till project setup is complete.

**In file explorer:**  
Go to renamed, cloned folder.  
Cut it's content together with hidden files and folders.  
Paste all cut files into PyCharm project directory (overwrite all existing if asked).  
Delete cloned folder.

**Move to PyCharm:**  
Make sure that new files are visible in "project" tab.  
Make sure that on upper ribbon there is "Git" 3rd from right (should be detected).  
In "Terminal" (narrow ribbon on the bottom of screen in PyCharm) if needed activate virtual environment (write: `Scripts\activate`). When virtual env is activated then before path in terminal there should be project's name in parentheses, in this case: `(Incident_ranking_function) C:\Users\<username>\etc`  
Install needed python libraries by writing in project's root: `pip install -r requirements.txt`

**Modification in xml standard library**  
In PyCharm project:
* In "Project" tab (left side) find and open "External Libraries" -> "Lib" -> "xml" -> "etree" -> "ElementTree.py"
* comment out ("#" before line) two first lines in register_namespace function (line 1006 and 1007) in xml.etree.ElementTree to be able to register xml namespaces called "ns*"
* PyCharm should save file itself  

### 1.2. Script takes as input:
* One of TTI output .xml files from [Orlando Datastore](http://prod-orlandodatastore-vip.traffic.tt3.com:8080/ui/).   
* Input.json, which is collection of info needed for ranking messages, e.g.:
    * current car position (ccp)
    * inner radius around ccp
    * outer radius around ccp
    * file name (with or without ".xml") of TTI file that needs to be processed
    * limit of messages in processed file
    * score dictionaries that hold condition and value that message should receive for it

>Both files need to be placed in one of "OUTPUT" subfolders. There can be many folders with different configurations, they can be named anyhow, but the name has to be indicated after "-f" flag during starting script:
> 
>`py incident-ranking-function -f output\<your-folder-name>`

### 1.3. Starting script (after setting up what it needs):
* TTI output .xml and input.json configuration file in one of "OUTPUT" subfolder
* in command prompt (cmd/powershell) in project's root folder write 
  * `.\Scripts\activate` to activate Python virtual environment with libraries and modifications described in 1.2. 
  * `py incident_ranking_function.py -f output\<your-folder-name>`
* in PyCharm just write `py incident_ranking_function.py -f output\<your-folder-name>` in Terminal in open project
(of course PyCharm configurations can be used, using that you will be asked for `output\<your-folder-name>`, filename completion doesn't work there, so it's less convenient)
* !!! configuration .json file has to be in root folder  

___

## 2. TTI .xml tag's values used for calculating scores
TTI .xml consists of metadata and set of <trafficMessage>, which hold tags used below.

### 2.1. Incident coordinates
1. From \<location\> -> \<locationGeneral\> -> \<boundingBox\> ->:
    * either \<LowerLeft\>
    * or \<UpperRight\> (one which is closer to ccp), if n/a
2. From \<location\> -> \<locationDescription\> -> \<startLocation\>, if n/a
3. From \<location\> -> \<OpenLR\> -> \<XMLLocationReference\> ->:
    * \<LineLocationReference\> -> \<LocationReferencePoint\> -> \<Coordinates\>
    * \<PointLocationReference\> -> \<PointAlongLine\> -> \<LocationReferencePoint\> -> \<Coordinates\>

Outcome will be:
* tuple of two tuples of lat & lon, set closer to ccp will be taken for distance calculation
* tuple of lat & lon
* ("Error", "Error") tuple, if coordinates not found

### 2.2. Event info
From \<messageManagement\> -> \<contentType\>

Outcome will be string containing:
* event name
* "Error" if event name not found

### 2.3. Jam priority
From \<event\> -> \<eventDescription\> -> \<alertCCodes\> -> \<eventCode\>

Outcome will be string containing:
* jam priority
* "Error" if not found

### 2.4. FRC info
From \<location\> -> \<locationGeneral\> -> \<functionalRoadClass\>

Outcome will be string containing:
* frc info
* "Error" if not found

### 2.5. Delay info
From \<event\> -> \<effectInfo\> -> \<absoluteDelaySeconds\>

Outcome will be integer:
* delay in seconds
* -100, means that message did not have a delay info, most probably completely correctly

### 2.6. Expiry info
From \<messageManagement\> -> \<expiresIn\>

Outcome will be float:
* amount of days in which message expires,
* -100 if amount was not found (but for no there was no such case, and amount was always positive)

### 2.7. Start time
From \<event\> -> \<tmcEvent\> -> \<startTimeUTC\>

Outcome will be string:
* start datetime of message
* "Error" if not found (active messages usually (or in every case) do not have startTimeUTC)


___

## 3. Score types
### 3.1. Filtering function
Decides either message should be taken into account.
* in inner radius EXCLUDES messages with ceratin FRCs given on a list "inn_r" (delimited with ",", no space)
* in outer radius EXCLUDES messages with ceratin FRCs given on a list "out_r"
* outside of outer radius: INCLUDES only messages given on a "3rd_r_frcs" and  "3rd_r_events" lists (e.g. only CLOSURES on low frcs should be left)
* ADDITIONALLY:
* EXCLUDES messages with event type listed in "excluded_completely" parameter
* EXCLUDES messages that have a startTimeUTC attribute and it is greater than file creationTimeUTC (from metadata), which means they are not active, future events

Outcome: boolean, decides whether to:
* filter out a message (True)
* or not (False).

### 3.2. Distance score
Formula for the score is: 1 - distance between ccp and incident / outer radius.
Output value ranges between 1 (highest score) until -X (largest registered was -4.7, depends on how large the country is).

Outcome: float, either with:
* distance score
* or -100 when distance could not been calculated. 

### 3.3. Radius boost score
Output ranges from 1 to 0.
3 levels which can receive different scores:
* Messages within certain radius (4 km at the moment, can be any integer up to inner radius, has to be put between " ")
* Within inner radius
* Outside inner radius

Outcome: float, either with:
* radius boost score value connected to certain category in input .json file 
* or -100 when distance could not been calculated. 

### 3.4. Event score
Output ranges from 1 to 0.
Different events receive different scores, e.g.:
* CLOSURES 1
* ROADWORKS 0.6
* etc.

Outcome: float, either with:
* 0 when event type unlisted (or listed with typo) in input .json file
* score value connected to certain category in input .json file
* -100 if getting the event info from .xml was not possible

In the future score will be enhanced with treating Jams depending on their severity.

### 3.5. FRC score
Output ranges from 1 to 0.
Different FRCs receive different scores, e.g.:
* FRC1 1
* FRE2 0.9
* etc.

Outcome: float, either with:
* 0 when frc type unlisted (or listed with typo) in input .json file
* score value connected to certain category in input .json file
* -100 if getting the event info from .xml was not possible

### 3.6. Delay score
Output ranges from 1 to 0.
Bigger the delay, more points the message gets.

Outcome: float, either with:
* 1 when excluded from counting delay score (on "excluded_from_delay_score" in input .json)
* 0 if event type is not excluded and does not have a delay either
* score value connected to certain category in input .json file

### 3.7 Weights
Weights for testing different balance between 3.2 - 3.6 scores (Filtering function works first, independently)
