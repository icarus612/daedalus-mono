import os


class RobinhoodCredentials:
    """Robinhood login credentials sourced from the environment.

    Mirrors the `RH_UNAME` / `RH_PASSWORD` environment variables `main.py` already
    reads via `dotenv`. `mfa_code` is optional — an empty string disables MFA, matching
    `TradeBot.__init__`'s existing "MFA code is not supplied" branch in
    controllers/base_trade_bot_RH.py.
    """

    def __init__(self):
        self.user = os.environ.get("RH_UNAME", "")
        self.password = os.environ.get("RH_PASSWORD", "")
        self.mfa_code = os.environ.get("RH_MFA_CODE", "")
