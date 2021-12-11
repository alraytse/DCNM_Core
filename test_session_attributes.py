""" session module tests """
from pytest import mark


@mark.core
class TestConnAttr:
    """ tests SessionManager connection object """

    def test_correct_logon_attr_is_set(self, conn):
        assert conn.logon_url == "/rest/logon"

    def test_correct_logout_attr(self, conn):
        assert conn.logout_url == "/rest/logout"

    def test_correct_version_attr(self, conn):
        """ dcnm version attr, used to check if this code will even run """
        assert conn.version_url == "/rest/dcnm-version"

    def test_correct_update_lan_creds_attr(self, conn):
        """ attr for updating dcnm lan credentions, needed to make changes """
        assert (
            conn.update_lan_creds_url == "/fm/fmrest/lanConfig/saveDefaultCredentials"
        )

    def test_correct_headers_attr(self, conn):
        """ this is the correct headers accepted by dcnm, any changes here and failures can occur """
        assert conn.headers == {
            "Accept": "application/json, text/plain",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def test_expiration_time_set_in_headers(self, conn):
        """ recommended timeout value by cisco to account for long api calls """
        assert conn.expiration_time == 1000000

    def test_fabric_is_set_to_none_from_start(self, conn):
        """ tests that fabric is None on initialize """
        assert conn.fabric is None

    def test_update_discover_creds_attr(self, conn):
        """ does this end point work on 11.3? """
        assert conn.update_discovery_creds_url == "/fm/fmrest/san/setCdpSeed"
