""" pytest fixtures for dcnm server testing """
from pytest import fixture
from dcnm.core.session import SessionManager
from mock_dcnm_server import dcnm_server
from threading import Thread
import requests


h, p = "127.0.0.1", 5000


@fixture(autouse=True, scope="session")
def app():
    """ daemonized mocked dcnm server """
    app = dcnm_server()
    thread = Thread(target=app.run, daemon=True, kwargs=dict(host=h, port=p))
    thread.start()

    yield app

    requests.get(f"http://{h}:{p}/shutdown")
    thread.join()


@fixture(autouse=True)
def conn():
    """ dcnm session object """
    connection = SessionManager(f"http://{h}:{p}", "testuser", "testpasswd")
    return connection
