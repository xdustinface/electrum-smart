import threading
import requests, json

from decimal import Decimal
from electrum_smart.util import print_msg, print_stderr, json_encode, json_decode, UserCancelled
from electrum_smart.bitcoin import COIN

URL_HIVE_VOTING_PORTAL = "https://vote.smartcash.cc/api/v1/"

class SmartvoteManager(object):
    """Smartvote manager.

    Keeps track of votes and helps with signing address.
    """
    def __init__(self, wallet):
        self.network_event = threading.Event()
        self.wallet = wallet
        self.avaliable_addresses = {}
        self.selected_addresses = {}
        self.load()

    def load(self):
        """Load from wallet storage."""
        self.avaliable_addresses = self.get_avaliable_vote_addresses()
        self.selected_addresses = self.get_avaliable_vote_addresses()

    def update_proposals(self):
        request = "voteproposals"
        response = requests.get(URL_HIVE_VOTING_PORTAL+request)

        if (response.ok):

            # Loading the response data into a dict variable
            jData = json.loads(response.content.decode("utf-8"))

            print_msg("Loaded {0} proposals from smartvote API".format(len(jData.get("result"))))

            return jData

        else:
            # If response code is not ok (200), print the resulting http error code with description
            response.raise_for_status()

    def get_avaliable_vote_addresses(self):
        addresses = self.wallet.get_addresses()
        vote_addresses = {}
        for addr in addresses:
            c, u, x = self.wallet.get_addr_balance(addr)
            if c >= 1 * COIN:
                vote_addresses[addr] = int(c / COIN)
        return vote_addresses

    def add_vote_address(self, addr):
        c, u, x = self.wallet.get_addr_balance(addr)
        self.selected_addresses[addr] = int(c / COIN)

    def remove_vote_address(self, addr):
        del self.selected_addresses[addr]

    def get_voting_power(self):
        return sum(self.selected_addresses.values())

    def add_thousands_spaces(self, a):
        a = int(a)
        return format(a, ',').replace(',', ' ').replace('.', ',')