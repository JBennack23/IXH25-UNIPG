import random
import json
import hashlib
import pickle

from phe import paillier as pa
from ecdsa import SigningKey, VerifyingKey, NIST256p

import blockchain as bc

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
    print(f"\u001B[1;36m[DEBUG] t1: {t1}\u001B[0m.")
    print(f"\u001B[1;36m[DEBUG] t2: {t2}\u001B[0m.")
    for i in range(0, 10):
        if t1[i] != t2[i]:
            return False
    return True

def sign_m(m: list[int], signing_key) -> tuple:
    """
    Sign a list of flags representing a car.

    Args:
        m (list[int]): The list to sign.
        signing_key (_type_): The key to use for signing.

    Returns:
        str: The signed list, ready to be sent to the server and its signature.
    """
    m1 = m.copy()
    for i in range(0, 10):
        m1[i] = str(m1[i].ciphertext())
    message = json.dumps(m1, sort_keys=True).encode('utf-8')
    signature = signing_key.sign_deterministic(
        message,
        hashfunc=hashlib.sha256
    )

    return m, message, signature

def verify_sign(message: str, signature: any, verify_key) -> bool:
    """
    Verifies the sign of the message

    Args:
        message (str): The message to verify.
        signature (any): The signature of the message.
        verify_key (_type_): The key to be used to verify.

    Returns:
        bool: `True` if the signature is valid, `False` otherwise.
    """
    try:
        verify_key.verify(signature, message, hashfunc=hashlib.sha256)
        return True
    except Exception:
        return False

def speed(car: list[int]) -> int:
    return int(hashlib.sha256(pickle.dumps(car)).hexdigest(), base=16) / (2 ** 256) * 100

# Initializations:

print("\t\u001B[1;33m---Init Phase ---\u001B[0m")

# Blockchain creation
print("- Creating Blockchain...")
chain = bc.Blockchain()
print("- Creating wallets...")
w1: bc.Wallet = chain.create_wallet()
print(f". Done. The balance of a wallet is {chain.get_balance(w1.address)}XPF.")
print("- Creating keys for digital signatures.")

client_keys: dict = {}
client_keys["private_key"] = SigningKey.generate(curve=NIST256p)
client_keys["public_key"] = client_keys["private_key"].get_verifying_key()

server_keys: dict = {}
server_keys["private_key"] = SigningKey.generate(curve=NIST256p)
server_keys["public_key"] = server_keys["private_key"].get_verifying_key()

print(f"[Client Signature Key]: \u001B[1;35m{client_keys['public_key'].to_string().hex()}\u001B[0m.")
print(f"[Server Signature Key]: \u001B[1;35m{server_keys['public_key'].to_string().hex()}\u001B[0m.")

print("\t\u001B[1;34m---Handshake Phase ---\u001B[0m")

# A Paillier Key-Pair is generated:
public_key, private_key = pa.generate_paillier_keypair()
# Public key is given to the two parts (client & server), but not private:
client_key: pa.PaillierPublicKey = public_key
server_key: pa.PaillierPublicKey = public_key

# Client Setup - Generate a Random m_c and encrypt it with its key:
m_c: list[int] = [random.randint(1, 499) for _ in range(0, 10)]
print(f"- Client generated iV: {m_c}.")

e_mc = encrypt_m(client_key, m_c)
print("- Client encrypted its iV and sent it to the client.")
server_inbox = sign_m(e_mc, client_keys["private_key"])

# Server Setup - Does the same as the client:
m_s: list[int] = [random.randint(1, 999) for _ in range(0, 10)]
print(f"- Server generated iV: {m_s}.")

e_ms = encrypt_m(server_key, m_s)
print("- Client encrypted its iV and sent it to the client.")
client_inbox = sign_m(e_ms, server_keys["private_key"])

# Now, the final (initial) car flags array is obtained by both summing the two lists:
if not verify_sign(client_inbox[1], client_inbox[2], server_keys["public_key"]):
    print("! Signature Verification Failed. Comunication Aborted.")
    exit(3)
car_client = [] # The client can have multiple cars
car_client.append(sum_cars(e_mc, client_inbox[0]))

if not verify_sign(server_inbox[1], server_inbox[2], client_keys["public_key"]):
    print("! Signature Verification Failed. Comunication Aborted.")
    exit(3)
car_server = {
    "c1": [sum_cars(e_ms, server_inbox[0])] # The array of the cars owned by this specific client
}

print(f"- Car speed is: \u001B[1;22m{speed(car_client[0])}\u001B[0m.")

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
# Encrypt it with same key of m
train_m = encrypt_m(server_key, train_m)
print("- Server generated a train vector and sends it to client.")
# Validate client payment:
mined_block = chain.mine_pending_transactions(miner_address=w1.address)
print(f"Mined block {mined_block.index}, hash: {mined_block.hash}, nonce: {mined_block.nonce}")

client_inbox = sign_m(train_m, server_keys["private_key"])
if not verify_sign(client_inbox[1], client_inbox[2], server_keys["public_key"]):
    print("! Signature Verification Failed. Comunication Aborted.")
    exit(3)
car_server["c1"][len(car_server["c1"]) - 1] = sum_cars(car_server["c1"][0], train_m)
car_client[0] = sum_cars(car_client[0], client_inbox[0])
print(f"The speed of the car now is: \u001B[1;22m{speed(car_client[0])}\u001B[0m.")

if car_check(car_client[0], car_server["c1"][0], private_key):
    print("> Training has been completed correctly.")
else:
    print("! Training failed!")
    exit(2)
