#!/usr/bin/env python3
"""
To Run:
    $ python mock_data_populate.py <dcnm url> <ad.f.l>, -p [enter] it will prompt for password.
    
Example Run:
    $python mock_data_populate.py https://dcnm-lab.dev.schwab.com ad.jeff.kala -p
    Password:

"""
import argparse, json
from getpass import getpass
from dcnm.core.session import SessionManager


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("url", help="url of dcnm include https://")
        parser.add_argument(
            "user", help="ad.first.last for dcnm",
        )
        parser.add_argument(
            "-p",
            "--password",
            action="store_true",
            dest="password",
            help="hidden password prompt",
        )
        args = parser.parse_args()
        if args.password:
            password = getpass()
        conn = SessionManager(args.url, args.user, password)
        mock_data = {
            "logon": conn.login().text,
            "saveDefaultCredentials": conn.update_lan_creds().text,
            "dcnm-version": conn.version.text,
            "get-fabrics": conn.get("/rest/control/fabrics").text,
            "get-networks": conn.get("/fm/fmrest/san/getEthSwitchAllWithTaskInfo").text,
            "get-inventory": conn.get(
                "/rest/control/fabrics/PDC1-LAB-Fabric/inventory"
            ).text,
            "logout": conn.logout().text,
        }

        with open("mock_data.json", "w") as f:
            json.dump(mock_data, f)
    except Exception as e:
        print(e)
