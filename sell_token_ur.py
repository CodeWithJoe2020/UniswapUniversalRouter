from web3 import Web3; w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/')) # example uses base
from os import getenv
from dotenv import load_dotenv
load_dotenv()
import json
import time
eoa = w3.eth.account.from_key('')                              # replace with your own set up
#----------------------

PERMIT_ADDRESS  = '0x31c2F6fcFf4F8759b3Bd5Bf0e1084A055615c768'
BRETT_ADDRESS   = '0x6894CDe390a3f51155ea41Ed24a33A4827d3063D'
WETH_ADDRESS    = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
ROUTER_ADDRESS  = '0x1A0A18AC4BECDDbd6389559687d1A73d8927E416'               # always double check the addresses 


with open('universal_router_abi.json', 'r') as file:
    router = json.load(file)

with open('permit.json', 'r') as file:
    permit = json.load(file)

with open('erc20.json', 'r') as file:
    erc20 = json.load(file)

ROUTER_ABI = router
PERMIT_ABI = permit
ERC20_ABI = erc20
router = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
permit = w3.eth.contract(address=PERMIT_ADDRESS, abi=PERMIT_ABI)
token  = w3.eth.contract(address=BRETT_ADDRESS,  abi=ERC20_ABI )

tx = {
        'from': eoa.address,
        'value': 0,
        'chainId': w3.eth.chain_id,
        'gas': 400000,
        'maxFeePerGas': w3.eth.gas_price * 2,
        'maxPriorityFeePerGas': w3.eth.max_priority_fee*2,
        'nonce': w3.eth.get_transaction_count(eoa.address)
}
#---------------------------------------------------------------
#  https://github.com/Uniswap/universal-router/blob/main/contracts/libraries/Commands.sol
#    uint256 constant V3_SWAP_EXACT_IN = 0x00;
#    uint256 constant UNWRAP_WETH = 0x0c;
# ----

# we will swap on v3 then unwrap the native token

commands = '0x000c'

from eth_abi import encode
from eth_abi.packed import encode_packed
# some sane inputs (sane doesn't mean safe in this case, always use a good slippage value unless protected some other way)
to = router.address  # router here, eoa address in unwrap
amount = 18000 * 10 ** 18
slippage = 10000
FEE = 100
path = encode_packed(['address','uint24','address'], [BRETT_ADDRESS, FEE, WETH_ADDRESS])
from_eoa = True
unwrap_calldata = encode(['address', 'uint256'], [eoa.address, slippage])
v3_calldata = encode(['address', 'uint256', 'uint256', 'bytes', 'bool'], [to, amount, slippage, path, from_eoa])
deadline = 2*10**10

# PERMIT
# Permit is a little involved, there are two ways you can do it. In both cases it is necessary to first perform
# a `classical` approval for the permit2 contract to move your tokens, as it is that contracts allowance that will be spent.
# this approval needs to be performed in a preceding transaction (unless as part of an atomic call from a custom contract for example)
# Following that approval we have two options we can explicitly "approve" the router as a spender of the permit2 contracts allowance in another transaction/call. # The benefit of this method is that the process is intuitive and familiar, it can be performed via a block explorer without any special encoding or signing.
# A second approach is to sign permit data (A set of encoded values), and send the signature for that permit along with the swap.
# While this method increases complexity a little it removes the need for the additional transaction to the permit2 contract to grant a approval to the router.

# We will keep it simple for this example:
approve_permit = token.functions.approve(PERMIT_ADDRESS, amount)
approve_router = permit.functions.approve(BRETT_ADDRESS, ROUTER_ADDRESS, amount, deadline)
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------


def sign_tx(tx, key):
  sig = w3.eth.account.sign_transaction
  signed_tx = sig(tx, private_key=key)
  return signed_tx

def send_tx(signed_tx):
  w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  tx_hash = w3.to_hex(w3.keccak(signed_tx.rawTransaction))
  return tx_hash

def main():

    approve1 = approve_permit.build_transaction(tx)
    print ('[-] Approving permit... ')
    tx_hash = send_tx(sign_tx(approve1, eoa.key))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print (f'[+] Approved PERMIT2 at TOKEN contract: {tx_hash}\n[>] {receipt}')

    tx.update({'nonce': w3.eth.get_transaction_count(eoa.address)+1})
    time.sleep(5)
    approve2 = approve_router.build_transaction(tx)
    print ('[-] Approving router... ')
    tx_hash = send_tx(sign_tx(approve2, eoa.key))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print (f'[+] Approved ROUTER at PERMIT contract: {tx_hash}\n[>] {receipt}')

    tx.update({'nonce': w3.eth.get_transaction_count(eoa.address)})
    
    swap = router.functions.execute(commands, [v3_calldata,unwrap_calldata], deadline).build_transaction(tx)
    print(swap)
    print('[-] Simulating swap...')
    #w3.eth.call(swap)
    print('[-] Attempting swap...')
    tx_hash = send_tx(sign_tx(swap, eoa.key))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print (f'[>] Hash of swap: {tx_hash}\n[>] {receipt}')

    

if __name__ == '__main__':
  main()
