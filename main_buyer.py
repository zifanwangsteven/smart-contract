from algosdk.future.transaction import LogicSig, AssetTransferTxn, LogicSigTransaction, calculate_group_id
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
    client = algod.AlgodClient(algod_token, algod_address, headers)
    return client

def wait_for_confirmation(client, transaction_id, timeout):
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

def purchase_bond(programstr, escrow_id, passphrase, amt, payment_id, par, interest_id, par_id, total_payments, algod_client, first_block, last_block):
    add = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)
    sp = algod_client.suggested_params()
    sp.first = first_block
    sp.last = last_block
    sp.flat_fee = True
    sp.fee = 1000
    print("--------------------------------------------")
    print("Opt-in the buyer account for interest and par token......")
    txn0_1 = AssetTransferTxn(add, sp, add, 0, interest_id)
    txn0_2 = AssetTransferTxn(add, sp, add, 0, par_id)
    sign0_1 = txn0_1.sign(key)
    sign0_2 = txn0_2.sign(key)
    txn0_1_id = algod_client.send_transaction(sign0_1)
    wait_for_confirmation(algod_client, txn0_1_id, 5)
    print("Successfully opt-in")
    print("--------------------------------------------")
    print("--------------------------------------------")
    print("Bundling purchase transactions and submitting......")
    txn0_2_id = algod_client.send_transaction(sign0_2)
    wait_for_confirmation(algod_client, txn0_2_id, 5)
    txn1 = AssetTransferTxn(add, sp, escrow_id, amt * par, payment_id)
    txn2 = AssetTransferTxn(escrow_id, sp, add, amt, par_id)
    txn3 = AssetTransferTxn(escrow_id, sp, add, amt * total_payments, interest_id)
    t = programstr.encode()
    program = base64.decodebytes(t)
    arg = (4).to_bytes(8, 'big')
    lsig = LogicSig(program, args=[arg])
    grp_id = calculate_group_id([txn1, txn2, txn3])
    txn1.group = grp_id
    txn2.group = grp_id
    txn3.group = grp_id
    stxn1 = txn1.sign(key)
    stxn2 = LogicSigTransaction(txn2, lsig)
    stxn3 = LogicSigTransaction(txn3, lsig)
    signed_group = [stxn1, stxn2, stxn3]
    tx_id = algod_client.send_transactions(signed_group)
    wait_for_confirmation(algod_client, tx_id, 200)
    print("Successfulley commited transaction!")
    print("--------------------------------------------")

def claim_interest(programstr, escrow_id, passphrase, amt, coupon, payment_id, interest_id, par_id, first_block, last_block, algod_client: algod_client()):
    add = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)
    sp = algod_client.suggested_params()
    sp.first = first_block
    sp.last = last_block
    sp.flat_fee = True
    sp.fee = 1000
    lease_str = "NPWoaHaDbyyovXHAHoc5AnKskQwfmTm4YK+psfQutvM="
    lease = base64.b64decode(lease_str)
    print("--------------------------------------------")
    print("Bundling interest claim and submitting......")
    txn1 = AssetTransferTxn(add, sp, escrow_id, amt, interest_id)
    txn2 = AssetTransferTxn(add, sp, add, amt, par_id)
    txn3 = AssetTransferTxn(escrow_id, sp, add, amt * coupon, payment_id, lease=lease)
    t = programstr.encode()
    program = base64.decodebytes(t)
    arg = (5).to_bytes(8, 'big')
    lsig = LogicSig(program, args=[arg])
    grp_id = calculate_group_id([txn1, txn2, txn3])
    txn1.group = grp_id
    txn2.group = grp_id
    txn3.group = grp_id
    stxn1 = txn1.sign(key)
    stxn2 = txn2.sign(key)
    stxn3 = LogicSigTransaction(txn3, lsig)
    signed_group = [stxn1, stxn2, stxn3]
    tx_id = algod_client.send_transactions(signed_group)
    wait_for_confirmation(algod_client, tx_id, 200)
    print("Successfully committed transaction!")
    print("--------------------------------------------")


def claim_par(programstr, escrow_id, passphrase, amt, par, payment_id, par_id, first_block, last_block, algod_client):
    add = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)
    sp = algod_client.suggested_params()
    sp.first = first_block
    sp.last = last_block
    sp.flat_fee = True
    sp.fee = 1000
    txn1 = AssetTransferTxn(add, sp, escrow_id, amt, par_id)
    txn2 = AssetTransferTxn(escrow_id, sp, add, amt * par, payment_id)
    t = programstr.encode()
    program = base64.decodebytes(t)
    arg = (6).to_bytes(8, 'big')
    lsig = LogicSig(program, args=[arg])
    grp_id = calculate_group_id([txn1, txn2])
    txn1.group = grp_id
    txn2.group = grp_id
    stxn1 = txn1.sign(key)
    stxn2 = LogicSigTransaction(txn2, lsig)
    signed_group = [stxn1, stxn2]
    tx_id = algod_client.send_transactions(signed_group)
    wait_for_confirmation(algod_client, tx_id, 10)


