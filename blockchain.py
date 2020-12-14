"""
David Moncayo
Blockchain Library Project

The main Chain class, this represents an individual
blockchain that is flexible with the data it can take
and is built in with hashing functions that handle
the blockchain functionality. All the data that can be added
to the blocks themselves is arbitrary and has a flexible
amount of use cases.
"""

import hashlib
import json
from os import urandom
from urllib.parse import urlparse
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import ec

class Chain:
    """
    Chain constructor

        id: any -> gives the blockchain a unique id
        data: dict -> data you would like to put into the genesis block
        exported: dict -> if the chain already exists you can import the genesis block
    """
    def __init__(self, id=None, data=None, exported=None):
        self._chain = []

        """
        Since multiple blockchains are used there
        must be some kind of identifier for each one
        to find and update it when necessary
        """
        self.id = id

        # Genesis block, extra data is optional
        if exported:
            self._chain.append(exported)
        else:
            self.new_block(previous_hash=1, data=data)
    
    """
    Create a new block in the chain

        previous_hash: hex -> a hashed value of the previous block in the chain
        data: dict -> extra data to be added into the block (can literally be anything)
    """
    def new_block(self, previous_hash, data=None):
        # Basic header for any block
        header = {
            'index': len(self._chain) + 1,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Ugly syntax for merging two dictionaries
        if data:
            block = {**header, **data}

        self._chain.append(block)
        return block

 
    """
    Prints the contents of the chain
    """
    def print_chain(self):
        print('============================')
        for block in self._chain:
            print(json.dumps(block, indent=4))
            print('============================')


    """
    Retrieves the last block of the chain

        return: dict -> the last block dictionary
    """
    @property
    def last_block(self):
        return self._chain[-1]


    """
    Retrieves the chain as an array

        return: dict[] -> array of dictionaries (blocks)
    """
    @property
    def chain(self):
        return self._chain


    """
    Helper method for returning a hash of a block

        return: hex -> a hashed value for a given block 
    """
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    """
    Determines if a chain is valid

        chain: Chain -> the given chain
        return: bool -> validity of the chain
    """
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            last_block = block
            current_index += 1

        return True



"""
The Node class that represents the identity of the server
running this code. It is equipped with a keypair for signing
transactions and functions for creating and verifying blocks.
"""

class Node:
    def __init__(self):
        self.neighbors = set()

        # Keep this safe!
        self._wallet_seed = int.from_bytes(urandom(16), byteorder='big')
        self._private_key = ec.derive_private_key(self._wallet_seed, ec.SECP384R1())


    """
    Register another node on the network to be aware of

        address: string -> address of the node on the network
    """
    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.neighbors.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.neighbors.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    """
    Sign a cryptographic message on given data

        data: string -> the data to be signed
        return: hex -> the signature
    """
    def generate_signature(self, data):
        hash = bytes.fromhex(data)

        signature = self._private_key.sign(
            hash,
            ec.ECDSA(hashes.SHA256())
        )

        return signature.hex()


    """
    Generate this node's transaction address and corresponding public key

        return: Tuple -> (address: hex, pubkey: hex)
    """
    def generate_transaction_addr(self):
        public_key = self._private_key.public_key()
        serialized_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Transaction addresses are made of hashing the public key once
        address = hashes.Hash(hashes.SHA256())
        address.update(serialized_public_key)

        # Return tuple of tx address and public key to verify
        return (address.finalize().hex(), serialized_public_key.hex())

    """
    Verify that a given address actually belongs to the user

        addr: hex -> the given address
        pubkey: hex -> the pubkey corresponding to the addr
        return: bool -> whether or not the key was verified
    """
    def verify_addr(self, addr, pubkey):
        # Regenerate the given addresses
        address = hashes.Hash(hashes.SHA256())
        sender_public_bytes = bytes.fromhex(pubkey)
        address.update(sender_public_bytes)

        # The two public keys both generate the corresponding addresses
        if (address.finalize().hex() == addr):
            return True
        else:
            return False

    """
    Verify that a block is valid and eligble to be put into the chain

        block: dict -> the block to be judged
        return: bool -> if the block was verified
    """
    def verify_block(self, block):
        txsig = bytes.fromhex(block['txsig'])
        pubkey = serialization.load_der_public_key(bytes.fromhex(block['pubkey']))

        try:
            pubkey.verify(txsig, b'I have authorized this transaction.', ec.ECDSA(hashes.SHA256()))
            return True
        except:
            return False