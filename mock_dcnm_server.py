""" flask dcnm mock server """
from flask import Flask, jsonify, request
import logging
import json

# suppress flask log noise
logset = logging.getLogger("werkzeug")
logset.setLevel(logging.ERROR)

with open("mock_data.json") as f:
    mock_data_dict = json.load(f)


def log_ep_request(ep, data):
    """  use in route:
        if request.method == "POST":
        log_ep_request(ep, request.get_data().decode())
    """
    with open("post_data.log", "a") as f:
        f.write(f"'{ep}' : {data},\n")


"""
def rest_endpoint_mock_data(endpoint):
    endpoint_d = {
        "logon": {"Dcnm-Token": "xzy"},
        "logout": "Logout Successfull",
        "dcnm-version": {"Dcnm-Version": "11.3(1)"},
        "saveDefaultCredentials": "Success",
    }
    return endpoint_d.get(endpoint, "NO MOCK DATA FOR ENDPOINT!")
"""


def rest_endpoint_mock_data(endpoint):
    mock_data_dict["logon"] = {"Dcnm-Token": "xzy"}
    return mock_data_dict.get(endpoint, "NO MOCK DATA FOR ENDPOINT!")


# pylint: disable=unused-variable,W0105
def dcnm_server():
    """ flask app daemonized for pytest """

    app = Flask(__name__)
    app.env = "development"
    app.testing = True

    @app.route("/shutdown")
    def shutdown():
        """ we need this to shutdown server after tests """
        request.environ["werkzeug.server.shutdown"]()
        return "OK", 200

    @app.route("/rest/<ep>", methods=["POST", "GET", "PUT", "DELETE"])
    def rest_endpoint(ep):
        """ /rest/* endpoints """
        if ep == "logout":
            return rest_endpoint_mock_data(ep), 202
        return rest_endpoint_mock_data(ep)

    @app.route("/fm/fmrest/lanConfig/<ep>", methods=["POST"])
    def lan_creds(ep):
        """ /lanConfig/* endpoints """
        return jsonify(rest_endpoint_mock_data(ep))

    return app


if __name__ == "__main__":
    app = dcnm_server()
    app.run()
