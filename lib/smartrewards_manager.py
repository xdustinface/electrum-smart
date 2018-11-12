from collections import namedtuple, OrderedDict
import base64
import threading
from decimal import Decimal

from . import bitcoin
from .blockchain import hash_header
from .smartnode import MasternodeAnnounce, NetworkAddress
from .util import AlreadyHaveAddress, print_error, bfh, print_msg, format_satoshis_plain

class SmartrewardsManager(object):
    """Smartrewards manager.

    Keeps track of smartrewards.
    """
    def __init__(self, wallet, config):
        self.network_event = threading.Event()
        self.wallet = wallet
        self.config = config
        self.smartrewards_statuses = {}

    def send_subscriptions(self):
        if not self.wallet.network.is_connected():
            return
        self.subscribe_to_masternodes()

    def subscribe_to_smartrewards(self):
        req = ('smartrewards.current', [])
        return self.wallet.network.send([req], self.smartrewards_current_response)

    def check_smartrewards_address(self, addr):
        req = ('smartrewards.check', [addr])
        return self.wallet.network.send([req], self.smartrewards_check_response)

    def smartrewards_current_response(self, response):

        if not 'result' in response:
            print_error(response['error'])
            return response['error']

        status = response['result']
        if status is None:
            status = False

        print_msg('Received updated smartrewards: "%s"' % (status))

        return status

    def smartrewards_check_response(self, response):

        if not 'result' in response:
            print_error(response['error'])
            return response['error']

        status = response['result']
        if status is None:
            status = False

        print_msg('Received updated smartrewards: "%s"' % (status))

        return status

    def get_smartrewards_current(self):
        return self.subscribe_to_smartrewards()

    def get_smartrewards_check(self, addr):
        return self.check_smartrewards_address(addr)