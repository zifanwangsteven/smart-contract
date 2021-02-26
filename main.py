from algosdk import account, mnemonic
from contract import compile
from utilities.wait import wait_for_confirmation
from utilities.alg_cl import algod_client
from utilities.payment import payment_transaction
from utilities.asset_config import interest_token_issuance, par_token_issuance
from algosdk.future.transaction import LogicSig
from utilities.chk_bal import check_balance
import os
import base64
import json

algod_client = algod_client()
passphrase = "connect another slight account merry project usage debris ignore achieve differ holiday cover annual adult poet lock minimum average occur melt renew nominee about list"
interest_tx, interest_id = interest_token_issuance(algod_client, passphrase, "Road", 1000, "https://something", 10)
par_tx, par_id = par_token_issuance(algod_client, passphrase, "test", 1000, "https://something")
print("Interest token issued id: {}".format(interest_id))
print("Par token issued id: {}".format(par_id))