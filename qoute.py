#Get Qoute on any token using qouter contract


from web3 import Web3
from web3.middleware import geth_poa_middleware
import json

# Connect to BSC node
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# PancakeSwap V3 Quoter address
QUOTER_ADDRESS = '0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997'

# WBNB address (Wrapped BNB)
WBNB_ADDRESS = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'

# Quoter ABI
QUOTER_ABI = json.loads('''
[
    {
        "inputs": [
            {"internalType": "bytes", "name": "path", "type": "bytes"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"}
        ],
        "name": "quoteExactInput",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "uint160[]", "name": "sqrtPriceX96AfterList", "type": "uint160[]"},
            {"internalType": "uint32[]", "name": "initializedTicksCrossedList", "type": "uint32[]"},
            {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
''')

# ERC20 ABI (for decimals)
ERC20_ABI = json.loads('''
[
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]
''')

def encode_path(token_in, token_out, fee):
    return token_in + fee.to_bytes(3, 'big') + token_out

def debug_pancakeswap_v3_buy(token_address, bnb_amount):
    quoter_contract = w3.eth.contract(address=QUOTER_ADDRESS, abi=QUOTER_ABI)
    token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    
    # Get token decimals
    token_decimals = token_contract.functions.decimals().call()

    token_in, token_out = WBNB_ADDRESS, token_address
    amount_in = bnb_amount
    
    # Try different fee tiers
    fee_tiers = [100, 500, 2500, 10000]
    
    for fee in fee_tiers:
        print(f"\nTrying fee tier: {fee}")
        
        # Encode the path
        path = encode_path(Web3.to_bytes(hexstr=token_in), Web3.to_bytes(hexstr=token_out), fee)
        
        try:
            # Call the quoter contract
            quote = quoter_contract.functions.quoteExactInput(path, amount_in).call()
            amount_out = quote[0]
            
            tokens_received_formatted = amount_out / (10 ** token_decimals)

            print(f"Quote successful for fee tier {fee}.")
            print(f"Estimated tokens to receive: {tokens_received_formatted} (raw: {amount_out})")
            return True, tokens_received_formatted, amount_out
        except Exception as e:
            error_message = str(e)
            print(f"Quote failed for fee tier {fee}. Error: {error_message}")
    
    print("All fee tiers failed. The token might not be available on PancakeSwap V3 or there might be insufficient liquidity.")
    return False, 0, 0

# Example usage
token_address = '0x1C45366641014069114c78962bDc371F534Bc81c'  # Replace with the address of the token you want to test
bnb_amount_to_trade = Web3.to_wei(0.01, 'ether')  # 0.01 BNB for buy

print("Debugging buy simulation:")
success, tokens_received, raw_amount = debug_pancakeswap_v3_buy(token_address, bnb_amount_to_trade)

if success:
    print("\nQuote simulation was successful.")
    print(f"Estimated tokens to receive: {tokens_received}")
    print(f"Raw amount: {raw_amount}")
else:
    print("\nQuote simulation failed for all fee tiers. Please check the error messages above.")


