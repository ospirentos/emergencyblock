import hashlib
import json
from time import time
from uuid import uuid4
from urllib.parse import urlparse
import sys

import requests
from flask import Flask, jsonify, request

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_events = []
        self.nodes = set()

        self.new_block(previous_hash=1, proof=100)

#----------P2P Node Connection and Consensus----------#

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block= chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")

            if block['previous_hash'] != self.hash(last_block):
                return False
            
            last_block = block
            current_index += 1
    
        return True
    
    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        
        if new_chain:
            self.chain = new_chain
            return True

        return False

#---------------Basic Blockchain Functions---------------#

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'events': self.current_events,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        #DEBUG: print size of a block object
        print("Size of an block object is ", sys.getsizeof(block))

        self.current_events = []

        self.chain.append(block)
        
        return block

    def new_event(self, source, eventType, location):
        self.current_events.append({
            'source': source,
            'eventType': eventType,
            'loaction': location,
            'time': time()
        })
        #DEBUG: pirnt size of an event object
        new_event = {
            'source': source,
            'eventType': eventType,
            'loaction': location,
            'time': time()
        }
        print("Size of an event object is ", sys.getsizeof(new_event))
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:6] == "000000"

#---------------------------API---------------------------#

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    mining_start_time = time()
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    #If there will be any reward, implement it here

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    elapsed_time = time() - mining_start_time

    response = {
        'message': "New Block Forged",
        'mining_time': elapsed_time,
        'index': block['index'],
        'events': block['events'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/events/new', methods=['POST'])
def new_event():
    values = request.get_json()

    required = ['source', 'eventType', 'location']
    if not all(k in values for k in required):
        return 'Missing values', 400
    
    index = blockchain.new_event(values['source'], values['eventType'], values['location'])

    response = {'message': f'Event will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain' : blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Out chain is authoritative',
            'chain': blockchain.chain
        }
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0')