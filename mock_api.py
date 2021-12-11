""" mock server for end to end testing, with out actual API access """
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
from threading import Thread
from mock_api_data import api_mock_resp
import requests


class MockApiRequestHandler(BaseHTTPRequestHandler):
    """ Mock API responder, ** path ** is the endpoint passed to this server! """

    def respond_with(self, endpoint, api_mock_resp):
        if endpoint in api_mock_resp:
            self.send_response(requests.codes.ok)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            response_content = json.dumps(api_mock_resp[endpoint])
            self.wfile.write(response_content.encode("utf-8"))
            self.wfile.flush()
        else:
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.send_error(404)

    def do_GET(self):
        """ GET implementation for testing POST calls """
        endpoint = self.path.replace("/", "_")
        # self.respond_with(endpoint, api_mock_resp)
        if endpoint in api_mock_resp:
            self.send_response(requests.codes.ok)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            response_content = json.dumps(api_mock_resp[endpoint])
            self.wfile.write(response_content.encode("utf-8"))
            self.wfile.flush()

    def do_POST(self):
        """ POST implementation for testing POST calls """
        endpoint = self.path.replace("/", "_")
        # self.respond_with(endpoint, api_mock_resp)
        if endpoint in api_mock_resp:
            self.send_response(requests.codes.ok)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            response_content = json.dumps(api_mock_resp[endpoint])
            self.wfile.write(response_content.encode("utf-8"))
            self.wfile.flush()


def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    _, port = s.getsockname()
    s.close()
    return port


def start_mock_server(port):
    mock_server = HTTPServer(("127.0.0.1", port), MockApiRequestHandler)
    mock_server_thread = Thread(target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()
