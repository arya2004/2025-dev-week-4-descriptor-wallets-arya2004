import requests
from bip_utils import Bip32Slip10Secp256k1, Bip32KeyNetVersions, P2WPKHAddr

# The descriptor provided:
DESCRIPTOR = "wpkh(tpubD6NzVbkrYhZ4XgiXtGrdW5XDAPFCL9h7we1vwNCpn8tGbBcgfVYjXyhWo4E1xkh56hjod1RhGjxbaTLV3X4FyWuejifB9jusQ46QzG87VKp/*)#adv567t2"

# Esplora API Base URL
BASE_URL = "http://localhost:8094/regtest/api"

def extract_xpub(descriptor: str) -> str:
    """ Extract the XPUB from the descriptor """
    start = descriptor.find("(")
    end = descriptor.find("/*")
    if start == -1 or end == -1:
        raise ValueError("Invalid descriptor format")
    return descriptor[start + 1 : end]

def derive_address(xpub: str, index: int) -> str:
    """ Derive a P2WPKH (SegWit) address from the XPUB at a given index """
    key_net_ver = Bip32KeyNetVersions(b'\x04\x35\x87\xcf', b'\x04\x35\x83\x94')  # Testnet versions
    bip32_ctx = Bip32Slip10Secp256k1.FromExtendedKey(xpub, key_net_ver=key_net_ver)
    
    try:
        child_key = bip32_ctx.ChildKey(index)
        pub_key_bytes = child_key.PublicKey().RawCompressed().ToBytes()
        address = P2WPKHAddr.EncodeKey(pub_key_bytes, hrp="bcrt")  # "bcrt" for regtest
        return address
    except Exception as e:
        print(f"Error deriving address at index {index}: {e}")
        return None

def get_utxos(address: str) -> list:
    """ Fetch UTXOs for a given address using the Esplora API """
    url = f"{BASE_URL}/address/{address}/utxo"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        utxos = response.json()

        # Debugging: Print API Response
        print(f"Checking Address: {address}")
        if utxos:
            print(f"UTXOs: {utxos}")
        else:
            print(f"No UTXOs found for address {address}")

        return utxos  # List of UTXO objects
    except requests.exceptions.RequestException as e:
        print(f"Error fetching UTXOs for {address}: {e}")
        return []

def main():
    """ Main function to calculate the total balance """
    xpub = extract_xpub(DESCRIPTOR)
    total_satoshis = 0
    index = 0
    consecutive_empty = 0
    EMPTY_THRESHOLD = 20  # Stop scanning after 20 empty addresses

    while consecutive_empty < EMPTY_THRESHOLD:
        addr = derive_address(xpub, index)
        if addr is None:
            print(f"Skipping index {index} due to address derivation failure.")
            break

        utxos = get_utxos(addr)
        if utxos:
            consecutive_empty = 0  # Reset counter if UTXOs found
            for utxo in utxos:
                total_satoshis += utxo.get("value", 0)
        else:
            consecutive_empty += 1

        index += 1

    total_btc = total_satoshis / 1e8
    balance_str = f"{total_btc:.8f}"

    with open("out.txt", "w") as f:
        f.write(balance_str)

    print(f"Total Balance: {balance_str} BTC (saved to out.txt)")

if __name__ == "__main__":
    main()
