#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.qgis.test_oauth_config
    # for specific test
    python -m unittest tests.qgis.test_oauth_config.TestGetScopes.test_null_scope
"""

import json
import unittest

from lantmateriet_qgis.core.util.oauth_config import (
    OAuth2ConfigData,
    _parse_oauth_config,
    get_scopes,
)


class TestGetScopes(unittest.TestCase):
    """Test reading scopes out of an OAuth2 configuration."""

    def test_missing_scope(self):
        """A configuration without a scope key has no scopes."""
        self.assertEqual(get_scopes(OAuth2ConfigData()), [])

    def test_null_scope(self):
        """A configuration with a JSON null scope has no scopes.

        Regression test: ``config.get("scope", "")`` returns ``None`` here,
        since the default only applies to a missing key, and ``None.split()``
        raised an AttributeError.
        """
        config = _parse_oauth_config(json.dumps({"scope": None}))
        self.assertEqual(get_scopes(config), [])

    def test_empty_scope(self):
        """An empty scope is no scopes, not one empty scope."""
        self.assertEqual(get_scopes(OAuth2ConfigData(scope="")), [])

    def test_whitespace_scope(self):
        """A whitespace-only scope is no scopes."""
        self.assertEqual(get_scopes(OAuth2ConfigData(scope="   ")), [])

    def test_single_scope(self):
        self.assertEqual(get_scopes(OAuth2ConfigData(scope="a_read")), ["a_read"])

    def test_multiple_scopes(self):
        self.assertEqual(
            get_scopes(OAuth2ConfigData(scope="a_read b_read")), ["a_read", "b_read"]
        )

    def test_surrounding_whitespace(self):
        """Stray whitespace does not produce empty scopes."""
        self.assertEqual(
            get_scopes(OAuth2ConfigData(scope="  a_read   b_read ")),
            ["a_read", "b_read"],
        )

    def test_non_string_scope(self):
        """A scope of an unexpected type is read as no scopes."""
        config = _parse_oauth_config(json.dumps({"scope": ["a_read"]}))
        self.assertEqual(get_scopes(config), [])


class TestParseOAuthConfig(unittest.TestCase):
    """Test parsing the oauth2config payload of an authentication config."""

    def test_valid_payload(self):
        payload = json.dumps({"clientId": "abc", "scope": "a_read"})
        self.assertEqual(
            _parse_oauth_config(payload), {"clientId": "abc", "scope": "a_read"}
        )

    def test_empty_payload(self):
        """An authentication config without an oauth2config value."""
        self.assertEqual(_parse_oauth_config(""), {})
        self.assertEqual(_parse_oauth_config(None), {})

    def test_invalid_json_payload(self):
        """An unreadable payload is empty, not an exception."""
        self.assertEqual(_parse_oauth_config("not json"), {})

    def test_non_object_payload(self):
        """A payload that is valid JSON but not an object is empty."""
        self.assertEqual(_parse_oauth_config("[]"), {})
        self.assertEqual(_parse_oauth_config("null"), {})


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
