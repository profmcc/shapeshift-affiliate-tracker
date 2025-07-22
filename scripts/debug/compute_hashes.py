from web3 import Web3

# Compute event signature hashes
increase_liquidity_sig = "IncreaseLiquidity(address,int24,int24,uint128,uint256,uint256)"
decrease_liquidity_sig = "DecreaseLiquidity(address,int24,int24,uint128,uint256,uint256)"
collect_sig = "Collect(address,address,uint256,uint256)"

print("Event Signature Hashes:")
print(f"IncreaseLiquidity: {Web3.keccak(text=increase_liquidity_sig).hex()}")
print(f"DecreaseLiquidity: {Web3.keccak(text=decrease_liquidity_sig).hex()}")
print(f"Collect: {Web3.keccak(text=collect_sig).hex()}")

# Also try with indexed parameters only (first topic)
print("\nEvent Signature Hashes (indexed params only):")
increase_liquidity_indexed_sig = "IncreaseLiquidity(address,int24,int24,uint128,uint256,uint256)"
decrease_liquidity_indexed_sig = "DecreaseLiquidity(address,int24,int24,uint128,uint256,uint256)"
collect_indexed_sig = "Collect(address,address,uint256,uint256)"

print(f"IncreaseLiquidity (indexed): {Web3.keccak(text=increase_liquidity_indexed_sig).hex()}")
print(f"DecreaseLiquidity (indexed): {Web3.keccak(text=decrease_liquidity_indexed_sig).hex()}")
print(f"Collect (indexed): {Web3.keccak(text=collect_indexed_sig).hex()}") 