import json
import sys
from jinja2 import Environment, PackageLoader
from restClass import restCalls


def render_config(update_json):
    """Take a exa command and translate it into yang formatted JSON
    :param update_json: The exa bgp string that is sent to stdout
    :type update_json: str

    """

    #import pdb
    #pdb.set_trace()
    if 'announce' in update_json['neighbor']['message']['update']:
        prefixes = update_json['neighbor']['message']['update']['announce']['ipv4 unicast'].values()
        next_hop = update_json['neighbor']['message']['update']['announce']['ipv4 unicast'].keys()[0]
        # set env variable for jinja2
        env = Environment(loader=PackageLoader('edit_rib', 'templates'))
        template = env.get_template('static.json')
        rib_announce(template.render(next_hop=next_hop, data=prefixes))
    elif 'withdraw' in update_json['neighbor']['message']['update']:
        prefixes = update_json['neighbor']['message']['update']['withdraw']['ipv4 unicast'].keys()
        current_config = get_config()
        partial_config = current_config['Cisco-IOS-XR-ip-static-cfg:vrf-prefixes']['vrf-prefix']
        for whole_dictionary in partial_config:
            current_prefix = whole_dictionary.get('prefix')
            for exa_prefix in prefixes:
                exa_prefix, pre_length = exa_prefix.split('/')
                if exa_prefix == current_prefix:
                    partial_config.remove(whole_dictionary)
                    break
        current_config['Cisco-IOS-XR-ip-static-cfg:vrf-prefixes']['vrf-prefix'] = partial_config
        rib_withdraw(current_config)


def rib_announce(rendered_config):
        """Make REST call to change the rib table
            This script will need the file of network commands to be filled
            We should trigger this script every time a change is made to the
            file.
        """
        rest_object = restCalls('lisa', 'timCp4tn6m!', '10.200.96.52:2580')
        response = rest_object.patch(rendered_config)
        #print response.raise_for_status()
        print response.status_code


def rib_withdraw(new_config):
    rest_object = restCalls('lisa', 'timCp4tn6m!', '10.200.96.52:2580')
    response = rest_object.put(new_config)
    print response.status_code


def get_config():
        rest_object = restCalls('lisa', 'timCp4tn6m!', '10.200.96.52:2580')
        response = rest_object.get('Cisco-IOS-XR-ip-static-cfg:router-static/default-vrf/address-family/vrfipv4/vrf-unicast/vrf-prefixes/vrf-prefix')
        if not response.raise_for_status():
            return response.json()
        else:
            response.raise_for_status()


def update_watcher():
    """Watches for BGP updates from neighbors"""
    while True:
        raw_update = sys.stdin.readline().strip()
        update_json = json.loads(raw_update)
        if update_json['type'] == 'update':
            render_config(update_json)
            #update = sys.stdin.readline().strip()


'''
def tester():
    with open('/vagrant/rest_calls/json.dataw', 'r') as f:
        fr = f.read()
        update_json = json.loads(fr)
        # A seperate RIB table change will be made for each update
        if update_json['type'] == 'update':
            render_jinja(update_json)
'''


if __name__ == "__main__":
    update_watcher()
