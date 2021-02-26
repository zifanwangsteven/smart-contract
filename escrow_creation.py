from contract import compile
import base64
from algosdk.future.transaction import  PaymentTxn, LogicSigTransaction
def create_escrow(mgr_add: str, proj_name: str, interest_id: int, par_id: int, payment_id: int,
                  begin_round: int, end_round: int, par: int, coupon: int, period: int, span: int, holdup: int, algod_client) -> str:
    """

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

    program = compile(mgr_add, interest_id, par_id, payment_id, par,
                      coupon, holdup, begin_round, end_round, period,
                      span, proj_name)

    raw_teal = "./teal/{}.teal".format(proj_name)
    data = open(raw_teal, 'r').read()

    try:
        response = algod_client.compile(data)
        return response['hash']
    except Exception as e:
        return str(e)

