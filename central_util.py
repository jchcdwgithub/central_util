import pandas as pd
import yaml
from pycentral.monitoring import Sites
from pycentral.base import ArubaCentralBase

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
                site_to_serials = {}
                if 'csv' == extension:
                    df = pd.read_csv(data_file)
                elif 'xlsx' == extension:
                    df = pd.read_excel(data_file)
                else:
                    raise Exception("Only csv and xlsx data_file formats are supported.")
                serials = list(df['serial'].values)
                file_sites = list(df['site'].values)
                for site,serial in zip(file_sites,serials):
                    if site in site_to_serials:
                        site_to_serials[site].append(serial)
                    else:
                        site_to_serials[site] = [serial]
            if not 'username' in yml_info:
                raise Exception("yml file must have a username defined.")
            if not 'password' in yml_info:
                raise Exception("yml file must have a password defined.")
            if not 'client_id' in yml_info:
                raise Exception("yml file must have a client_id defined.")
            if not 'customer_id' in yml_info:
                raise Exception("yml file must have a customer_id defined.")
            if not 'client_secret' in yml_info:
                raise Exception("yml file must have a client_secret defined.")
            if 'base_url' in yml_info:
                base_url = yml_info['base_url']
            else:
                base_url = 'https://apigw-uswest4.central.arubanetworks.com'
            central_info = {
                'username' : yml_info['username'],
                'password' : yml_info['password'],
                'client_id' : yml_info['client_id'],
                'client_secret' : yml_info['client_secret'],
                'customer_id' : yml_info['customer_id'],
                'base_url' : base_url
            }
            print('Logging into Central...')
            central = ArubaCentralBase(central_info)
            sites = Sites()
            central_sites = ''
            try:
                print('retrieving list of sites from Central...')
                sites_resp = sites.get_sites(central)
                if sites_resp['code'] == 200:
                    central_sites = sites_resp['msg']
                else:
                    raise Exception(sites_resp)
            except Exception as e:
                print(f'Error retrieving sites from Central: {e}')
            site_to_id = {}
            for site in central_sites:
                site_to_id[site['site_name']] = site['site_id']
            for site,serials in site_to_serials:
                print(f'assigning devices to site {site}')
                try:
                    print(f'looking up site id...')
                    site_id = site_to_id[site]
                except Exception as e:
                    print(f"Something went wrong looking up site_id. Make sure site is configured on Central and site name matches Central site name. {e}")    
                resp = sites.associate_devices(central,site_id,'IAP',serials)
                if resp['code'] == 200:
                    print(f'Successfully assigned devices to {site}')
                else:
                    print(f'Something went wrong when trying to assign devices to site: {resp}')
                    print('Continuing to next site...')
    except Exception as e:
        print(f'something went wrong: {e}')
if __name__ == "__main__":
    main()