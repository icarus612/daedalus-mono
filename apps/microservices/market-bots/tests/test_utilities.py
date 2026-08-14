"""Tests for src.utilities.RobinhoodCredentials.

Written from the W1-P3 contract slice (apps/microservices/market-bots,
`RobinhoodCredentials` class specification) alone. Per the contract:

    class RobinhoodCredentials:
        def __init__(self):
            self.user = os.environ.get("RH_UNAME", "")
            self.password = os.environ.get("RH_PASSWORD", "")
            self.mfa_code = os.environ.get("RH_MFA_CODE", "")

`RobinhoodCredentials()` takes no arguments, and each attribute mirrors the
corresponding environment variable, defaulting to an empty string when that
variable is unset.
"""

from src.utilities import RobinhoodCredentials

ENV_VARS = ("RH_UNAME", "RH_PASSWORD", "RH_MFA_CODE")


def _unset_all(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_instantiates_with_no_arguments():
    # The contract's __init__ takes only `self` -- no required arguments.
    creds = RobinhoodCredentials()
    assert isinstance(creds, RobinhoodCredentials)


def test_defaults_to_empty_strings_when_env_vars_unset(monkeypatch):
    _unset_all(monkeypatch)

    creds = RobinhoodCredentials()

    assert creds.user == ""
    assert creds.password == ""
    assert creds.mfa_code == ""


def test_reflects_env_vars_when_set(monkeypatch):
    monkeypatch.setenv("RH_UNAME", "trader_joe")
    monkeypatch.setenv("RH_PASSWORD", "s3cr3t-pw")
    monkeypatch.setenv("RH_MFA_CODE", "123456")

    creds = RobinhoodCredentials()

    assert creds.user == "trader_joe"
    assert creds.password == "s3cr3t-pw"
    assert creds.mfa_code == "123456"
