from algosdk.future.transaction import AssetTransferTxn
from algosdk import mnemonic
from algosdk.v2client import algod
from main_buyer import purchase_bond
import os

# def wait_for_confirmation(client, transaction_id, timeout):
#     """
#     Wait until the transaction is confirmed or rejected, or until 'timeout'
#     number of rounds have passed.
#     Args:
#         transaction_id (str): the transaction to wait for
#         timeout (int): maximum number of rounds to wait
#     Returns:
#         dict: pending transaction information, or throws an error if the transaction
#             is not confirmed or rejected in the next timeout rounds
#     """
#     start_round = client.status()["last-round"] + 1
#     current_round = start_round
#
#     while current_round < start_round + timeout:
#         try:
#             pending_txn = client.pending_transaction_info(transaction_id)
#         except Exception:
#             return
#         if pending_txn.get("confirmed-round", 0) > 0:
#             return pending_txn
#         elif pending_txn["pool-error"]:
#             raise Exception(
#                 'pool error: {}'.format(pending_txn["pool-error"]))
#         client.status_after_block(current_round)
#         current_round += 1
#     raise Exception(
#         'pending tx not found in timeout rounds, timeout value = : {}'.format(timeout))
#
algod_address = os.environ.get("ALGOD_ADDRESS")
algod_token = ""
api_key = os.environ.get("API_KEY")
headers = {
    "X-API-KEY": api_key,
}
client = algod.AlgodClient(algod_token, algod_address, headers)
params = client.suggested_params()
first = params.first
last = params.last
User_Address = "T7C6F3SHUYWJRZUCHVGDKSEEVOPJFOD2OHCVYKUU4UTIBVYQP4MNOBM7WY"
User_Mnemonic = "actress aware rocket couch human van dignity ill window banana object alone food horror grape drive street shock embark amateur decade genre sign absent fever"
User_Key = mnemonic.to_private_key(User_Mnemonic)
# Manager_Addres = "KIDEKPZDSNHMDMAKR4ZXAJ7Q3RMYLZYQB5TZ5IGPNBZG47PMNB65FK7BFA"
# Manager_Mnemonic = "connect another slight account merry project usage debris ignore achieve differ holiday cover annual adult poet lock minimum average occur melt renew nominee about list"
# Manager_Key = mnemonic.to_private_key(Manager_Mnemonic)
# atn = AssetTransferTxn(User_Address, params, User_Address, 0, 14208367)
# signed = atn.sign(User_Key)
# tx_id = client.send_transaction(signed)
# wait_for_confirmation(client, tx_id, 5)
# atn = AssetTransferTxn(Manager_Addres, params, User_Address, 1000, 14208367)
# signed = atn.sign(Manager_Key)
# tx_id = client.send_transaction(signed)
# wait_for_confirmation(client, tx_id, 5)

programstr = "AiARAAECAwQFBtWd4wbZneMG75rjBoDVpQYKgL/WBqDCHqCB9QagjQbA1YcJJgIgUgZFPyOTTsGwCo8zcCfw3FmF5xAPZ56gz2hybn3saH0G023sdDE2LRciEkAALi0XIxJAAEYtFyQSQABkLRclEkAAdi0XIQQSQADTLRchBRJAATotFyEGEkABagAxADEUEjETMgMSEDEQIQQSEDERIQcSEDESIhIQQgFmMQAxFBIxEzIDEhAxECEEEhAxEzIDEhAxESEIEhAxEiISEEIBQTEHKBIxECEEEhAxESEJEhAxAiEKDRBCASgzABAhBBIzABEhCRIQMwASIQsYIhIQMwAEIQwMEDMBECEEEhAzAREhCBIQMwESMwASIQsKEhAzAAAzARQSEDMCECEEEhAzAhEhBxIQMwISMwASIQsKIQ0LEhAzAAAzAhQSEEIAwzMAECEEEjMAESEHEhAzAAYpEhAzAQAzAAASEDMBFDMAABIQMwERIQgSEDMBEjMAEhIQMwIQIQQSEDMCESEJEhAzAhQzABMSEDIGIQ4NEDMCAiELGCISEDMCBDMBAiEPCBIQMwISMwASIwsSEEIAVDMAECEEEjMAESEIEhAzARAhBBIQMwECIRANEDMBFDMAABIQMwERIQkSEDMBEjMAEiELCxIQQgAcMQAxFBIxEzIDEhAxECEEEhAxESEJEhAxEiISEA=="
purchase_bond(programstr, #contract_response
              "XTERQOPEQ2SZ75EG24RFJ7KGCYVRDFFZVO756WN2QWKO3BFPPDJ5MM6ZLU", #contract_address
              User_Mnemonic, #mnemonic
              2, #amt
              14208367, # payment_id
              10,   # par
              14208725, # interest_id
              14208729, # par_id
              10, # total_payments
              client,
              first,
              last)
