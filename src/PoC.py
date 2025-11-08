import random
import blockchain as bc
from phe import paillier as pa

def sum_cars(m1: list[int], m2: list[int]) -> list[int]:
    """
    Sum two car vectors, elementwise.

    Args:
        m1 (list[int]): The list of flags for the first car.
        m2 (list[int]): The list of flags for the second car.

    Returns:
        list[int]: The sum result.
    """
    res = []
    for i in range(0, 10):
        res.append(m1[i] + m2[i])
    return res

def encrypt_m(key: pa.PaillierPublicKey, m: list[int]) -> list:
    """
    Encrypt the list of integers (flags) representing a car.

    Args:
        key (pa.PaillierPublicKey): The key to use for encryption.
        m (list[int]): The list of flags representing the car.

    Returns:
        list: The encrypted list of flags.
    """
    enc = []
    for el in m:
        enc.append(key.encrypt(el))
    return enc

def decrypt_m(key: pa.PaillierPrivateKey, m: list[int]) -> list:
    """
    Decrypt the list of integers (flags) representing a car.

    Args:
        key (pa.PaillierPublicKey): The key to use for decryption.
        m (list[int]): The (encrypted) list of flags representing the car.

    Returns:
        list: The decrypted list of flags.
    """
    dec = []
    for el in m:
        dec.append(key.decrypt(el))
    return dec

def car_check(car_client: list[int], car_server: list[int], key: pa.PaillierPrivateKey) -> bool:
    t1 = decrypt_m(key, car_client) # First car decrypt
    t2 = decrypt_m(key, car_server) # First car decrypt
    print(f"t1: {t1}")
    print(f"t2: {t2}")
    if t1 == t2:
        return True
    return False

# Initializations:

print("\t\u001B[1;33m---Init Phase ---\u001B[0m")

# Blockchain creation
print("- Creating Blockchain...")
chain = bc.Blockchain()
print("- Creating wallets...")
w1: bc.Wallet = chain.create_wallet()
print(f". Done. The balance of a wallet is {chain.get_balance(w1.address)}XPF.")

print("\t\u001B[1;34m---Handshake Phase ---\u001B[0m")

# A Paillier Key-Pair is generated:
public_key, private_key = pa.generate_paillier_keypair()
# Public key is given to the two parts (client & server), but not public:
client_key: pa.PaillierPublicKey = public_key
server_key: pa.PaillierPublicKey = public_key

# Client Setup - Generate a Random m_c and encrypt it with its key:
m_c: list[int] = [random.randint(1, 499) for _ in range(0, 10)]
print(f"- Client generated iV: {m_c}.")

e_mc = encrypt_m(client_key, m_c)
print("- Client encrypted its iV and sent it to the client.")
server_inbox = e_mc

# Server Setup - Does the same as the client:
m_s: list[int] = [random.randint(1, 999) for _ in range(0, 10)]
print(f"- Server generated iV: {m_s}.")

e_ms = encrypt_m(server_key, m_s)
print("- Client encrypted its iV and sent it to the client.")
client_inbox = e_ms

# Now, the final (initial) car flags array is obtained by both summing the two lists:
car_client = [] # The client can have multiple cars
car_client.append(sum_cars(e_mc, client_inbox))

car_server = {
    "c1": [sum_cars(e_ms, server_inbox)] # The array of the cars owned by this specific client
}

# DEBUG CHECK---
if car_check(car_client[0], car_server["c1"][0], private_key):
    print("> Both Client & Server now have the same iV for the user's car.")
else:
    print("! Error in initialization.")
    exit(1)
# END DEBUG CHECK---

print("\t\u001B[1;32m---Training Phase ---\u001B[0m")
print("- Client \"c1\" requested a training.")
chain.create_transaction(sender_private_key=w1.private_key, recipient="SYSTEM", amount=1.0)
server_inbox = w1

# Server generates a random training vector:
train_m: list[int] = [random.randint(-19, 19) for _ in range(0, 10)]
print("- Server generated a train vector and sends it to client.")
# Validate client payment:
mined_block = chain.mine_pending_transactions(miner_address=w1.address)
print(f"Mined block {mined_block.index}, hash: {mined_block.hash}, nonce: {mined_block.nonce}")

client_inbox = train_m
car_server["c1"][len(car_server["c1"]) - 1] = sum_cars(car_server["c1"][0], train_m)
car_client[0] = sum_cars(car_client[0], client_inbox)

if car_check(car_client[0], car_server["c1"][0], private_key):
    print("> Training has been completed correctly.")
else:
    print("! Training failed!")
    exit(2)
