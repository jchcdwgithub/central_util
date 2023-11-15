# central_util
This script reads from a csv or xlsx file and assigns the devices in that file to the sites and/or groups defined in the file.
## Installation
Pull the script from github or download it as a zip file:
`git clone https://github.com/jchcdwgithub/central_util.git`

Run pip to install the libraries from the requirements.txt file:
`python -m pip install -r requirements.txt`

Note that you might need to run python3 and/or pip3 instead.

## Data File Format
For either the csv or xlsx file, there are three columns that might be defined:
1. serial
2. site
3. group

The serial column must be defined and either the site and/or the group columns can be added for each device. If both are defined
the script will associate the devices to the site(s) and move the devices to the group(s). The data file must be defined in an info.yml
file that should be in the same directory as the script.
```
---
data_file: mydata.xlsx
```

## Providing Central Credentials
To interact with the Central API several pieces of information must be provided to the script:
1. client_id
2. client_secret
3. customer_id
4. username
5. password

These can all be added to a yml file named info.yml which must be in the same directory as the script:
```
---
data_file: mydata.xlsx
username: john.smith@cdw.com
password: cdw123123
client_id: some_long_string
client_secret: some_long_string
customer_id: some_long_string
```

These five parameters can also be stored as environment variables with the following names:
1. CLIENT_ID
2. CLIENT_SECRET
3. CUSTOMER_ID
4. CENTRAL_USERNAME
5. PASSWORD

## Usage
After creating the info.yml file and providing the previously mentioned credentials, run the script:
`python central_util.py`