#!/usr/bin/env python
"""

Jeff Kala | Jose Lima
Tue Feb 19 8:59:03 AM 2019

collection of DNCM boilerplate calls

    Example:
        1) import core.dcnm_calls

            fabric_list = core.dcnm_calls.get_fabrics(connection_obj)

        2) from core.dcnm_calls import get_fabrics

            fabric_list = get_fabrics(connection_obj)


    Todo:
        * todo
"""
import json
from getpass import getpass
from .session import Session
from .utilities import time_me


def get_connection():
    """Connection handler to handle intial connection to DCNM and
       creating connection_obj and getting fabric_name

       +Checks minimun python version 3.6.x to support f-string formatting.
       SystemExit uses % format incase this file is ran in a system with no f-string support.

       Args (none)

       Returns:
        connection_obj (object)
        fabric_name (str)
    """
    import sys

    _PY3_MIN = sys.version_info[:2] >= (3, 6)
    if not _PY3_MIN:
        raise SystemExit(
            'ERROR: DCNM API package requires a minimum of Python3 version 3.6. Current version: %s'
            % ''.join(sys.version.splitlines()))
    print('\nEnter "AD" credentials for DCNM Changes\n')
    user = input('Username: ')
    password = getpass()
    base_url = input('DCNM URL ( include https:// ): ')
    base_url = base_url.strip()
    sess = Session(base_url, user, password)
    sess.login()
    sess.update_lan_creds()
    fabric_list = get_fabrics(sess)
    fabric_name = None
    while not fabric_name:
        print('\n')
        print(', '.join(fabric_list))
        print('\n')
        fabric_name = input(f'\nEnter the fabric name from list above:\n')
        if fabric_name not in fabric_list:
            print(
                'Invalid fabric name, check spelling.. name is case sensitive..'
            )
            fabric_name = None
    sess.fabric = fabric_name
    return sess


def get_fabrics(connection_obj):
    """returns a list of DCNM fabrics

        returns a list of fabrics with no duplicate names by first filtering
        through a set() before the list is created, return list(set())

        Args:

            required:
                connection_obj (Class object): DCNM connection/session object from main script

            optional:
                url (str): REST URL used to get a list of fabrics, default
                supports dcnm version 10 & 11

        Examples:
            from core.dcnm_calls import get_fabrics

            connection = Session(url, username, password)
            connection.login()

            # with default URL
            fabric_list = get_fabrics(connection)

            # with alternate url
            fabric_list = get_fabrics(connection, url='/rest/new/url')

            print(fabric_list)

        Returns:
            A list of fabrics, with no duplicates
    """
    resp = connection_obj.get(f'/rest/control/fabrics')
    # return [x['fabricName'] for x in json.loads(resp.text)]
    return [x['fabricName'] for x in resp.json()]


def get_networks(connection_obj, fabric_name):
    """ Function used to get all networks for a fabric from DCNM.
    Args:   connection_obj - is imported from main and is keeping track of the session connection to DCNM.
            fabric_name (str) name of the fabric.
    returns:
    A list of all networks from DCNM (WITHOUT DUPLICATES)
    """
    gn_url = f'/rest/top-down/fabrics/{fabric_name}/networks'
    resp = connection_obj.get(gn_url)
    data = json.loads(resp.text)
    return list({x['networkName'] for x in data})


def get_inventory(connection_obj, fabric_name):
    """ Function is used to get switch inventory for a fabric in DCNM.
    Args:   connection_obj - is imported from main and is keeping track of the session connection to DCNM.
            fabric_name (str)

    Returns:
    A list of all the inventory and basic information on each switch.
    """
    gi_url = f'/rest/control/fabrics/{fabric_name}/inventory'
    resp = connection_obj.get(gi_url)
    data = json.loads(resp.text)
    return list(','.join(x['displayValues']) for x in data)


def get_templates(connection_obj):
    """ Function used to get all templates in DCNM.
    Args: connection_obj - is imported from main and is keeping track of the session connection to DCNM.

    returns:
    A list pf all the templates form DCNM each index is one template.
    """
    get_temp_url = '/fm/fmrest/config/templates/'
    resp = connection_obj.get(get_temp_url)
    data = json.loads(resp.text)
    return list(','.join(x['name'] for x in data))


def get_template_details(connection_obj, template_name):
    """ Function used to pull full details from 1 of the templates
    provided from get_templates function.

    Args:
        connection_obj - imported from main to keep track of DCNM api session.
        template_name - exact name from get_templates that more detail
                        is required for.

    returns:
    Full details for the provided from template in json.
    """
    temp_url = f'/fm/fmrest/config/templates/{template_name}'
    resp = connection_obj.get(temp_url)
    return json.loads(resp.text)


def get_vtep(connection_obj):
    """ Function is used to pull all VTEPs in DCNM.
    Args: connection_obj - is imported from main and is keeping track of the session connection to DCNM.

    Returns:
    payload in json format.
    """
    get_vtep_url = '/rest/topology/switches/vxlan/vteps'
    resp = connection_obj.get(get_vtep_url)
    return json.loads(resp.text)


def get_vni_per_swid(connection_obj, sw_id):
    """ Function used to pull all mappings for a given switch-id.
    mapping will be:
    switch: <name>, vlan <num>, VNI <num>

    Args:  switch-id which can be parsed from get_vteps output.
           connection_obj - imported from main to keep track of DCNM api session.

    returns:
    A list of the mappings. In above syntax, each index is one full mapping.
    """
    v_list = []
    get_vni = connection_obj.get(
        f"/rest/topology/switches/vxlan?switch-id={sw_id}")
    vnis = json.loads(get_vni.text)
    for x in vnis:
        v_list.append(
            f"Switch: {x['Switch Name']}, Vlan: {x['Vlan']}, Vni: {x['Vni']}")
    return v_list


@time_me
def create_networks(connection_obj, fabric_name, nets):
    """ Function is used to create a network in DCNM.
    Args:   connection_obj (obj) - is imported from main and is keeping track of the session connection to DCNM.
            fabric_name (str)
            nets (list) of (dicts)
                Example of nets:  [{'networkName': 'TEST_API_1','vlanId':999, 'segmentId':10999}]
                    networkName (str)
                    vlanID (int)
                    segmentId (int)

    Returns:
    (dict) {'successful': [list of networks {'networkName': <name>,'vlanId':<vlan>}], 'failed': [list of failed networks {'networkName': <name>,'vlanId':<vlan>}], 'duplicates':[list of networkNames]}
    """
    #Checking to see if any of the networks passed in from 'nets' already exist in DCNM, if found won't be created again.
    existing_nets = set(get_networks(
        connection_obj, connection_obj.fabric)).intersection(
            set(list(x['networkName'] for x in nets)))
    cn_url = f'/rest/top-down/fabrics/{fabric_name}/networks'
    #For networkTemplateconfig you cannot use the f-strings to format the string since its not
    #Allowed when the strings include '\' charcters.
    success_list = []
    failed_list = []
    dup_list = []
    #Loop through all networks to be created except for the networks that already existed. (NO BULK NETWORK CREATE API COULD BE FOUND.)
    for net in nets:
        if net['networkName'] in existing_nets:
            dup_list.append({
                'networkName': net['networkName'],
                'vlanId': int(net['vlanId']),
                'segmentId': int(net['segmentId'])
            })
        else:
            #net_template_config is based on "Default_network_extention" template, with values being passed in.
            net_template_config = """{\"suppressArp\":\"false\",\"vlanId\":\"%s\",\"gatewayIpAddress\":\"\",\"networkName\":\"%s\",\"enableIR\":\"false\",\"mtu\":\"\", \
        \"isLayer2Only\":\"true\",\"intfDescription\":\"\",\"segmentId\":\"%s\",\"mcastGroup\":\"239.1.1.1\",\"gatewayIpV6Address\":\"\",\"dhcpServerAddr1\":\"\",\"nveId\":\"1\", \
        \"vrfDhcp\":\"\",\"vrfName\":\"NA\"}""" % (net['vlanId'],
                                                   net['networkName'],
                                                   net['segmentId'])

            #Input_data is the body payload that needs to be sent with the API call to DCNM.
            input_data = {
                "fabric": f"{fabric_name}",
                "networkName": f"{net['networkName']}",
                "networkId": int(net['segmentId']),
                "networkTemplate": "Default_Network",
                "networkExtensionTemplate": "Default_Network_Extension",
                "networkTemplateConfig": f"{net_template_config}",
                "vrf": "NA"
            }
            try:
                #Since there is no bulk 'network create' api call, we for-loop through the networks.  The number of api calls = number of networks from original list.
                resp = connection_obj.post(cn_url, json.dumps(input_data))
                if resp.ok:
                    success_list.append({
                        'networkName': net['networkName'],
                        'vlanId': int(net['vlanId']),
                        'segmentId': int(net['segmentId'])
                    })
                else:
                    failed_list.append({
                        'networkName': net['networkName'],
                        'vlanId': int(net['vlanId']),
                        'segmentId': int(net['segmentId'])
                    })
            except Exception as e:
                print(e)
                sys.exit(0)
    return {
        'successful': success_list,
        'failed': failed_list,
        'duplicates': dup_list
    }


@time_me
def delete_networks(connection_obj, fabric_name, network_names):
    """ Function is used to create a network in DCNM.
    Args:   connection_obj (obj) - is imported from main and is keeping track of the session connection to DCNM.
            fabric_name (str)
            network_names (list)

    Returns:
    (dict) {'successful': [list of networks {'networkName': <name>,'vlanId':<vlan>}], 'failed': [list of failed networks {'networkName': <name>,'vlanId':<vlan>}], 'doesnt_exist:[list of networkNames]}
    """
    success_list = []
    failed_list = []
    doesnt_exist_list = []
    #Checking to see if any of the networks passed in from 'network_names' don't exist in DCNM, if found program won't try and delete an unexistent network.
    unexisting_nets = set(network_names) - set(
        get_networks(connection_obj, connection_obj.fabric))
    print(unexisting_nets)
    for net in network_names:
        if net in unexisting_nets:
            doesnt_exist_list.append(net)
        else:
            cn_url = f'/rest/top-down/fabrics/{fabric_name}/networks/{net}'
            try:
                resp = connection_obj.delete(cn_url)
                if resp.ok:
                    success_list.append(net)
                else:
                    failed_list.append(net)
            except Exception as e:
                print(e)
                sys.exit(0)
    return {
        'successful': success_list,
        'failed': failed_list,
        'doesnt_exist': doesnt_exist_list
    }


@time_me
def attach_networks(connection_obj, fabric_name, nets):
    """ Function is used to attach a network to a switch in DCNM.
    Args:   connection_obj - is imported from main and is keeping track of the session connection to DCNM.
            fabric_name (str)
            nets (list) of (dicts)
                Example of nets:  [{'networkName': 'TEST_API_1','vlanId':999, 'attachInfo': [{'serialNumber': FDO220324GK','interfaces': ''},{'serialNumber': FDO22112VQU','interfaces': ''}'']}]
                    networkName (str)
                    vlanID (int)
                    serialNumber (list) of serial numbers. We will for-loop through these later in the code.

    Returns:
    boolean: True for Success, False otherwise
    """
    #This url can take a 'bulk' style body and attach any number of networks with 1 API call.
    an_url = f'/rest/top-down/fabrics/{fabric_name}/networks/attachments'
    final_list = []
    #The Following for-loops are used to create the payload body to sent with API call.
    for net in nets:
        lan_attach_list = []
        for switch in net['attachInfo']:
            input_data = {
                "fabric": f"{fabric_name}",
                "networkName": f"{net['networkName']}",
                "serialNumber": f"{switch['serialNumber']}",
                "switchPorts": f"{','.join(switch['interfaces'])}",
                "detachSwitchPorts": "",
                "vlan": int(net['vlanId']),
                "dot1QVlan": 0,
                "untagged": False,
                "deployment": True
            }
            lan_attach_list.append(input_data)
        final_dict = {
            "networkName": f"{net['networkName']}",
            "lanAttachList": lan_attach_list
        }
        final_list.append(final_dict)
    try:
        #One single POST will have the body of ALL networks, and then ALL switches for each network to be deployed to.
        resp = connection_obj.post(an_url, json.dumps(final_list))
        if resp.ok:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        sys.exit(0)


@time_me
def deattach_networks(connection_obj, fabric_name, nets):
    """ Function is used to attach a network to a switch in DCNM.
    Args:   connection_obj - is imported from main and is keeping track of the session connection to DCNM.
            fabric_name (str)
            nets (list) of (dicts)
                Example of nets:  [{'networkName': 'TEST_API_1','vlanId':999, 'attachInfo': [{'serialNumber': FDO220324GK','interfaces': ''},{'serialNumber': FDO22112VQU','interfaces': ''}'']}]
                    networkName (str)
                    vlanID (int)
                    serialNumber (list) of serial numbers. We will for-loop through these later in the code.

    Returns:
    boolean: True for Success, False otherwise
    """
    #This url can take a 'bulk' style body and attach any number of networks with 1 API call.
    an_url = f'/rest/top-down/fabrics/{fabric_name}/networks/attachments'
    final_list = []
    #The Following for-loops are used to create the payload body to sent with API call.
    for net in nets:
        lan_attach_list = []
        for switch in net['attachInfo']:
            input_data = {
                "fabric": f"{fabric_name}",
                "networkName": f"{net['networkName']}",
                "serialNumber": f"{switch['serialNumber']}",
                "switchPorts": "",
                "detachSwitchPorts": f"{','.join(switch['interfaces'])}",
                "vlan": int(net['vlanId']),
                "dot1QVlan": 0,
                "untagged": False,
                "deployment": False
            }
            lan_attach_list.append(input_data)
        final_dict = {
            "networkName": f"{net['networkName']}",
            "lanAttachList": lan_attach_list
        }
        final_list.append(final_dict)
    try:
        #One single POST will have the body of ALL networks, and then ALL switches for each network to be deployed to.
        resp = connection_obj.post(an_url, json.dumps(final_list))
        if resp.ok:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        sys.exit(0)


@time_me
def deattach_interfaces(connection_obj, fabric_name, nets):
    """ Function is used to attach a network to a switch in DCNM.
    Args:   connection_obj - is imported from main and is keeping track of the session connection to DCNM.
            fabric_name (str)
            nets (list) of (dicts)
                Example of nets:  [{'networkName': 'TEST_API_1','vlanId':999, 'attachInfo': [{'serialNumber': FDO220324GK','interfaces': ''},{'serialNumber': FDO22112VQU','interfaces': ''}'']}]
                    networkName (str)
                    vlanID (int)
                    serialNumber (list) of serial numbers. We will for-loop through these later in the code.

    Returns:
    boolean: True for Success, False otherwise
    """
    #This url can take a 'bulk' style body and attach any number of networks with 1 API call.
    an_url = f'/rest/top-down/fabrics/{fabric_name}/networks/attachments'
    final_list = []
    #The Following for-loops are used to create the payload body to sent with API call.
    for net in nets:
        lan_attach_list = []
        for switch in net['attachInfo']:
            input_data = {
                "fabric": f"{fabric_name}",
                "networkName": f"{net['networkName']}",
                "serialNumber": f"{switch['serialNumber']}",
                "switchPorts": "",
                "detachSwitchPorts": f"{','.join(switch['interfaces'])}",
                "vlan": int(net['vlanId']),
                "dot1QVlan": 0,
                "untagged": False,
                "deployment": True
            }
            lan_attach_list.append(input_data)
        final_dict = {
            "networkName": f"{net['networkName']}",
            "lanAttachList": lan_attach_list
        }
        final_list.append(final_dict)
    try:
        #One single POST will have the body of ALL networks, and then ALL switches for each network to be deployed to.
        resp = connection_obj.post(an_url, json.dumps(final_list))
        if resp.ok:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        sys.exit(0)


@time_me
def preview(connection_obj, fabric_name, network_names):
    """ Function is used to preview the deployment of the network.
    Args:   connection_obj - is imported from main and is keeping track of the session connection to DCNM.
            fabric_name (str)
            network_name (list)
    Returns:
    json payload to overview the changes before continuing (logic in main()) or returns False if unsuccessful.
    """
    pv_url = f'/rest/top-down/fabrics/{fabric_name}/networks/preview?network-names={",".join(network_names)}'
    try:
        resp = connection_obj.get(pv_url)
        if resp.ok:
            return json.loads(resp.text)
        else:
            return False
    except Exception as e:
        print(e)
        sys.exit(0)


@time_me
def deploy_networks(connection_obj, fabric_name, network_names):
    """ Function is used to deploy the network that was created.
    Args:   connection_obj - is imported from main and is keeping track of the session connection to DCNM.
            fabric_name (str)
            network_name (list)
    Returns:
    boolean: True for Success, False otherwise
    """
    dn_url = f'/rest/top-down/fabrics/{fabric_name}/networks/deployments'
    input_data = {'networkNames': f'{",".join(network_names)}'}
    try:
        resp = connection_obj.post(dn_url, json.dumps(input_data))
        if resp.ok:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        sys.exit(0)
