from collections import namedtuple, OrderedDict
import base64
import threading
import json
from decimal import Decimal

from . import bitcoin
from .blockchain import hash_header
from .smartnode import MasternodeAnnounce, NetworkAddress
from .util import AlreadyHaveAddress, print_error, bfh, print_msg, format_satoshis_plain

class SmartRewardsCycle(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)

    rewards_cycle = 0
    start_blockheight = 0
    start_blocktime = 0
    end_blockheight = 0
    end_blocktime = 0
    eligible_addresses = 0
    eligible_smart = 0.0
    disqualified_addresses = 0
    disqualified_smart = 0.0
    estimated_rewards = 0.0
    estimated_percent = 0.0

    def get_rewards_cycle(self):
        return str(self.rewards_cycle)

class SmartrewardsManager(object):
    """Smartrewards manager.

    Keeps track of smartrewards.
    """
    def __init__(self, wallet):
        self.network_event = threading.Event()
        self.wallet = wallet
        self.smartrewards_cycle = SmartRewardsCycle()

    def send_subscriptions(self):
        if not self.wallet.network.is_connected():
            return
        self.subscribe_to_masternodes()

    def subscribe_to_smartrewards(self):
        if not self.wallet.network.is_connected():
            print_error("Cannot update smartrewards. Wallet not connected")
            return
        req = ('smartrewards.current', [])
        self.wallet.network.send([req], self.smartrewards_current_response)

    def check_smartrewards_address(self, addr):
        if not self.wallet.network.is_connected():
            print_error("Cannot update smartrewards. Wallet not connected")
            return
        req = ('smartrewards.check', [addr])
        return self.wallet.network.send([req], self.smartrewards_check_response)

    def smartrewards_current_response(self, response):

        if not 'result' in response:
            print_error(response['error'])
            return response['error']

        result = response['result']
        if result is None:
            result = False

        print_msg('Received smartrewards info: "%s"' % (result))

        self.smartrewards_cycle = SmartRewardsCycle(**result)

        a = 1

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