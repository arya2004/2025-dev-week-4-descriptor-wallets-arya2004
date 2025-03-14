import requests
from bip_utils import Bip32Secp256k1, P2WPKHAddr

def main():
    
    descriptor = "wpkh(tpubD6NzVbkrYhZ4XgiXtGrdW5XDAPFCL9h7we1vwNCpn8tGbBcgfVYjXyhWo4E1xkh56hjod1RhGjxbaTLV3X4FyWuejifB9jusQ46QzG87VKp/*)#adv567t2"
    
    
    start = descriptor.find("wpkh(") + len("wpkh(")
    end = descriptor.find("/*")
    xpub = descriptor[start:end]

   
    hrp = "bcrt"
    
    
    api_base = "http://localhost:8094/regtest/api"
    
    total_satoshis = 0
    gap_limit = 20  

    
    bip32_ctx = Bip32Secp256k1.FromExtendedKey(xpub)
    
    for i in range(gap_limit):
        # Derive child key at index i.
        child_node = bip32_ctx.DerivePath(str(i))
        pub_key_bytes = child_node.PublicKey().RawCompressed().ToBytes()
        # Generate a bech32 P2WPKH address (wpkh) using the HRP "bcrt"
        address = P2WPKHAddr.EncodeKey(pub_key_bytes, hrp)
        
        
        url = f"{api_base}/address/{address}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                chain_stats = data.get("chain_stats", {})
                funded = chain_stats.get("funded_txo_sum", 0)
                spent = chain_stats.get("spent_txo_sum", 0)
                balance = funded - spent
                total_satoshis += balance
            else:
                print(f"Failed to fetch data for address {address}: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error fetching data for address {address}: {e}")

   
    total_btc = total_satoshis / 1e8

    
    with open("out.txt", "w") as f:
        f.write(str(total_btc))

if __name__ == "__main__":
    main()
