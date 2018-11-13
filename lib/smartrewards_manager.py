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

    def __init__(self, rewards_cycle=0, start_blockheight=0, start_blocktime=0,
                 end_blockheight=0, end_blocktime=0, eligible_addresses=0.0, eligible_smart=0,
                 disqualified_addresses=0, disqualified_smart=0.0,
                 estimated_rewards=0.0, estimated_percent=0.0):
        self.rewards_cycle = rewards_cycle
        self.start_blockheight = start_blockheight
        self.start_blocktime = start_blocktime
        self.end_blockheight = end_blockheight
        self.end_blocktime = end_blocktime
        self.eligible_addresses = eligible_addresses
        self.eligible_smart = eligible_smart
        self.disqualified_addresses = disqualified_addresses
        self.disqualified_smart = disqualified_smart
        self.estimated_rewards = estimated_rewards
        self.estimated_percent = estimated_percent
        self.actual_blockheight = 0

    def get_rewards_cycle(self):
        return str(self.rewards_cycle)

    def get_estimated_percent(self):
        return "{:.2%}".format(self.estimated_percent)

    def get_rounds_end(self):
        return '{} blocks'.format(self.end_blockheight - self.actual_blockheight)

class SmartrewardsManager(object):
    """Smartrewards manager.

    Keeps track of smartrewards.
    """
    def __init__(self, wallet, network):
        self.network_event = threading.Event()
        self.wallet = wallet
        self.smartrewards_cycle = SmartRewardsCycle()
        self.network = network

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

        self.smartrewards_cycle.actual_blockheight = self.network.get_local_height()

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