from algosdk.future.transaction import LogicSig, PaymentTxn, AssetConfigTxn, AssetTransferTxn, LogicSigTransaction
from algosdk import mnemonic
from algosdk.v2client import algod
import os
import base64

def algod_client():
    algod_address = os.environ.get("ALGOD_ADDRESS")
    algod_token = ""
    api_key = os.environ.get("API_KEY")
    headers = {
        "X-API-KEY": api_key,
    }
    alc = algod.AlgodClient(algod_token, algod_address, headers)
    return alc

def wait_for_confirmation(client, transaction_id, timeout):
    """
    Wait until the transaction is confirmed or rejected, or until 'timeout'
    number of rounds have passed.
    Args:
        transaction_id (str): the transaction to wait for
        timeout (int): maximum number of rounds to wait
    Returns:
        dict: pending transaction information, or throws an error if the transaction
            is not confirmed or rejected in the next timeout rounds
    """
    start_round = client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception(
                'pool error: {}'.format(pending_txn["pool-error"]))
        client.status_after_block(current_round)
        current_round += 1
    raise Exception(
        'pending tx not found in timeout rounds, timeout value = : {}'.format(timeout))

def claim_fund(programstr, passphrase, escrow_id, amt, payment_id, first_block, last_block, algod_client: algod_client()):
    add = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)
    sp = algod_client.suggested_params()
    sp.first = first_block
    sp.last = last_block
    sp.flat_fee = True
    sp.fee = 1000
    txn = AssetTransferTxn(escrow_id, sp, add, amt, payment_id)
    t = programstr.encode()
    program = base64.decodebytes(t)
    arg = (3).to_bytes(8, 'big')
    lsig = LogicSig(program, args=[arg])
    stxn = LogicSigTransaction(txn, lsig)
    tx_id = algod_client.send_transaction(stxn)
    wait_for_confirmation(algod_client, tx_id, 10)


def replenish_account(passphrase, escrow_id, amt, payment_id, algod_client):
    add = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)
    sp = algod_client.suggested_params()
    sp.flat_fee = True
    sp.fee = 1000
    txn = AssetTransferTxn(add, sp, escrow_id, amt, payment_id)
    stxn = txn.sign(key)
    tx_id = algod_client.send_transaction(stxn)
    wait_for_confirmation(algod_client, tx_id, 10)