from web3 import Web3
from colorama import Fore
import pyfiglet
import os

class SandwichTracker:
    """
    A class to track and analyze transactions on the Ethereum blockchain for potential sandwich attack patterns.
    """

    def __init__(self):
        """
        Initializes the SandwichTracker with a Web3 connection and sets up initial data structures.
        """
        self.web3 = self.setup_web3_connection()
        self.known_dex_contracts = ['0xdAC17F958D2ee523a2206206994597C13D831ec7']  # Replace with actual addresses
        self.to_from_pairs = {}
        self.transaction_count = {}
        self.tx_lookup = {}
        self.possible_sandwich = {}

    def setup_web3_connection(self):
        """
        Sets up a Web3 connection to the Ethereum blockchain using an Infura API key.
        Returns a Web3 instance.
        """
        api_key = os.getenv("INFURA_API_KEY")  # Secure API key storage
        if not api_key:
            raise ValueError("INFURA_API_KEY not set in environment variables")
        return Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{api_key}'))

    def grab_transactions(self):
        """
        Fetches the latest block and processes all transactions within it.
        """
        block = self.web3.eth.get_block('latest')
        if block and block.transactions:
            for transaction in block.transactions:
                self.process_transaction(transaction.hex())

    def process_transaction(self, tx_hash):
        """
        Processes a single transaction by its hash.
        Checks if the transaction interacts with known DEX contracts and updates tracking data.
        """
        try:
            tx = self.web3.eth.get_transaction(tx_hash)
            if tx.to is not None and tx.to in self.known_dex_contracts:
                self.update_transaction_data(tx)
        except Exception as e:
            print(f"Error processing transaction {tx_hash}: {e}")

    def update_transaction_data(self, tx):
        """
        Updates the internal data structures with information from a given transaction.
        """
        if tx.to in self.to_from_pairs and self.to_from_pairs[tx.to] == tx['from']:
            self.transaction_count[tx.to] += 1
        else:
            self.transaction_count[tx.to] = 1
            self.to_from_pairs[tx.to] = tx['from']
        self.tx_lookup[tx.hash.hex()] = [tx.to, tx['from'], tx.gasPrice]

    def find_bots(self):
        """
        Identifies potential bots by finding to/from pairs with exactly 2 transactions.
        """
        for transaction_hash, pair in self.tx_lookup.items():
            if self.transaction_count[pair[0]] == 2:
                self.possible_sandwich[transaction_hash] = [pair[0], pair[2]]

    def find_sandwich(self):
        """
        Analyzes the possible sandwich attacks by checking for variance in gas prices.
        Returns a list of transactions that are potential sandwich attacks.
        """
        all_bots = {}
        duplicate_bots = {}
        sandwiches = []

        for s_hash, s_gas in self.possible_sandwich.items():
            if s_gas[1] in all_bots.values():
                duplicate_bots[s_hash] = s_gas[1]
            else:
                all_bots[s_hash] = s_gas[1]

        for s_hash, bot in all_bots.items():
            if bot not in duplicate_bots.values():
                sandwiches.append(s_hash)

        return sandwiches

if __name__ == "__main__":
    # Display header
    result = pyfiglet.figlet_format("Smart Bot Sandwich Tracker", font="chunky")
    print(f'{Fore.GREEN}Searching for Sandwich: \n {Fore.RED}{result}')

    # Initialize and run tracker
    tracker = SandwichTracker()
    tracker.grab_transactions()
    tracker.find_bots()

    # Process potential sandwich attacks and print results
    sandwiches = tracker.find_sandwich()
    if sandwiches:
        for sandwich in sandwiches:
            print(f'{Fore.GREEN}Delicious Sandwich Found: \n {Fore.YELLOW}{sandwich}')
    else:
        print(f'{Fore.GREEN}No sandwiches found in the latest block.')
