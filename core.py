from time import sleep
from web3 import Web3
import tomllib
import json

with open("config.toml", "rb") as config_file:
    config = tomllib.load(config_file)
with open("abi.json", "r") as config_file:
    abi = json.load(config_file)

w3 = Web3(Web3.HTTPProvider(config["PRIVATE"]["WSS_APIKEY"]))
contract = w3.eth.contract(
    address=config["PUBLIC"]["marimo_address"], abi=abi)


def check_marimo():
    block = w3.eth.get_block(block_identifier="latest")
    base_fee_per_gas = getattr(block, "baseFeePerGas")
    gas_in_gwei = Web3.from_wei(base_fee_per_gas, "gwei")
    # check for gas price
    print(
        f"bh: {getattr(block, 'number')}")
    if gas_in_gwei > config["PUBLIC"]["gas_price"]:
        print(f"Gas too expensive. {gas_in_gwei} GWEI")
    else:
        # get all marimbo from PUBLIC_KEY acc and iterate over it
        marimos_owned = contract.functions.tokensOfOwner(
            config["PRIVATE"]["PUBLIC_KEY"]).call()
        for marimo_id in marimos_owned:
            marimo_life = contract.functions.getElapsedTimeFromLastWaterChanged(
                marimo_id).call()
            life_threshold = 60 * 60 * 24 * \
                (100 - config["PUBLIC"]["water_clarity"])
            # check for marimos life
            if marimo_life < life_threshold:
                print("Marimo life is good.")
            else:
                print(
                    f"Marimo life is {marimo_life / 60 / 60 / 24} days")
                nonce = w3.eth.get_transaction_count(
                    config["PRIVATE"]["PUBLIC_KEY"])
                marimo_txn = contract.functions.changeWater(marimo_id).build_transaction({
                    'chainId': 1,
                    'gas': 300000,
                    'maxFeePerGas': base_fee_per_gas,
                    'maxPriorityFeePerGas': w3.to_wei('1', 'gwei'),
                    "nonce": nonce
                })
                signed_txn = w3.eth.account.sign_transaction(
                    marimo_txn,
                    private_key=config["PRIVATE"]["PRIVATE_KEY"]
                )
                w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                print(signed_txn.hash)
                receipt = w3.eth.wait_for_transaction_receipt(signed_txn.hash)
                print(receipt)


if __name__ == '__main__':
    while True:
        check_marimo()
        sleep(5)
