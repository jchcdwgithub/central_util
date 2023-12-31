import pandas as pd
import os
import yaml
from pycentral.configuration import Devices, Groups
from pycentral.base import ArubaCentralBase
from pycentral.monitoring import Sites

def build_serial_dictionary(grps_or_sts:list[str], serials:list[str]) -> dict[str,list[str]]:
    '''
    Creates a dictionary of group or site to serials that go in each.
    '''
    grp_or_st_to_ser = {}
    for grp_or_st,serial in zip(grps_or_sts,serials):
        if grp_or_st in grp_or_st_to_ser:
            grp_or_st_to_ser[grp_or_st].append(serial)
        else:
            grp_or_st_to_ser[grp_or_st] = [serial]
    return grp_or_st_to_ser

def associate_devices_to_sites(st_to_ser:dict[str,list[str]], central:ArubaCentralBase):
    '''
    Associates the devices to the sites according to the st_to_ser dictionary passed. Uses the ArubaCentralBase connection instance passed.
    '''
    sites = Sites()
    central_sites = ''
    try:
        print('retrieving list of sites from Central...')
        sites_resp = sites.get_sites(central)
        if sites_resp['code'] == 200:
            central_sites = sites_resp['msg']['sites']
        else:
            raise Exception(sites_resp)
    except Exception as e:
        print(f'Error retrieving sites from Central: {e}')
    site_to_id = {}
    for site in central_sites:
        site_to_id[site['site_name']] = site['site_id']
    for site in st_to_ser:
        if not site in site_to_id:
            raise Exception(f"Not able to find site {site} in Central. Check name or create site.")
    for site in st_to_ser:
        print(f'assigning devices to site {site}')
        try:
            print(f'looking up site id...')
            site_id = site_to_id[site]
        except Exception as e:
            print(f"Something went wrong looking up site_id. Make sure site is configured on Central and site name matches Central site name. {e}")    
        serials = st_to_ser[site]
        site_payload = {
            'site_id' : site_id,
            'device_type' : 'IAP',
            'device_ids' : serials
        }
        resp = central.command(apiMethod="POST",apiPath="/central/v2/sites/associations",apiData=site_payload)
        if resp['code'] == 200:
            failed = resp['msg']['failed']
            if len(failed) > 0:
                print(f"Failed to associate some devices to the site: {failed}")
            success = resp['msg']['success']
            if len(success) > 0:
                print(f'Successfully assigned devices to {site}: {success}')
        else:
            print(f'Something went wrong when trying to assign devices to site: {resp}')
            print('Continuing to next site...')

def update_ap_settings(central:ArubaCentralBase, ap_serial:str, ap_settings:dict) -> dict:
    '''
    Update AP setting based on serial number.
    The ap_settings dictionary has possible keys:
        hostname: str
        ip_address: str
        zonename: str
        achannel: str
        atxpower: str
        gchannel: str
        gtxpower: str
        dot11a_radio_disable: bool
        dot11g_radio_disable: bool
        usb_port_disable: bool
    '''
    path = f'/configuration/v2/ap_settings/{ap_serial}'
    resp = central.command(apiMethod="POST", apiPath=path, apiData=ap_settings)
    return resp

def name_devices(device_serials:list[str], device_names:list[str], central:ArubaCentralBase):
    '''
    Name the devices a according to the two columns device_serials and device_names. Uses the central connection instance for API calls.
    '''
    aps_named = 0
    total_aps = len(device_names)
    for device_serial,device_name in zip(device_serials,device_names):
        ap_settings = {
            'hostname':device_name,
            'ip_address': "",
            'zonename' : '',
            'achannel' : '',
            'atxpower' : '',
            'gchannel' : '',
            'gtxpower' : '',
            'dot11a_radio_disable' : False,
            'dot11g_radio_disable' : False,
            'usb_port_disable' : False
        }
        if device_name != '':
            print(f'naming ap {device_name}')
            resp = update_ap_settings(central,device_serial,ap_settings)
            if not resp['code'] == 200:
                print(f'Error naming AP {device_name}. {resp}')
            else:
                aps_named += 1
    print(f'renamed {aps_named} out of {total_aps}')

def move_devices_to_group(grp_to_ser:dict[str,list[str]],central:ArubaCentralBase):
    '''
    Moves the devices to the respective groups according to the grp_to_ser dictionary. Uses the ArubaCentralBase instance for connection.
    '''
    devices = Devices()
    groups = Groups()
    try:
        print('Retrieving groups from Central...')
        resp = groups.get_groups(central)
        if not resp['code'] == 200:
            raise Exception(f"Error getting groups from Central:{resp}")
        central_groups = set() 
        list_of_groups = resp['msg']['data']
        #Calling get_groups returns a list of list of groups i.e. {'msg': 'data': [[group1], [group2],...]}
        for group_list in list_of_groups:
            central_groups.add(group_list[0])
        for grp in grp_to_ser:
            if not grp in central_groups:
                raise Exception(f"Groups {grp} not found in Central. Check name or create group.")
        for grp in grp_to_ser:
            grp_devices = grp_to_ser[grp]
            print(f'moving devices to group {grp}')
            resp = devices.move_devices(central,grp,grp_devices)
            if not resp['code'] == 200:
                print(f'Error moving devices to group {grp}. Continuing...')
            else:
                print(f'Successfully moved devices to {grp}')
    except Exception as e:
        print(f"Something went wrong: {e}")

def main():
    try:
        with open('info.yml', 'r') as yf:
            file_contents = yf.read()
            yml_info = yaml.safe_load(file_contents)
            if not 'data_file' in yml_info:
                raise Exception("yml file must have a data_file defined.")
            else:
                data_file = yml_info['data_file']
                extension = data_file.split('.')[-1]
                df = ''
                username = ''
                password = ''
                client_id = ''
                client_secret = ''
                customer_id = ''
                site_to_serials = {}
                group_to_serials = {}
                if 'csv' == extension:
                    df = pd.read_csv(data_file)
                elif 'xlsx' == extension:
                    df = pd.read_excel(data_file)
                else:
                    raise Exception("Only csv and xlsx data_file formats are supported.")
                if 'serial' in df:
                    serials = list(df['serial'].values)
                else:
                    raise Exception("No serial column found. A serial column with device serials must be in the data file.")
                if 'site' in df:
                    file_sites = list(df['site'].values)
                    site_to_serials = build_serial_dictionary(file_sites,serials)
                if 'group' in df:
                    file_groups = list(df['group'].values)
                    group_to_serials = build_serial_dictionary(file_groups,serials)
            if not 'username' in yml_info:
                if os.getenv("CENTRAL_USERNAME"):
                    username = os.getenv("CENTRAL_USERNAME")
                else:
                    raise Exception("yml file must have a username defined or this value must be in an environment variable named CENTRAL_USERNAME.")
            else:
                username = yml_info['username']
            if not 'password' in yml_info:
                if os.getenv("PASSWORD"):
                    password = os.getenv("PASSWORD")
                else:
                    raise Exception("yml file must have a password defined or this value must be in an environment variable named PASSWORD.")
            else:
                password = yml_info['password']
            if not 'client_id' in yml_info:
                if os.getenv("CLIENT_ID"):
                    client_id = os.getenv("CLIENT_ID")
                else:
                    raise Exception("yml file must have a client_id defined or this value must be in an environment variable named CLIENT_ID.")
            else:
                client_id = yml_info['client_id']
            if not 'customer_id' in yml_info:
                if os.getenv("CUSTOMER_ID"):
                    customer_id = os.getenv("CUSTOMER_ID")
                else:
                    raise Exception("yml file must have a customer_id defined or this value must be in an environment variable named CUSTOMER_ID.")
            else:
                customer_id = yml_info['customer_id']
            if not 'client_secret' in yml_info:
                if os.getenv("CLIENT_SECRET"):
                    client_secret = os.getenv("CLIENT_SECRET")
                else:
                    raise Exception("yml file must have a client_secret defined or this value must be in an environment variable named CLIENT_SECRET.")
            else:
                client_secret = yml_info['client_secret']
            if 'base_url' in yml_info:
                base_url = yml_info['base_url']
            elif os.getenv("BASE_URL"):
                base_url = os.getenv("BASE_URL")
            else:
                base_url = 'https://apigw-uswest4.central.arubanetworks.com'
                print(f"base_url not explicitly defined. Using {base_url} for API calls.")
            central_info = {
                'username' : username,
                'password' : password,
                'client_id' : client_id,
                'client_secret' : client_secret,
                'customer_id' : customer_id,
                'base_url' : base_url
            }
            print('Logging into Central...')
            central = ArubaCentralBase(central_info)
            if 'group' in df:
                move_devices_to_group(group_to_serials,central)
            if 'site' in df:
                associate_devices_to_sites(site_to_serials, central)
            if 'name' in df:
                names = list(df['name'].values)
                name_devices(serials, names, central)
    except Exception as e:
        print(f'something went wrong: {e}')

if __name__ == "__main__":
    main()