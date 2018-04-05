from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from btcrpc.utils.config_file_reader import ConfigFileReader
from btcrpc.utils.rpc_calls.rpc_call import RPCCall
from btcrpc.utils.chain_enum import ChainEnum
import json
import socket, errno
from web3 import Web3, HTTPProvider

from btcrpc.utils.log import *

log = get_log("PythonBitcoinRpc Call:")


class PythonEthJsonRpc(RPCCall):
    def __init__(self, wallet, currency):
        yml_config_reader = ConfigFileReader()
        url = yml_config_reader.get_rpc_server(currency=currency, wallet=wallet)
        w3 = Web3(HTTPProvider(url))
        self.access = w3

    def do_getinfo(self):
        raise NotImplementedError

    def do_get_new_address(self):
        raise NotImplementedError

    def do_set_account(self, address, account):
        raise NotImplementedError

    def do_get_transaction(self, txid):
        raise NotImplementedError

    def do_list_transactions(self, account, count=10, from_index=0):
        raise NotImplementedError

    def amount_received_by_address(self, address="", confirms=0):
        raise NotImplementedError

    def do_validate_address(self, address=""):
        #Since the address sent in might not be in checksum format, we convert it. Note: self.access.eth.accounts always
        #returns the accounts in checksum format.
        check_sum_address = self.access.toChecksumAddress(address)
        is_valid_address = self.access.isAddress(check_sum_address)
        wallet_account = \
            next((account for account in self.access.eth.accounts if account == self.access.toChecksumAddress(check_sum_address)),
                 None)
        address_is_mine = wallet_account is not None
        return {'isvalid': is_valid_address, 'ismine': address_is_mine}

    def list_transactions(self, account="", count=10, from_index=0):
        raise NotImplementedError

    def send_from(self, from_account="", to_address="", amount=0, minconf=1):
        raise NotImplementedError

    def get_blockchain_info(self):
        raise NotImplementedError

    def get_received_amount_by_account(self, account="", minconf=1):
        raise NotImplementedError

    def get_balance(self, account="", minconf=1):
        raise NotImplementedError

    def get_wallet_balance(self):
        accounts = self.access.eth.accounts
        account_balances = map(lambda account: self.access.fromWei(self.access.eth.getBalance(account), "ether"),
                               accounts)
        return sum(account_balances)

    def get_chain(self):
        try:
            network_id_string = self.access.net.version
            network_id_int = int(network_id_string)
            if network_id_int == 1:
                return ChainEnum.MAIN
            elif network_id_int == 0 \
                or network_id_int == 2 \
                or network_id_int == 3 \
                or network_id_int == 4 \
                or network_id_int == 42 \
                or network_id_int == 77:
                return ChainEnum.TEST_NET
            elif network_id_int == 1999:
                return ChainEnum.REGTEST
            else:
                return ChainEnum.UNKNOWN
        except ValueError:
            return ChainEnum.UNKNOWN

    def move(self, from_account="", to_account="", amount=0, minconf=1):
        raise NotImplementedError

    def list_accounts(self, confirmations=1):
        return self.access.eth.accounts

    def list_received_by_address(self, confirmations=1, include_empty=False):
        raise NotImplementedError

    def get_addresses_by_account(self, account):
        raise NotImplementedError

    def set_tx_fee(self, amount):
        # Since we want to use the fee suggested by the node software, we don't make a RPC call to manually set the fee.
        return False

    def send_to_address(self, address, amount, subtractfeefromamount=True):
        txids = []
        check_sum_address = self.access.toChecksumAddress(address)
        amount_left_to_send = self.access.toWei(amount, "ether")
        for account in self.access.eth.accounts:
            #NOTE TO BE REMOVED: ONLY FOR TESTING
            if account == self.access.eth.accounts[0]:
                continue
            sender = account
            receiver = check_sum_address
            balance = self.access.eth.getBalance(sender)
            transactionObject = {
                'from': sender,
                'to': receiver
            }
            transactionFee = self.access.eth.gasPrice * self.access.eth.estimateGas(transactionObject)
            if balance < transactionFee: #Theres either no balance to send or, only balance lower than the transactionfee
                continue
            print(account)
            if balance < amount_left_to_send:
                transactionValue = balance - transactionFee
            else:
                if subtractfeefromamount:
                    transactionValue = amount_left_to_send - transactionFee
                elif amount_left_to_send + transactionFee > balance:
                    transactionValue = balance - transactionFee
                else:
                    transactionValue = amount_left_to_send

            transactionObject['value'] = transactionValue
            self.access.personal.unlockAccount(account, "vt_test4")
            txid = self.access.eth.sendTransaction(transactionObject)
            self.access.personal.lockAccount(account)
            txids.append(txid)
            #self.access.eth.sendTransaction(transactionObject, callback_function)
            amount_left_to_send = amount_left_to_send - transactionValue
            if subtractfeefromamount:
                amount_left_to_send = amount_left_to_send - transactionFee
            if amount_left_to_send <= 0:
                break
        return txids

    # amount is type of dictionary
    def send_many(self, from_account="", minconf=1, **amounts):
        raise NotImplementedError