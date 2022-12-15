import asyncio
import os
from web3 import Web3
from dotenv import load_dotenv
load_dotenv()

CONFIG = {
    "water_clarity": 81,
    "gas_price": 15,
    "marimo_address": "0xA35aa193f94A90eca0AE2a3fB5616E53C1F35193",
    "marimo_abi": [
        {
            "inputs": [
                {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
            ],
            "name": "changeWater",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
            ],
            "name": "getElapsedTimeFromLastWaterChanged",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "owner", "type": "address"}
            ],
            "name": "tokensOfOwner",
            "outputs": [
                {"internalType": "uint256[]", "name": "", "type": "uint256[]"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
    ]
}


w3 = Web3(Web3.WebsocketProvider(os.environ.get("WSS_APIKEY")))
contract = w3.eth.contract(
    address=CONFIG["marimo_address"], abi=CONFIG["marimo_abi"])


def check_marimo():
    block = w3.eth.get_block(block_identifier="latest")
    base_fee_per_gas = block["baseFeePerGas"]
    gas_in_gwei = Web3.fromWei(base_fee_per_gas, "gwei")
    # check for gas price
    print(
        f"bh: {block['number']}")
    if gas_in_gwei > CONFIG["gas_price"]:
        print(f"Gas too expensive. {gas_in_gwei} GWEI")
    else:
        # get all marimbo from PUBLIC_KEY acc and iterate over it
        marimos_owned = contract.functions.tokensOfOwner(
            os.environ.get("PUBLIC_KEY")).call()
        for marimo_id in marimos_owned:
            marimo_life = contract.functions.getElapsedTimeFromLastWaterChanged(
                marimo_id).call()
            life_threshold = 60 * 60 * 24 * (100 - CONFIG["water_clarity"])
            # check for marimos life
            if marimo_life < life_threshold:
                print("Marimo life is good.")
            else:
                print(
                    f"Marimo life is {marimo_life / 60 / 60 / 24} days")
                nonce = w3.eth.get_transaction_count(
                    os.environ.get("PUBLIC_KEY"))
                print(nonce)
                marimo_txn = contract.functions.changeWater(marimo_id).build_transaction({
                    'maxFeePerGas': w3.toWei(CONFIG["gas_price"], 'gwei'),
                    'maxPriorityFeePerGas': w3.toWei('1', 'gwei'),
                    "nonce": nonce
                })
                signed_txn = w3.eth.account.sign_transaction(
                    marimo_txn,
                    private_key=os.environ.get("PRIVATE_KEY")
                )
                tx = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                print(tx)
                receipt = w3.eth.wait_for_transaction_receipt(tx)
                print(receipt)


async def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            check_marimo()
            await asyncio.sleep(poll_interval)


def main():
    block_filter = w3.eth.filter("latest")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(log_loop(block_filter, 5)))
    finally:
        loop.close()


if __name__ == '__main__':
    main()
