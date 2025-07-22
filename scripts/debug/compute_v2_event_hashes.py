from web3 import Web3
 
print("Mint:", Web3.keccak(text="Mint(address,uint256,uint256)").hex())
print("Burn:", Web3.keccak(text="Burn(address,uint256,uint256,address)").hex())
print("Swap:", Web3.keccak(text="Swap(address,uint256,uint256,uint256,uint256,address)").hex()) 