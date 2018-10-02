import threading
import requests, json

from electrum_smart.util import print_msg, print_stderr, json_encode, json_decode, UserCancelled

URL_HIVE_VOTING_PORTAL = "https://vote.smartcash.cc/api/v1/"

class SmartvoteManager(object):
    """Smartvote manager.

    Keeps track of votes and helps with signing address.
    """
    def __init__(self):
        self.network_event = threading.Event()
        #self.wallet = wallet
        #self.config = config
        self.load()

    def load(self):
        """Load from wallet storage."""
        #masternodes = self.wallet.storage.get('masternodes', {})
        #self.masternodes = [MasternodeAnnounce.from_dict(d) for d in masternodes.values()]

    def update_proposals(self):
        request = "voteproposals"
        response = requests.get(URL_HIVE_VOTING_PORTAL+request)

        if (response.ok):

            # Loading the response data into a dict variable
            jData = json.loads(response.content)

            print_msg("Loaded {0} proposals from smartvote API".format(len(jData.get("result"))))

            return jData

        else:
            # If response code is not ok (200), print the resulting http error code with description
            response.raise_for_status()