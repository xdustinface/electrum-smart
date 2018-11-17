from collections import namedtuple, OrderedDict
import base64
import threading
import json
from decimal import Decimal

from . import bitcoin
from .blockchain import hash_header
from .smartnode import MasternodeAnnounce, NetworkAddress
from .util import AlreadyHaveAddress, print_error, bfh, print_msg, format_satoshis_plain, format_satoshis
from .bitcoin import COIN

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

class SmartRewardsAddress(object):

    def __init__(self, label='', address='', amount=0.0,
                 eligible_amount=0.0, estimated_reward=0):
        self.label = label
        self.address = address
        self.amount = amount
        self.eligible_amount = eligible_amount
        self.estimated_reward = estimated_reward

class SmartrewardsManager(object):
    """Smartrewards manager.

    Keeps track of smartrewards.
    """
    def __init__(self, wallet, network):
        self.smartrewards_cycle = SmartRewardsCycle()
        self.smartrewards_eligible = {}
        self.rewards = []
        self.network_event = threading.Event()
        self.wallet = wallet
        self.network = network
        self.load()

    def load(self):
        for addr in self.wallet.get_addresses():
            balance = sum(self.wallet.get_addr_balance(addr))
            label = self.wallet.labels.get(addr)
            if balance >= 1000 * COIN:
                self.rewards.append(SmartRewardsAddress(label, addr, balance, 0, 0))


    def send_subscriptions(self):
        if not self.wallet.network.is_connected():
            return
        self.subscribe_to_smartrewards_cycle()
        self.subscribe_to_smartrewards_address()

    def subscribe_to_smartrewards_cycle(self):
        if not self.wallet.network.is_connected():
            print_error("Cannot update smartrewards. Wallet not connected")
            return
        req = ('smartrewards.current', [])
        self.wallet.network.send([req], self.smartrewards_cycle_response)

    def subscribe_to_smartrewards_address(self):
        requests = []
        for addr in self.wallet.get_addresses():
            balance = sum(self.wallet.get_addr_balance(addr))
            if balance >= 1000 * COIN:
                requests.append(('smartrewards.check', [addr]))

        if not self.wallet.network.is_connected():
            print_error("Cannot update smartrewards. Wallet not connected")
            return

        self.network.send(requests, self.smartrewards_check_response)

    def smartrewards_cycle_response(self, response):

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

        result = response['result']
        addr = result.get("address")
        eligible_balance = result.get("balance_eligible")

        self.smartrewards_eligible[addr] = eligible_balance

        print_msg('received smartrewards resposnse: eligible balance for address {} is {}'.format(addr, eligible_balance))

    def get_smartrewards_current(self):
        return self.subscribe_to_smartrewards()

    def get_smartrewards_check(self, addr):
        return self.check_smartrewards_address(addr)

    def add_thousands_spaces(self, a):
        a = int(a)
        return format(a, ',').replace(',', ' ').replace('.', ',')
