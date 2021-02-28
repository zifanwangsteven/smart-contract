from algosdk.future.transaction import LogicSig, PaymentTxn, AssetConfigTxn, AssetTransferTxn, LogicSigTransaction
from algosdk import account, mnemonic
from contract import compile
from algosdk.v2client import algod
import os
import base64
from main_buyer import purchase_bond, claim_interest

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


def interest_token_issuance(algod_client, passphrase, proj_name, vol, url, total_payments) -> (int, int):
    """
    Issues Token for Interest Payment
    Default 10 interest payments
    returns an AssetConfigTxn()
    """

    # sets basic transaction parameter
    params = algod_client.suggested_params()
    params.fee = 1000
    params.flat_fee = True
    address = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)
    # configure asset basics
    txn = AssetConfigTxn(
        sender= address,
        sp=params,
        total=total_payments * vol,
        default_frozen=False,
        unit_name=proj_name[0] + "IC",
        asset_name=proj_name + "Interest",
        manager=address,
        reserve=address,
        freeze=address,
        clawback=address,
        url=url,
        decimals=0)
    signed = txn.sign(key)
    txid = algod_client.send_transaction(signed)
    wait_for_confirmation(algod_client, txid, 4)
    try:
        ptx = algod_client.pending_transaction_info(txid)
        asset_id = ptx["asset-index"]
        return txid, asset_id
    except Exception as e:
        print(e)


def par_token_issuance(algod_client, passphrase, proj_name, vol, url) -> (int, int):
    """
    Issues Token for Par Value Payment
    returns an AssetConfigTxn()
    """

    # sets basic transaction parameter
    params = algod_client.suggested_params()
    params.fee = 1000
    params.flat_fee = True

    address = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)

    # configure asset basics
    txn = AssetConfigTxn(
        sender=address,
        sp=params,
        total=vol,
        default_frozen=False,
        unit_name=proj_name[0] + "PC",
        asset_name=proj_name + "Par",
        manager=address,
        reserve=address,
        freeze=address,
        clawback=address,
        url=url,
        decimals=0)
    signed = txn.sign(key)
    txid = algod_client.send_transaction(signed)
    wait_for_confirmation(algod_client, txid, 4)
    try:
        ptx = algod_client.pending_transaction_info(txid)
        asset_id = ptx["asset-index"]
        return txid, asset_id
    except Exception as e:
        print(e)


def create_escrow(mgr_add: str, proj_name: str, interest_id: int, par_id: int, payment_id: int, closure: int,
                  begin_round: int, end_round: int, par: int, coupon: int, total_payments, period: int, span: int, holdup: int, algod_client) -> (str, str):
    """

    :param closure: the last round before which a buyer can purchase bond in escrow account
    :param total_payments: the number of interest payments
    :param holdup: the time period within which the bondholder cannot withdraw funding from escrow account
    :param mgr_add: public address of manager of interest_id and par_id (should be bond issuer)
    :param proj_name: name of the project, should be the same as when configuring ASA
    :param interest_id: the asset-id field for the interest token created
    :param par_id: the asset-id field for the par token created
    :param payment_id: the asset-id field for the stablecoin accepted as payment
    :param begin_round: the first round from which the bondholders can collect interest
    :param end_round: the first round from which bondholders can collect par value
    :param par: the par value of the bond, as measured in units of payment_id
    :param coupon: the amount payable in every period, as measured in units of payment_id
    :param period: the number of rounds after which an interest can be collected
    :param span: the number of rounds allowed for claim of interest
    :return: the hashed address of the TEAL program (escrow account)
    """


    program = compile(mgr_add, interest_id, par_id, payment_id, closure, par,
                      coupon, holdup, begin_round, end_round, total_payments,
                      period, span, proj_name)

    raw_teal = "./teal/{}.teal".format(proj_name)
    data = open(raw_teal, 'r').read()

    try:
        response = algod_client.compile(data)
        return response['result'], response['hash']
    except Exception as e:
        return str(e)

def payment_transaction(passphrase, amt, rcv, algod_client)->dict:
    params = algod_client.suggested_params()
    add = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)
    params.flat_fee = True
    params.fee = 1000
    unsigned_txn = PaymentTxn(add, params, rcv, amt)
    signed = unsigned_txn.sign(key)
    txid = algod_client.send_transaction(signed)
    pmtx = wait_for_confirmation(algod_client, txid, 4)
    return pmtx

def asset_transaction(passphrase, amt, rcv, asset_id, algod_client)->dict:
    params = algod_client.suggested_params()
    add = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)
    params.flat_fee = True
    params.fee = 1000
    unsigned_txn = AssetTransferTxn(add, params, rcv, amt, asset_id)
    signed = unsigned_txn.sign(key)
    txid = algod_client.send_transaction(signed)
    pmtx = wait_for_confirmation(algod_client, txid, 4)
    return pmtx

def main_pub(passphrase, proj_name, vol, url, par, coupon, payment_id,
             closure, start_round, period, total_payments, span, hold_up, client):
    # ensuring that buyer will be able to claim coupon on start_round
    add = mnemonic.to_public_key(passphrase)
    key = mnemonic.to_private_key(passphrase)
    print("Checking configurations......")
    print("--------------------------------------------")
    cl = client
    if start_round % period != 0:
        start_round = (start_round + period) - (start_round % period)
        print("Start round for interest payment refactored to {}".format(start_round))
    end_round = start_round + (total_payments-1) * period
    print("--------------------------------------------")

    # issuance of tokens
    print("Issuing tokens......")
    print("--------------------------------------------")
    try:
        interest_txid, interest_id = interest_token_issuance(cl, passphrase, proj_name, vol, url, total_payments)
        par_txid, par_id = par_token_issuance(cl, passphrase, proj_name, vol, url)
    except Exception as e:
        print("Issuance failed :{}".format(e))
        return
    print("Issued tokens successfully")
    print("Interest token id: {}, recorded in {}".format(interest_id, interest_txid))
    print("Par token id: {}, recorded in {}".format(par_id, par_txid))
    print("--------------------------------------------")

    # creating escrow account
    print("--------------------------------------------")
    print("Creating escrow account......")
    try:
        escrow_result, escrow_id = create_escrow(add, proj_name, interest_id, par_id, payment_id,
                                  closure, start_round, end_round, par, coupon,
                                  total_payments, period, span, hold_up, cl)
    except Exception as e:
        print("Escrow account creation failed :{}".format(e))
        return
    print("Created escrow account successfully")
    print("Escrow account result :{}".format(escrow_result))
    print("Escrow account public address: {}".format(escrow_id))
    print("--------------------------------------------")

    # activating escrow account
    print("--------------------------------------------")
    print("Activating escrow account......")
    try:
        txn = payment_transaction(passphrase, 1000000, escrow_id, cl)
    except Exception as e:
        print("Activation failed :{}".format(e))
        return
    print("Activated successfully")
    print(txn)
    print("--------------------------------------------")

    # opt-in the escrow account for interest token
    print("--------------------------------------------")
    print("Opt-in for interest token......")
    try:
        program_str = escrow_result.encode()
        program = base64.decodebytes(program_str)
        arg1 = (0).to_bytes(8, 'big')
        lsig = LogicSig(program, [arg1])
        sp = cl.suggested_params()
        atn = AssetTransferTxn(lsig.address(), sp, lsig.address(), 0, interest_id)
        lstx = LogicSigTransaction(atn, lsig)
        txid = cl.send_transaction(lstx)
        msg = wait_for_confirmation(cl, txid, 5)
    except Exception as e:
        print("Opt-in interest token failed :{}".format(e))
        return
    print("Opt-in interest token success!")
    print(msg)
    print("--------------------------------------------")

    # opt-in the escrow account for par token
    print("--------------------------------------------")
    print("Opt-in for par token......")
    try:
        program_str = escrow_result.encode()
        program = base64.decodebytes(program_str)
        arg1 = (1).to_bytes(8, 'big')
        lsig = LogicSig(program, [arg1])
        sp = cl.suggested_params()
        atn = AssetTransferTxn(lsig.address(), sp, lsig.address(), 0, par_id)
        lstx = LogicSigTransaction(atn, lsig)
        txid = cl.send_transaction(lstx)
        msg = wait_for_confirmation(cl, txid, 5)
    except Exception as e:
        print("Opt-in par token failed :{}".format(e))
        return
    print("Opt-in par token success!")
    print(msg)
    print("--------------------------------------------")

    # opt-in the escrow account for payment token
    print("--------------------------------------------")
    print("Opt-in for payment token......")
    try:
        program_str = escrow_result.encode()
        program = base64.decodebytes(program_str)
        arg1 = (6).to_bytes(8, 'big')
        lsig = LogicSig(program, [arg1])
        sp = cl.suggested_params()
        atn = AssetTransferTxn(lsig.address(), sp, lsig.address(), 0, payment_id)
        lstx = LogicSigTransaction(atn, lsig)
        txid = cl.send_transaction(lstx)
        msg = wait_for_confirmation(cl, txid, 5)
    except Exception as e:
        print("Opt-in payment token failed :{}".format(e))
        return
    print("Opt-in payment token success!")
    print(msg)
    print("--------------------------------------------")

    # transferring the interest tokens to escrow account
    print("--------------------------------------------")
    print("Transfer interest token to escrow account......")
    try:
        atn = asset_transaction(passphrase, vol * total_payments, escrow_id, interest_id, cl)
    except Exception as e:
        print("Transferred interest token failed :{}".format(e))
        return
    print("Transferred interest token successfully")
    print(atn)
    print("--------------------------------------------")

    # transferring the par tokens to escrow account
    print("--------------------------------------------")
    print("Transfer par token to escrow account......")
    try:
        atn = asset_transaction(passphrase, vol, escrow_id, par_id, cl)
    except Exception as e:
        print("Transferred par token failed :{}".format(e))
        return
    print("Transferred par token successfully")
    print(atn)
    print("--------------------------------------------")
    print("Setup-complete!")
    return interest_id, par_id, escrow_result, escrow_id



#--------------------------------------------------------------------
# FOR DEMONSTRATION PURPOSE ONLY
#--------------------------------------------------------------------
# ADDRESSES(FOR DEMO ONLY)
pub_add = "YOUR ADDRESS"
pub_pass = "YOUR MNEMONIC"
buyer_add = "YOUR ADDRESS"
buyer_pass = "YOUR MNEMONIC"
#--------------------------------------------------------------------
# MANUALLY SETTING PARAMETER
closure = 12610711+ 18  # before which block purchase of bond is allowed
proj_name = "INFI1" # the name used for token issuance
payment_id = 14208367 # the asset used for purchase / payment
par = 10 # the par value of bond as measured in units of payment_id
coupon = 1 # the coupon value of bond as measured in units of payment_id
vol = 1000 # total number of bond available
total_payments = 10 # how many interest payments in total
amt = 2 # number of bonds to be purchased by buyer
#--------------------------------------------------------------------
# PRESET PARAMETERS
period = 10 # how many blocks between two interest payments
first_coupon_payment = closure + 1 # the first block from which a bondholder is allowed to claim interest
span = 500 # the length of interest payment period (exaggerated for demo purpose)
client = algod_client()
#--------------------------------------------------------------------
# SETTING UP TOKENS, ESCROW ACCOUNT
interest_id, par_id, escrow_result, escrow_id= main_pub(passphrase=pub_pass, proj_name=proj_name,
         vol=vol, url="https://asdfsodf", par=par, coupon=coupon, payment_id=payment_id, closure=closure,
         start_round=first_coupon_payment, period=period, total_payments=10, span=span, hold_up=13200000,client=client)
#--------------------------------------------------------------------
# BUYER PURCHASING
params = client.suggested_params()
first = params.first
last = params.last
purchase_bond(programstr=escrow_result, escrow_id=escrow_id, passphrase=buyer_pass,
              amt=2, payment_id=payment_id, par=par,  interest_id=interest_id, # interest_id
              par_id=par_id, total_payments=10, algod_client=client, first_block=first, last_block=last)
#--------------------------------------------------------------------
# CLAIM INTEREST
claim_interest(programstr=escrow_result, escrow_id=escrow_id, passphrase=buyer_pass,
               amt=2, coupon=coupon, payment_id=payment_id, interest_id=interest_id, par_id=par_id,
               first_block=first_coupon_payment, last_block=first_coupon_payment + span, algod_client=client)
#--------------------------------------------------------------------
