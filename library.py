"""
David Moncayo
Blockchain Libary Project

Library is a container class for storing blockchains
It takes in objects of class Chain and can create 
blocks when an exchange takes place
"""

from blockchain import Chain
import hashlib

class Library:
    def __init__(self):
        self._library = []

    """
    Adds a new book to the library

        new_book: Chain -> Chain object (representing a book)
        return: bool -> True for success, False otherwise 
    """
    def add_book(self, new_book):
        for book in self._library:
            if book.id == new_book.id:
                return False

        self._library.append(new_book)
        return True

    """
    Prints all the book id's in the library
    """    
    def print_books(self):
        for book in self._library:
            print(book.id)
            
    """
    Create an exchange between two people in the blockchain of a specific book

        data = {
            sender: The person conducting the transaction,
            recipient: The recipient of the transaction,
            pubkey: The public key of the sender,
            txsig: The signature of the sender
        }

        return: bool -> True on success, False otherwise
    """
    def create_exchange(self, data):
        if data['sender'] == data['recipient']:
            return False

        for book in self._library:
            if book.id == data['book_id'] and book.last_block.get('recipient') == data['sender']:
                data = {
                    'sender': data['sender'],
                    'recipient': data['recipient'],
                    'pubkey': data['pubkey'],
                    'txsig': data['txsig']
                }

                previous_hash = book.hash(book.last_block)
                book.new_block(previous_hash, data)
                return True
        
        return False

    """
    Looks for a specific Chain from the library

        return: Chain -> Where the id matches req
    """        
    def fetch_book(self, req):
        for book in self._library:
            if book.id == req:
                return book