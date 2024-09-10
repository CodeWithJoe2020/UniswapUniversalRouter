from web3 import Web3; w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/')) # example uses base
from os import getenv
from dotenv import load_dotenv
load_dotenv()
import json
import time
eoa = w3.eth.account.from_key('')                              # replace with your own set up
#----------------------
pk = ''

PERMIT_ADDRESS  = '0x31c2F6fcFf4F8759b3Bd5Bf0e1084A055615c768'
BRETT_ADDRESS   = '0x1C45366641014069114c78962bDc371F534Bc81c'
WETH_ADDRESS    = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
ROUTER_ADDRESS  = '0x1A0A18AC4BECDDbd6389559687d1A73d8927E416'               # always double check the addresses 


with open('universal_router_abi.json', 'r') as file:
    router = json.load(file)



with open('erc20.json', 'r') as file:
    erc20 = json.load(file)

ROUTER_ABI = router

ERC20_ABI = erc20
router = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
token  = w3.eth.contract(address=BRETT_ADDRESS,  abi=ERC20_ABI )


commands = '0x0b00'
from eth_abi import encode
from eth_abi.packed import encode_packed
# some sane inputs (sane doesn't mean safe in this case, always use a good slippage value unless protected some other way)
to = eoa.address
amount = w3.to_wei(0.001, 'ether')
slippage = 3000
FEE = 10000                   #100,500,3000,10000
# (address tokenIn, uint24 fee, address tokenOut)
path = encode_packed(['address','uint24','address'], [WETH_ADDRESS, FEE, BRETT_ADDRESS])
from_eoa = False # the router or user? router after wrapping

wrap_calldata = encode(['address', 'uint256'], [router.address, amount])
v3_calldata = encode(['address', 'uint256', 'uint256', 'bytes', 'bool'], [to, amount, slippage, path, from_eoa])

deadline = 2*10**10

print(commands)
print(wrap_calldata.hex())
print(v3_calldata.hex())
print(deadline)
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------

tx = {
        'from': eoa.address,
        'value': amount,
        'chainId': 56,
        'gas': 400000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(eoa.address)
}

def sign_tx(tx, key):
  sig = w3.eth.account.sign_transaction
  signed_tx = sig(tx, private_key=key)
  return signed_tx

def send_tx(signed_tx):
  w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  tx_hash = w3.to_hex(w3.keccak(signed_tx.rawTransaction))
  return tx_hash

def main():
  swap = router.functions.execute(commands, [wrap_calldata, v3_calldata], deadline).build_transaction(tx)
  # print(swap)
  # print('[-] Simulating swap...')
  # w3.eth.call(swap)
  print('[-] Attempting swap...')
  tx_hash = send_tx(sign_tx(swap, pk))
  receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
  print (f'[>] Hash of swap: {tx_hash}\n[>] {receipt}')

if __name__ == '__main__':
  main()
