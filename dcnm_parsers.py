#!/usr/bin/env python
"""DCNM data parsers



Utilities used to read/write/convert data

    Example:
        import core.dcnm_parsers

    Todo:
        * todo
"""
import ipaddress
import json
import re


# support functions for DeploymentTracker
def network_name_generator(ip_address, vlan):
    """generates DCNM network name

    Args:
        ip_address (str): takes and ip address in this format 100.64.0.0/24
        vlan (str): vlan number, 777

    Examples:
        networkName = network_name_generator('100.64.0.0/24', '777')
        print(networkName)

    Output:

        100-64-0-0_24_VL777_10777

    """
    prefix = str(ip_address.replace(".", "-"))
    prefix = prefix.replace("/", "_")
    vlanId = str(vlan).strip()
    segmentId = str(int(vlan) + 10000).strip()
    str_vlan = "_" + "VL" + vlanId + "_"
    networkName = prefix + str_vlan + segmentId
    return networkName, vlanId, segmentId


def is_network_valid(my_ip, mim_allowed_prefixlen=30):
    """checks if my_ip is a valid IPv4 network in CIDR (network/bits)

        Args:
            ip (str): an my_ip address in string in CIDR notation, 100.64.0.0/24

            min_allowed_prefixlen (int): minimun CIDR prefix lenght allowed,
                if outside of this we Raise a ValueError, default value is 30 if
                not specified

        Examples:
            from core.dcnm_parsers import is_network_valid
            my_ip = '100.64.0.0/24'

            1) is_network_valid(my_ip)
            2) is_network_valid(my_ip, 28) -> 28 is min prefix lenght allowed

        Returns:
            bool: if my_ip is valid CIDR notation
            raise (ValueError): if invalid

    """
    if ipaddress.IPv4Network(my_ip).prefixlen < mim_allowed_prefixlen:
        return True
    else:
        raise ValueError(
            f"{my_ip} -> prefix length must be at least /{mim_allowed_prefixlen} bits and defined in CIDR notation"
        )


class DeploymentTracker:
    """Static factory class for tracking config states

    This class tracks config states from different sources

    Args:
        connection (obj): connection object from core.session.Session
        set fabric name before passing object to this function:
            connection.fabric = 'PDC1-LAB-Fabric'

        from_csv (str): file name from sys.argv[1] or string with file name 'my_csv.csv'
            when this is set, the file will be parsed through factory function new(), cells will be validated
            a new class object is created with a list of networks.

        from_list (list of dicts) [{},{}]: if we just want to feed this a list of networks to check status:
            valid format:

    Example:

        deployment = DeploymentTracker.new(connection, from_csv=sys.argv[1])

        my_deployment = DeploymentTracker.new(connection, from_list=my_list_of_dictionaries)

        print(my_deployment.get_deployment_status)
    """

    def __init__(self, connection, networks=None, interfaces=None):

        if networks:
            self.networks = networks
        else:
            self.networks = None

        if interfaces:
            self.interfaces = interfaces
        else:
            self.interfaces = None

        self.connection = connection
        self.user = connection.user
        self.server = connection.base_url
        self.fabric = connection.fabric
        self.fabrics_from_dcnm = self._get_fabrics
        if not self.fabric in self.fabrics_from_dcnm:
            raise ValueError(
                f"{self.fabric} name is invalid, available fabrics {self.fabrics_from_dcnm}"
            )
        print(f"\nWorking on: {self.fabric}\n")
        self.switchdb = self.get_switchdb

    @property
    def get_deployment_status(self):
        """returns a dictionary from all networks in network source"""
        network_names = ",".join(x["networkName"] for x in self.networks)
        resp = self.connection.get(
            f"/rest/top-down/fabrics/{self.fabric}/networks/attachments?network-names={network_names}"
        )
        return json.loads(resp.text)

    @property
    def _get_fabrics(self):
        """private method: returns a list of fabrics"""
        resp = self.connection.get(f"/rest/control/fabrics")
        return [x["fabricName"] for x in json.loads(resp.text)]

    @property
    def get_fabrics(self):
        """returns list of fabrics from DCNM"""
        return self.fabrics_from_dcnm

    @property
    def get_switchdb(self):
        """returns inventory of leafs and serial numbers for current fabric"""
        switchdb = self._get_switch_inv(self.connection)
        switchdb = {
            k["logicalName"].lower(): k["serialNumber"]
            for k in switchdb
            if k["switchRole"] != "spine"
        }
        return switchdb

    @classmethod
    def _cm_get_switchdb(cls, connection):
        """private method: used to pre-build cls.networks from csv"""
        switchdb = cls._get_switch_inv(connection)
        switchdb = {
            k["logicalName"].lower(): k["serialNumber"]
            for k in switchdb
            if k["switchRole"] != "spine"
        }
        return switchdb

    @classmethod
    def _get_switch_inv(cls, connection):
        """private method: retrieves list of switches in the current fabric
        requires connect.fabric = 'name-of-fabric',
        preferably this is done during connection setup"""
        resp = connection.get(f"/rest/control/fabrics/{connection.fabric}/inventory")
        return json.loads(resp.text)

    def set_fabric(self, new_value):
        """Allows assigment of self.fabric outside of the class"""
        self.fabric = new_value

    @classmethod
    def new(cls, connection, from_csv=None, attach_info=None, interfaces=None):
        """builds a class from a csv file or list of dictionaries

        Note:
            First row is skept by the parser, please include a header to name
            your columns.
            * only set attach_info for port/leaf deployments
            * only set interfaces if updating interface descriptions
            * DO NOT set both options at once, first option will take precedence

        Args:
            connection (obj): connection object from get_connection() -> contains session

            from_csv (str): string containing csv input file, sys.argv[1] is valid.
                * if this is the only option set, we return a network for initial network deployment
                * CSV should have 2 columns and proper header:  network,vlan

            attach_info (bool): CSV file  should have proper 4 column header with this set to True: subnet,vlan,switch,port

            interfaces (bool): CSV file should have 3 column header: switch,interface,description

            if attach_info and interface is not set: deployment = DeploymentTracker.new(connection, from_csv='data.csv')
                we return only a list of networks, we expect two column CSV header: subnet,vlan

        returns:
            class (obj): class objected used to provide support for deployment

        """
        if attach_info:
            networks = cls._attach_info_from_csv(connection, from_csv)
            obj = cls(connection, networks=networks)
        elif interfaces:
            interfaces = cls._interfaces_from_csv(connection, from_csv)
            obj = cls(connection, interfaces=interfaces)
        else:
            networks = cls._networks_from_csv(connection, from_csv)
            obj = cls(connection, networks=networks)
        return obj

    @classmethod
    def network_key(cls, n):
        """checks for valid ip address in CIDR format 0.0.0.0/0"""
        n = n.strip()
        network_p = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}")
        valid_network = network_p.match(n)
        if not valid_network:
            raise ValueError(
                f"{n}: Invalid IP address, use CIDR format e.g. 10.0.0.0/24"
            )
        return n

    @classmethod
    def vlan_key(cls, n):
        """checks for valid vlan number: 1-4094"""
        n = n.strip()
        vlan_p = re.compile(r"^[1-9](\d{,3})?$")
        valid_vlan = vlan_p.match(n)
        if not valid_vlan or int(n) > 4094:
            raise ValueError(f"{n}: Invalid vlan, valid vlans: 1-4094")
        return n

    @classmethod
    def switch_key(cls, n):
        """check for valid switch name format"""
        n = n.strip()
        switch_p = re.compile(r"^[a-zA-Z]+\w+$")
        valid_switch_name = switch_p.match(n)
        if not valid_switch_name:
            raise ValueError(f"{n}: Invalid switch name, e.g. rlf02bdc")
        return n

    @classmethod
    def desc_key(cls, n):
        """check description for invalid characters/format"""
        desc_p = re.compile(r"[.]{,80}")
        valid_desc = desc_p.match(n)
        if not valid_desc:
            raise ValueError(f"{n}: Invalid characters or limit reached, char max: 80")
        return n

    @classmethod
    def port_key(cls, port_key):
        """check portnames for invalid characters/format"""
        # ports_p = re.compile(r'^[a-zA-Z]+[^#$%&!_]+\d$')
        ports_p = re.compile(
            r"^([Ee]thernet[^#$%&!_]+\d$|[Pp]ort-channel[^#$%&!_]+\d$)"
        )
        ports = [x.strip().capitalize() for x in port_key.split(",")]
        for i in ports:
            valid_ports = ports_p.match(i)
            if not valid_ports:
                raise ValueError(
                    f"{port_key}: Invalid switch port number or bad format: {i} e.g. Ethernet1/1"
                )
        return ports

    @classmethod
    def csv_reader(cls, csvfile):
        """returns a generator object from csv file"""
        import csv

        with open(csvfile) as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) > 0:
                    yield row

    @classmethod
    def _generate_network(cls, row):
        """takes row from csv, returns a dictionary after field validation"""
        if is_network_valid(cls.network_key(row[0])) and cls.vlan_key(row[1]):
            temp_dict = {}
            networkName, vlanId, segmentId = network_name_generator(row[0], row[1])
            temp_dict["networkName"] = networkName
            temp_dict["vlanId"] = vlanId
            temp_dict["segmentId"] = segmentId
            temp_dict["attachInfo"] = []
            print(f"Network: {networkName} --> VLAN: {vlanId}")
        return temp_dict

    @classmethod
    def _generate_interface(cls, row):
        """takes row from csv, returns a dictionary after field validation"""
        interface = {}
        # {"deviceName": "rlf05lab", "ifName":"Ethernet1/1", "DESC":"TEST_INT_DESC"}
        # 80 chars max allowed per cisco docs
        interface["deviceName"] = cls.switch_key(row[0])
        interface["ifName"] = cls.port_key(row[1])[0]
        interface["DESC"] = cls.desc_key(row[2]).lower()
        print(
            f'Switch: {interface["deviceName"]}, port: {interface["ifName"]} desc: {interface["DESC"]}'
        )
        return interface

    @classmethod
    def _interfaces_from_csv(cls, connection, csvfile):
        """private method: generates a list of network dictionaries"""
        csvfile_iter = cls.csv_reader(csvfile)
        switchdb = cls._cm_get_switchdb(connection)
        interfaces = []
        for row in csvfile_iter:
            interfaces.append(cls._generate_interface(row))
        input("\n\nPress any key to continue...... CTRL-C to abort\n\n")
        return interfaces

    @classmethod
    def _networks_from_csv(cls, connection, csvfile):
        """private method: generates a list of network dictionaries"""
        networks_dict = {}
        csvfile_iter = cls.csv_reader(csvfile)
        switchdb = cls._cm_get_switchdb(connection)
        for row in csvfile_iter:
            temp_dict = cls._generate_network(row)
            networks_dict[temp_dict["networkName"]] = temp_dict
        input("\n\nPress any key to continue...... CTRL-C to abort\n\n")
        return [x for x in networks_dict.values()]

    @classmethod
    def get_switch_peer(cls, connection, serial, net_name):
        url = f"/rest/top-down/fabrics/{connection.fabric}/networks/switches?network-names={net_name}&serial-numbers={serial}"
        resp = connection.get(url)
        if resp.status_code == 200:
            for switch in json.loads(resp.text)[0]["switchDetailsList"]:
                if switch["serialNumber"] == serial:
                    return switch["peerSerialNumber"]

            return
        else:
            raise ValueError(
                f"networkName: {net_name} -> switch serialNumber: {serial} not attached, check DCNM for status"
            )

    @classmethod
    def _attach_info_from_csv(cls, connection, csvfile):
        """private method: generates a list of dictionaries from csv"""
        csvfile_iter = cls.csv_reader(csvfile)
        switchdb = cls._cm_get_switchdb(connection)
        networks = []
        for row in csvfile_iter:
            # get basic kv networks -> vlan,vni,network name
            net = cls._generate_network(row)
            switchName = cls.switch_key(row[2])
            if switchName not in switchdb:
                raise KeyError(
                    f"SwitchName: {switchName}, is not valid or not in {connection.fabric}, check name/case. Available switches: {switchdb}"
                )
            net["serialNumber"] = switchdb[switchName]
            net["ports"] = cls.port_key(row[3])
            peerSerialNumber = cls.get_switch_peer(
                connection, net["serialNumber"], net["networkName"]
            )
            net["peer"] = peerSerialNumber
            networks.append(net)
        for i in networks:
            i["attachInfo"].append(
                {"interfaces": i["ports"], "serialNumber": i["serialNumber"]}
            )
            i["attachInfo"].append({"interfaces": [], "serialNumber": i["peer"]})
            for x in networks:
                if (
                    i["networkName"] == x["networkName"]
                    and i["serialNumber"] == x["peer"]
                ):
                    i["attachInfo"].append(
                        {"serialNumber": x["serialNumber"], "interfaces": x["ports"]}
                    )
        input("\n\nPress any key to continue...... CTRL-C to abort\n\n")
        return networks
