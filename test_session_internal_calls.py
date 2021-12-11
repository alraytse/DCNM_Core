""" test basic api calls needed by SessionManager obj """
import json
from pytest import mark


@mark.live_calls
@mark.smoke
@mark.core
class TestSessionObjCalls:
    """ test dcnm.core.sesson.SessionManager object """

    def test_get_method(self, conn):
        response = conn.get("/rest/fake")
        assert response.text == "NO MOCK DATA FOR ENDPOINT!"

    def test_post_method(self, conn):
        response = conn.post("/rest/fake", {"fake": "data"})
        assert response.text == "NO MOCK DATA FOR ENDPOINT!"

    def test_login_method(self, conn):
        response = conn.login()
        assert response.json() == {"Dcnm-Token": "xzy"}

    def test_logout_method_is_success(self, conn):
        response = conn.logout()
        assert response.status_code == 202

    def test_dcnm_version_method_is_supported(self, conn):
        """ checks dcnm version from the server """
        response = conn.version
        local_supported_versions = conn.supported_versions
        assert response.json()["Dcnm-Version"] in local_supported_versions

    def test_update_lan_creds_method(self, conn):
        conn.login()
        response = conn.update_lan_creds()
        assert response.ok
