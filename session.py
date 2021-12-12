#!/usr/bin/env python
"""This class generates a API connection object

Jose Lima
Tue Nov 12 4:13:14 PM 2018

Tested on: Python v3.6.3, DCNM v10.4.x, v11.0.1, and v11.2.1

This is the core module used for setup, tracking and teardown of API calls to DCNM

    Example:
        A couple of ways to call this module from other scripts in the /dcnm/ root
        folder:

        1) from core.session import Session
            connection = Session(url, usr, pass)

        2) from core import session
            connection = session.Session(url, usr, pass)

    Notes:
        General usage:
            from core.session import Session

            connection = Session(url, usr, pass)
            connection.login()
            output = connection.get('/some/api/call')
            connection.logout()

            optional for post methods:
               connection.update_lan_creds()

    Todo:
        *
"""
# general imports
import json
import gzip

# our baked in requests
from . import requests

# import from our own API tools
from .utilities import (
    retry_on_server_error,
    retry_on_auth_and_error,
    retry_on_login_error,
)

# suppresses invalid cert warnings, depricated..., using verify=False
requests.packages.urllib3.disable_warnings()

__author__ = "Jose Lima"


class SessionManager:
    """API session manager base class

    This class creates a connection object used to manage API sessions
    It should be used to create new classes and take advantage of inheritance to
    support future versions of Cisco DCNM and adapt to any changes.

        Attributes:
            self.base_url (str): server URL e.g. http://dcnm-lab.schwab.com
            self.logon_url (str): url used to make auth request
            self.logout_url (str): url used to close teardown our session
            self.version_url (str): url used to verify the version of DCNM is supported by this module
            self.user (str): API username, ad.first.last, or first.last
            self._passwd (str): API password, through JH or first.last AD
            self.headers (json): required headers to stablish API call with DCNM
            self.expiration_time (int): how long to request our token from the server

        Notes:

            @retry_on_server_error = decorator used to retry on any HTTP 500+ errors
            @retry_on_auth_and_error = decorator used to retry on any HTTP 400+ errors

                decorators can be safely removed or commented out with out
                impacting API call functionality, however they are there to provide
                session reliability in the event the server is busy during any of
                the API calls.
    """

    def __init__(self, url, user, passwd):
        self.base_url = url
        self.logon_url = "/rest/logon"
        self.logout_url = "/rest/logout"
        self.version_url = "/rest/dcnm-version"
        self.update_lan_creds_url = "/fm/fmrest/lanConfig/saveDefaultCredentials"
        self.update_discovery_creds_url = "/fm/fmrest/san/setCdpSeed"
        self.user = user
        self._passwd = passwd
        self.fabric = None
        self.headers = {
            "Accept": "application/json, text/plain",
            "Content-Type": "application/json; charset=UTF-8",
        }
        # removed from headers due to 11.3 issues with gzip.  Add back in next dcnm version if supported.
        # "Content-Encoding": "gzip",
        self.expiration_time = 1000000

    def check_for_reauth(self, resp):
        if "Access denied" in resp.text:
            self.login()
            print(f"Re-authenticating session for {self.user}, done!\n")

    @property
    def supported_versions(self):
        self.DCNM_SUPPORTED_VERSIONS = ["11.2(1)", "11.3(1)", "11.4(1)"]
        return self.DCNM_SUPPORTED_VERSIONS

    @retry_on_login_error
    def login(self):
        """Creates login request to DCNM

        Pulls session token and updates headers on succesful login.
        all future request post/get/delete will include the token in the new
        header.

        Notes:
            self.version is called to check against supported
            DNCM versions in DCNM_SUPPORTED_VERSIONS constant
        """

        url = self.base_url + self.logon_url
        payload = {"expirationTime": self.expiration_time}
        try:
            resp = requests.post(
                url,
                auth=(self.user, self._passwd),
                data=json.dumps(payload),
                timeout=30,
                verify=False,
            )
            if resp.ok:
                dcnm_get_ver = self.version
                dcnm_ver = dcnm_get_ver.json()["Dcnm-Version"]
                self.headers.update(json.loads(resp.text))

                if dcnm_ver not in self.supported_versions:
                    print(
                        f"Server runs untested DCNM Version: {dcnm_ver}, tested DCNM versions include: {self.DCNM_SUPPORTED_VERSIONS}\n Please use the lastest install of this python package"
                    )
                    quit()
            else:
                print(f"Could not login to {url} --> {resp.text}")
            return resp

        except requests.exceptions.ConnectionError:
            print(f"Connection Timed out --> {url}")

    @retry_on_server_error
    def logout(self):
        # Dcnm-Token is already loaded through def login(), self.headers.update(json.loads(resp.text))
        url = self.base_url + self.logout_url
        # del self.headers["Content-Encoding"]
        resp = requests.post(url, headers=self.headers, timeout=30, verify=False)
        if resp.status_code != 202:
            print(
                f"Failed to logout: {url}, expected: 202, received --> {resp.status_code}"
            )
        return resp

    @property
    @retry_on_server_error
    def version(self):
        """Checks DCNM version number

        This runs on every successful login request, version returned from this
        call is compared with DCNM_SUPPORTED_VERSIONS

            Returns:
                resp (json): Dcnm-Version, resp.json()['Dcnm-Version']
        """
        resp = self.get(self.version_url)
        return resp

    @retry_on_auth_and_error
    def put(self, url, data, timeout=1200):
        url = self.base_url + url
        resp = requests.put(
            url, headers=self.headers, data=data, timeout=timeout, verify=False
        )
        if not resp.ok:
            print(f"Error: {url} --> {resp.text}")
            self.check_for_reauth(resp)
        return resp

    @retry_on_auth_and_error
    def post(self, url, data, timeout=1800):
        url = self.base_url + url
        # json_bytes = data.encode("utf-8")
        print(f"\n[ client --> server ] payload sent, waiting for server response...")
        resp = requests.post(
            url,
            headers=self.headers,
            # data=gzip.compress(json_bytes),
            data=data,
            timeout=timeout,
            verify=False,
        )
        print(
            f"[ server --> client ] response time delta: {resp.elapsed.total_seconds()} seconds\n"
        )
        if not resp.ok:
            print(f"Error: {url} --> {resp.text}\n")
            self.check_for_reauth(resp)
        return resp

    @retry_on_server_error
    def update_discovery_creds(self, payload):
        """updates discovery credentials in DCNM

        """
        url = self.base_url + self.update_discovery_creds_url
        headers = {
            "dcnm-token": self.headers["Dcnm-Token"],
            "content-type": "application/x-www-form-urlencoded",
            "cache-control": "no-cache",
        }
        resp = requests.post(
            url, headers=headers, data=payload, timeout=30, verify=False
        )
        if not resp.ok and resp.text != "Operation is successful":
            print(
                f"Error: {url} --> {resp.text}.. Manually update Discovery creds in DCNM GUI"
            )
        return resp

    @retry_on_server_error
    def update_lan_creds(self, other_user=None, other_passwd=None):
        """updates LAN credentials in DCNM

        Lan credentials are obtain through object at time of creation.
        Please make sure to use the correct RW credentials for this call.

        Examples:
            connection.login()
            connection.update_lan_creds()

        """
        url = self.base_url + self.update_lan_creds_url
        headers = {
            "dcnm-token": self.headers["Dcnm-Token"],
            "content-type": "application/x-www-form-urlencoded",
            "cache-control": "no-cache",
        }
        if other_user is None:
            payload = {
                "username": self.user,
                "password": self._passwd,
                "privProtocol": "N/A",
            }
        else:
            payload = {
                "username": other_user,
                "password": other_passwd,
                "privProtocol": "N/A",
            }
        resp = requests.post(
            url, headers=headers, data=payload, timeout=30, verify=False
        )
        if not resp.ok and resp.text != "Operation is successful":
            print(
                f"Error: {url} --> {resp.text}.. Manually update LAN creds in DCNM GUI"
            )
        return resp

    @retry_on_auth_and_error
    def get(self, url, timeout=30):
        url = self.base_url + url
        resp = requests.get(url, headers=self.headers, timeout=timeout, verify=False)
        if not resp.ok:
            try:
                print(f"Error: {self.base_url} --> {resp.json()['message']}")
            except Exception as e:
                print(f"Error: {url} --> {resp.text}")
            self.check_for_reauth(resp)
        return resp

    @retry_on_server_error
    def delete(self, url):
        url = self.base_url + url
        resp = requests.delete(url, headers=self.headers, verify=False)
        if not resp.ok:
            print(f"Error: {url} --> {resp.text}")
            self.check_for_reauth(resp)
        return resp


class Session(SessionManager):
    """Production Session manager class
    this supports existing API functionality
    """

    pass
