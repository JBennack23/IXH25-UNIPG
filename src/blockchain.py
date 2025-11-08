# Simple Blockchain simulation for a cryptocurrency "XPF"
# - Account model (balances stored in chain state)
# - Wallets initialized with 10 XPF on creation
# - Lightweight "signature" scheme for simulation purposes (HMAC-like using wallet private key)
# - Mining with simple proof-of-work

import hashlib, json, time, secrets
from dataclasses import dataclass
from typing import List, Optional

# ----------------------- Utilities -----------------------
def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def current_time() -> float:
    return time.time()

# ----------------------- Data Classes -----------------------
@dataclass
class Transaction:
    sender: str  # address (or "SYSTEM" for minting)
    recipient: str
    amount: float
    timestamp: float
    signature: Optional[str] = None  # created by wallet (simulated)

    def to_json(self, include_signature: bool = True) -> str:
        d = {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp
        }
        if include_signature and self.signature is not None:
            d["signature"] = self.signature
        return json.dumps(d, sort_keys=True)

    def hash(self) -> str:
        return sha256(self.to_json(include_signature=True))

@dataclass
class Block:
    index: int
    prev_hash: str
    timestamp: float
    transactions: List[Transaction]
    nonce: int = 0
    hash: Optional[str] = None

    def compute_hash(self) -> str:
        tx_json = json.dumps([tx.to_json() for tx in self.transactions], sort_keys=True)
        block_string = f"{self.index}{self.prev_hash}{self.timestamp}{tx_json}{self.nonce}"
        return sha256(block_string)

# ----------------------- Wallet (simulation) -----------------------
class Wallet:
    def __init__(self):
        # private_key is kept secret in this simulation; address is derived deterministically
        self.private_key = secrets.token_hex(32)
        # address = short prefix of sha256(private_key)
        self.address = sha256(self.private_key)[:40]

    def sign(self, message: str) -> str:
        # Simulated signature: sha256(private_key + message)
        return sha256(self.private_key + message)

    def __repr__(self):
        return f"Wallet(address={self.address})"

# ----------------------- Blockchain -----------------------
class Blockchain:
    def __init__(self, difficulty: int = 3):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty = difficulty  # number of leading zeros required in block hash (for mined blocks)
        # registry to hold wallets for signature verification in this simulation environment
        # maps address -> private_key (ONLY for local simulation/testing). Never do this in real systems.
        self._wallet_registry = {}
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis_block = Block(index=0, prev_hash="0", timestamp=current_time(), transactions=[], nonce=0)
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    # Wallet creation: register wallet and immediately credit 10 XPF via a confirmed SYSTEM transaction
    def create_wallet(self) -> Wallet:
        w = Wallet()
        # register the wallet (simulation only)
        self._wallet_registry[w.address] = w.private_key
        # mint 10 XPF to this wallet via SYSTEM transaction AND confirm it immediately by creating a new block
        tx = Transaction(sender="SYSTEM", recipient=w.address, amount=10.0, timestamp=current_time(), signature=None)
        # create a block that contains only this SYSTEM mint transaction and append it to the chain
        mint_block = Block(index=len(self.chain), prev_hash=self.chain[-1].hash, timestamp=current_time(), transactions=[tx], nonce=0)
        # we do NOT perform proof-of-work for SYSTEM-created mint blocks: compute hash directly
        mint_block.hash = mint_block.compute_hash()
        self.chain.append(mint_block)
        return w

    def get_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount
        # pending transactions are not counted as confirmed balance (so wallets cannot spend pending incoming)
        return balance

    def create_transaction(self, sender_private_key: str, recipient: str, amount: float) -> Transaction:
        # derive sender address from private key to prevent forging
        sender_address = sha256(sender_private_key)[:40]
        tx = Transaction(sender=sender_address, recipient=recipient, amount=amount, timestamp=current_time())
        # create signature (simulation)
        tx.signature = sha256(sender_private_key + tx.to_json(include_signature=False))
        # validate before accepting
        if not self._verify_transaction(tx):
            raise ValueError("Transaction verification failed or insufficient balance.")
        self.pending_transactions.append(tx)
        return tx

    def _verify_transaction(self, tx: Transaction) -> bool:
        # SYSTEM transactions are allowed without signature (minting)
        if tx.sender == "SYSTEM":
            return True
        # Check that sender is known in registry (simulation)
        if tx.sender not in self._wallet_registry:
            print("Unknown sender address:", tx.sender)
            return False
        private_key = self._wallet_registry[tx.sender]
        # recompute signature
        expected_sig = sha256(private_key + tx.to_json(include_signature=False))
        if expected_sig != tx.signature:
            print("Invalid signature for tx:", tx.to_json())
            return False
        # check balance (only confirmed balance is considered)
        if self.get_balance(tx.sender) < tx.amount:
            print("Insufficient balance for tx:", tx.to_json())
            return False
        return True

    def mine_pending_transactions(self, miner_address: str) -> Block:
        """
        Mines a block containing the current pending transactions.
        Note: mining does NOT give a reward in this design.
        Miner address parameter is kept for compatibility (could be used for fees).
        """
        if not self.pending_transactions:
            raise ValueError("No transactions to mine")

        # include only the pending transactions (no SYSTEM mining reward)
        block_txs = list(self.pending_transactions)
        new_block = Block(index=len(self.chain), prev_hash=self.chain[-1].hash, timestamp=current_time(), transactions=block_txs)
        # proof-of-work
        target = "0" * self.difficulty
        while True:
            new_hash = new_block.compute_hash()
            if new_hash.startswith(target):
                new_block.hash = new_hash
                break
            new_block.nonce += 1
        # add block and clear pending transactions
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i-1]
            # Recompute hash and compare. Note: SYSTEM mint blocks were created without PoW but their hash must still match compute_hash()
            if current.hash != current.compute_hash():
                print(f"Invalid hash at block {i}")
                return False
            if current.prev_hash != prev.hash:
                print(f"Invalid prev_hash at block {i}")
                return False
            # verify transactions inside (signatures & balances)
            # For simplicity we verify signatures (if not SYSTEM) but we don't attempt to re-run sequential balance simulations here
            for tx in current.transactions:
                if tx.sender != "SYSTEM":
                    if tx.sender not in self._wallet_registry:
                        print("Unknown sender in chain:", tx.sender)
                        return False
                    expected = sha256(self._wallet_registry[tx.sender] + tx.to_json(include_signature=False))
                    if tx.signature != expected:
                        print("Invalid signature in block", i, "tx:", tx.to_json())
                        return False
        return True

    # helper to pretty-print balances for all registered wallets
    def all_balances(self):
        balances = {}
        for addr in self._wallet_registry.keys():
            balances[addr] = self.get_balance(addr)
        return balances

# ----------------------- Demonstration -----------------------
if __name__ == "__main__":
    chain = Blockchain(difficulty=3)
    print("Blockchain created. Genesis block hash:", chain.chain[0].hash)

    # create two wallets (each will receive 10 XPF immediately, confirmed)
    w1 = chain.create_wallet()
    w2 = chain.create_wallet()
    print("\nCreated wallets:")
    print("w1:", w1.address)
    print("w2:", w2.address)
    print("\nBalances AFTER wallet creation (should be 10 each):")
    print("w1:", chain.get_balance(w1.address))
    print("w2:", chain.get_balance(w2.address))

    # w1 sends 4 XPF to w2
    print("\nw1 sends 4 XPF to w2 (creating and adding transaction to pending):")
    tx1 = chain.create_transaction(sender_private_key=w1.private_key, recipient=w2.address, amount=4.0)
    print("Pending tx:", tx1.to_json())

    # attempt invalid transaction: w2 sends 20 XPF to w1 (insufficient funds)
    print("\nAttempting invalid transaction (w2 -> w1, amount 20):")
    try:
        chain.create_transaction(sender_private_key=w2.private_key, recipient=w1.address, amount=20.0)
    except ValueError as e:
        print("Failed as expected:", e)

    # mine pending transactions (no reward is assigned)
    print("\nMining pending transactions (miner is w2) - no mining reward in this design:")
    mined_block = chain.mine_pending_transactions(miner_address=w2.address)
    print("Mined block", mined_block.index, "hash:", mined_block.hash, "nonce:", mined_block.nonce)

    print("\nFinal balances (confirmed):")
    print("w1:", chain.get_balance(w1.address))
    print("w2:", chain.get_balance(w2.address))

    # Check chain validity
    print("\nIs blockchain valid?", chain.is_chain_valid())

    # show all balances for registered wallets
    print("\nAll wallet balances:")
    for addr, bal in chain.all_balances().items():
        print(addr, "->", bal)
