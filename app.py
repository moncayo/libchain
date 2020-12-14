"""
David Moncayo
Blockchain Library Project

The main driver for the app, a Flask front end
that takes JSON data that calls and acts upon the
blockchain data. Just for the sake of presentations,
this was the easiest way to show how multiple nodes could work.
"""

from flask import Flask, jsonify, request
from library import Library
from blockchain import Chain, Node
import requests

app     = Flask(__name__)
library = Library()
node    = Node()


"""
Route for creating a new book in the library

Sets the recipient address to the node that creates the book,
which will typically be the library and broadcasts the creation
of the chain to the rest of the network
"""
@app.route('/book/new', methods=['POST'])
def new_book():
    values = request.get_json()
    book_id = values['book_id']
    address, public_key = node.generate_transaction_addr()
    book = Chain(id=book_id, data={
        'sender': None,
        'recipient': address
    })

    if library.add_book(book):
        # Broadcasts the book to the rest of the network
        for neighbor in node.neighbors:
            requests.post(f'http://{neighbor}/broadcast/book/{book_id}', json=book.last_block)

        # Returns the newly added block
        return jsonify(book.last_block), 200
    else:
        return {'error': 'This book must already exist.'}, 400

"""
Retrieves the chain of a certain book given the id

values = { 
    book_id: the id of the chain (book)
}
"""
@app.route('/book/chain/', methods=['GET'])
def book_chain():
    values = request.get_json()
    book_id = values['book_id']

    return jsonify(library.fetch_book(book_id).chain), 200


"""
Register a new node that is connected to the network

values = {
    nodes: [] an array of IP addresses
}
"""
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    node_list = values.get('nodes')
    
    if node_list is None:
        return "Error: Please supply a valid list of nodes", 400

    for idx in node_list:
        node.register_node(idx)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(node.neighbors),
    }
    
    return jsonify(response), 201


"""
Create an exchange between a sender and recipient for a book

This node will create an exchange from itself to the recipient
given the proper keys and authorization (such as this node being
in possession of the book in the first place). If the transaction
is successful then the new block will be created and broadcasted
to the rest of the network.
"""
@app.route('/book/exchange', methods=['POST'])
def new_transaction():
    values = request.get_json()
    address, pub_key = node.generate_transaction_addr()
    recipient = values['recipient']

    data = {
        'book_id': values['book_id'],
        'sender': address,
        'recipient': recipient,
        'pubkey': pub_key,
        'txsig': node.generate_signature(b'I have authorized this transaction.'.hex())
    }

    if library.create_exchange(data):
        for neighbor in node.neighbors:
            r = requests.post(f'http://{neighbor}/broadcast/block', json=data)
        return jsonify(data), 200
    
    return 'Something went wrong'


"""
An endpoint for the node to receive a new block

    block: dict -> the block to be added        
"""
@app.route('/broadcast/block', methods=['POST'])
def broadcast_block():
    block = request.get_json()
    library.create_exchange(block)

    return 'Success!', 200


"""
Broadcast a new book to the nodes on the network that do not have i

    book_id: str -> the id of the chain (book)
    req: dict -> the exported genesis block data
"""
@app.route('/broadcast/book/<book_id>', methods=['POST'])
def broadcast_book(book_id):
    req = request.get_json()
    book = Chain(id=book_id, exported=req)
    library.add_book(book)

    return 'Success!', 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    # A useful tool for creating new nodes -- run the same code on multiple ports
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port, debug=True)