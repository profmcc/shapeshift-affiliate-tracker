// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "sim-idx-sol/Simidx.sol";
import "sim-idx-generated/Generated.sol";

contract Triggers is BaseTriggers {
    function triggers() external virtual override {
        Listener listener = new Listener();
        CowSwapListener cowSwapListener = new CowSwapListener();
        ZeroXTransformERC20Listener zeroXListener = new ZeroXTransformERC20Listener();
        PortalsListener portalsListener = new PortalsListener();
        DummyListener dummyListener = new DummyListener();
        LPPoolListener lpPoolListener = new LPPoolListener();
        UniswapV2SwapListener v2SwapListener = new UniswapV2SwapListener();
        UniswapV3SwapListener v3SwapListener = new UniswapV3SwapListener();
        
        // Uniswap V3 Factory listeners (pool creation)
        addTrigger(ChainIdContract(1, 0x1F98431c8aD98523631AE4a59f267346ea31F984), listener.triggerOnCreatePoolFunction());
        addTrigger(ChainIdContract(137, 0x0227628f3F023bb0B980b67D528571c95c6DaC1c), listener.triggerOnCreatePoolFunction());
        addTrigger(ChainIdContract(10, 0x1F98431c8aD98523631AE4a59f267346ea31F984), listener.triggerOnCreatePoolFunction());
        addTrigger(ChainIdContract(42161, 0x1F98431c8aD98523631AE4a59f267346ea31F984), listener.triggerOnCreatePoolFunction());
        addTrigger(ChainIdContract(8453, 0x33128a8fC17869897dcE68Ed026d694621f6FDfD), listener.triggerOnCreatePoolFunction());
        addTrigger(ChainIdContract(43114, 0x0227628f3F023bb0B980b67D528571c95c6DaC1c), listener.triggerOnCreatePoolFunction());
        addTrigger(ChainIdContract(56, 0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865), listener.triggerOnCreatePoolFunction());
        
        // CowSwap GPv2Settlement contracts
        addTrigger(ChainIdContract(1, 0x9008D19f58AAbD9eD0D60971565AA8510560ab41), cowSwapListener.triggerOnTradeEvent());
        addTrigger(ChainIdContract(137, 0x9008D19f58AAbD9eD0D60971565AA8510560ab41), cowSwapListener.triggerOnTradeEvent());
        addTrigger(ChainIdContract(10, 0x9008D19f58AAbD9eD0D60971565AA8510560ab41), cowSwapListener.triggerOnTradeEvent());
        addTrigger(ChainIdContract(42161, 0x9008D19f58AAbD9eD0D60971565AA8510560ab41), cowSwapListener.triggerOnTradeEvent());
        addTrigger(ChainIdContract(8453, 0x9008D19f58AAbD9eD0D60971565AA8510560ab41), cowSwapListener.triggerOnTradeEvent());
        
        // 0x Exchange Proxy contracts
        addTrigger(ChainIdContract(1, 0xDef1C0ded9bec7F1a1670819833240f027b25EfF), zeroXListener.triggerOnTransformErc20Function());
        addTrigger(ChainIdContract(137, 0xDef1C0ded9bec7F1a1670819833240f027b25EfF), zeroXListener.triggerOnTransformErc20Function());
        addTrigger(ChainIdContract(10, 0xDef1C0ded9bec7F1a1670819833240f027b25EfF), zeroXListener.triggerOnTransformErc20Function());
        addTrigger(ChainIdContract(42161, 0xDef1C0ded9bec7F1a1670819833240f027b25EfF), zeroXListener.triggerOnTransformErc20Function());
        addTrigger(ChainIdContract(8453, 0xDef1C0ded9bec7F1a1670819833240f027b25EfF), zeroXListener.triggerOnTransformErc20Function());
        addTrigger(ChainIdContract(43114, 0xDef1C0ded9bec7F1a1670819833240f027b25EfF), zeroXListener.triggerOnTransformErc20Function());
        addTrigger(ChainIdContract(56, 0xDef1C0ded9bec7F1a1670819833240f027b25EfF), zeroXListener.triggerOnTransformErc20Function());
        
        // Portals Router
        addTrigger(ChainIdContract(1, 0xbf5A7F3629fB325E2a8453D595AB103465F75E62), portalsListener.triggerOnPortalEvent());
        
        // LP Pool with sim idx 0x470e8de2eBaef52014A47Cb5E6aF86884947F08c
        addTrigger(ChainIdContract(1, 0x470e8de2eBaef52014A47Cb5E6aF86884947F08c), lpPoolListener.triggerOnIncreaseLiquidityEvent());
        addTrigger(ChainIdContract(1, 0x470e8de2eBaef52014A47Cb5E6aF86884947F08c), lpPoolListener.triggerOnDecreaseLiquidityEvent());
        addTrigger(ChainIdContract(1, 0x470e8de2eBaef52014A47Cb5E6aF86884947F08c), lpPoolListener.triggerOnCollectEvent());
        
        // Major Uniswap V2 pairs for swap tracking
        // Ethereum mainnet major pairs
        addTrigger(ChainIdContract(1, 0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc), v2SwapListener.triggerOnSwapEvent()); // WETH/USDC
        addTrigger(ChainIdContract(1, 0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8), v2SwapListener.triggerOnSwapEvent()); // WETH/USDT
        addTrigger(ChainIdContract(1, 0x470e8de2eBaef52014A47Cb5E6aF86884947F08c), v2SwapListener.triggerOnSwapEvent()); // WETH/FOX
        addTrigger(ChainIdContract(1, 0x2fDbAdf3C4D5A8666Bc06645B8358ab803996E28), v2SwapListener.triggerOnSwapEvent()); // WETH/UNI
        
        // Major Uniswap V3 pools for swap tracking
        addTrigger(ChainIdContract(1, 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640), v3SwapListener.triggerOnSwapEvent()); // WETH/USDC V3
        addTrigger(ChainIdContract(1, 0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36), v3SwapListener.triggerOnSwapEvent()); // WETH/USDT V3
        addTrigger(ChainIdContract(1, 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8), v3SwapListener.triggerOnSwapEvent()); // WETH/USDC V3 0.3%
        
        // Polygon major pairs
        addTrigger(ChainIdContract(137, 0x6e7a5FAFcec6BB1e78bAE2A1F0B612012BF14827), v2SwapListener.triggerOnSwapEvent()); // WMATIC/USDC
        addTrigger(ChainIdContract(137, 0x34965ba0ac2451A34a0471F04CCa3F990b8dea27), v2SwapListener.triggerOnSwapEvent()); // WMATIC/USDT
        
        // Arbitrum major pairs
        addTrigger(ChainIdContract(42161, 0x5f6ce0ca13b87bd738519545d3e018e70e339c24), v2SwapListener.triggerOnSwapEvent()); // WETH/FOX
        addTrigger(ChainIdContract(42161, 0x905dfCD5649dE5Bc4c4C8C8C8C8C8C8C8C8C8C8), v2SwapListener.triggerOnSwapEvent()); // WETH/USDC
        
        // Base major pairs
        addTrigger(ChainIdContract(8453, 0x4C36388bE6F416A29C8d8ED537538b8e4e5e8B52), v2SwapListener.triggerOnSwapEvent()); // WETH/USDC
        
        // Avalanche major pairs
        addTrigger(ChainIdContract(43114, 0x2b4C76d0dc16BE1C31D4C1DC53bF9B45987Fc75c), v2SwapListener.triggerOnSwapEvent()); // WAVAX/USDC
        
        // BSC major pairs
        addTrigger(ChainIdContract(56, 0x58F876857a02D6762E0101bb5C46A8c1ED44Dc16), v2SwapListener.triggerOnSwapEvent()); // WBNB/BUSD
    }
}

/// Index calls to the UniswapV3Factory.createPool function on Ethereum
/// To hook on more function calls, specify that this listener should implement that interface and follow the compiler errors.
contract Listener is UniswapV3Factory$OnCreatePoolFunction {
    /// Emitted events are indexed.
    /// To change the data which is indexed, modify the event or add more events.
    event PoolCreated(uint64 chainId, address caller, address pool, address token0, address token1, uint24 fee);

    /// The handler called whenever the UniswapV3Factory.createPool function is called.
    /// Within here you write your indexing specific logic (e.g., call out to other contracts to get more information).
    /// The only requirement for handlers is that they have the correct signature, but usually you will use generated interfaces to help write them.
    function onCreatePoolFunction(
        FunctionContext memory ctx,
        UniswapV3Factory$createPoolFunctionInputs memory inputs,
        UniswapV3Factory$createPoolFunctionOutputs memory outputs
    )
        external
        override
    {
        emit PoolCreated(uint64(block.chainid), ctx.txn.call.callee, outputs.pool, inputs.tokenA, inputs.tokenB, inputs.fee);
    }
}

// Utility to get ShapeShift affiliate address by chain ID
library ShapeShiftAffiliate {
    function get(uint256 chainId) internal pure returns (address) {
        if (chainId == 1) return 0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be; // Ethereum
        if (chainId == 137) return 0xB5F944600785724e31Edb90F9DFa16dBF01Af000; // Polygon
        if (chainId == 10) return 0x6268d07327f4fb7380732dc6d63d95F88c0E083b; // Optimism
        if (chainId == 42161) return 0x38276553F8fbf2A027D901F8be45f00373d8Dd48; // Arbitrum
        if (chainId == 8453) return 0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502; // Base
        if (chainId == 43114) return 0x74d63F31C2335b5b3BA7ad2812357672b2624cEd; // Avalanche
        if (chainId == 56) return 0x8b92b1698b57bEDF2142297e9397875ADBb2297E; // BSC
        return address(0);
    }
}

// Structs and interfaces for 0x TransformERC20
struct TransformErc20FunctionInputs {
    address inputToken;
    address outputToken;
    uint256 inputTokenAmount;
    uint256 minOutputTokenAmount;
    bytes[] transformations;
}

struct TransformErc20FunctionOutputs {
    uint256 outputTokenAmount;
}

interface TransformErc20OnTransformErc20Function {
    function onTransformErc20Function(
        bytes memory ctx,
        TransformErc20FunctionInputs memory inputs,
        TransformErc20FunctionOutputs memory outputs
    ) external;
}

// Structs and interfaces for CowSwap GPv2Settlement
struct GPv2SettlementTradeEventInputs {
    address owner;
    address sellToken;
    address buyToken;
    uint256 sellAmount;
    uint256 buyAmount;
    uint256 feeAmount;
    bytes orderUid;
    bytes32 appData;
}

interface GPv2SettlementOnTradeEvent {
    function onTradeEvent(
        bytes memory ctx,
        GPv2SettlementTradeEventInputs memory inputs
    ) external;
}

// 0x TransformERC20 listener for affiliate fees
contract ZeroXTransformERC20Listener is TransformErc20OnTransformErc20Function {
    event ZeroXAffiliateFeePaid(
        uint64 chainId,
        address sender,
        address recipient,
        address token,
        uint256 amount
    );
    function onTransformErc20Function(
        bytes memory ctx,
        TransformErc20FunctionInputs memory inputs,
        TransformErc20FunctionOutputs memory outputs
    ) external override {
        address affiliate = ShapeShiftAffiliate.get(block.chainid);
        for (uint i = 0; i < inputs.transformations.length; i++) {
            (address token, uint256 amount, address recipient) = abi.decode(inputs.transformations[i], (address, uint256, address));
            if (recipient == affiliate) {
                emit ZeroXAffiliateFeePaid(
                    uint64(block.chainid),
                    tx.origin,
                    recipient,
                    token,
                    amount
                );
            }
        }
    }
    function triggerOnTransformErc20Function() view public returns (Trigger memory) {
        return Trigger({
            abiName: "ZeroExExchangeProxy",
            selector: bytes4(0x68c6fa61), // transformERC20(address,address,uint256,uint256,(uint32,bytes)[])
            triggerType: TriggerType.FUNCTION,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onTransformErc20Function.selector
        });
    }
}

// CowSwap listener for Trade events
contract CowSwapListener is GPv2SettlementOnTradeEvent {
    event CowSwapAffiliateTrade(
        uint64 chainId,
        address owner,
        address sellToken,
        address buyToken,
        uint256 sellAmount,
        uint256 buyAmount,
        uint256 feeAmount,
        bytes orderUid,
        bytes32 appData
    );
    function onTradeEvent(
        bytes memory ctx,
        GPv2SettlementTradeEventInputs memory inputs
    ) external override {
        address affiliate = ShapeShiftAffiliate.get(block.chainid);
        if (inputs.owner == affiliate) {
            emit CowSwapAffiliateTrade(
                uint64(block.chainid),
                inputs.owner,
                inputs.sellToken,
                inputs.buyToken,
                inputs.sellAmount,
                inputs.buyAmount,
                inputs.feeAmount,
                inputs.orderUid,
                inputs.appData
            );
        }
    }
    function triggerOnTradeEvent() view public returns (Trigger memory) {
        return Trigger({
            abiName: "GPv2Settlement",
            selector: 0xd78ad95fa46c994b6551d0da85fc275fe613ce3b7d2a7c2c2cfd7c6c3b7aadb3,
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onTradeEvent.selector
        });
    }
}

contract PortalsListener {
    event PortalsAffiliateFee(
        uint64 chainId,
        address inputToken,
        uint256 inputAmount,
        address outputToken,
        uint256 outputAmount,
        address sender,
        address broadcaster,
        address recipient,
        address partner
    );

    function onPortalEvent(
        bytes memory ctx,
        address inputToken,
        uint256 inputAmount,
        address outputToken,
        uint256 outputAmount,
        address sender,
        address broadcaster,
        address recipient,
        address partner
    ) external {
        if (partner == 0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be) {
            emit PortalsAffiliateFee(
                uint64(block.chainid),
                inputToken,
                inputAmount,
                outputToken,
                outputAmount,
                sender,
                broadcaster,
                recipient,
                partner
            );
        }
    }

    function triggerOnPortalEvent() view public returns (Trigger memory) {
        return Trigger({
            abiName: "PortalsRouter",
            selector: 0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03,
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onPortalEvent.selector
        });
    }
}

contract DummyListener {
    event DummyValueSet(uint64 chainId, uint256 value);

    function onValueSetEvent(
        bytes memory ctx,
        uint256 value
    ) external {
        emit DummyValueSet(uint64(block.chainid), value);
    }

    function triggerOnValueSetEvent() view public returns (Trigger memory) {
        return Trigger({
            abiName: "DummyContract",
            selector: 0x6c1c1e6b2e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e,
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onValueSetEvent.selector
        });
    }
}

// LP Pool listener for tracking liquidity add/remove/collect events
contract LPPoolListener is UniswapV3Pool$OnIncreaseLiquidityEvent, UniswapV3Pool$OnDecreaseLiquidityEvent, UniswapV3Pool$OnCollectEvent {
    event LiquidityAdded(
        uint64 chainId,
        address pool,
        address owner,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount,
        uint256 amount0,
        uint256 amount1
    );

    event LiquidityRemoved(
        uint64 chainId,
        address pool,
        address owner,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount,
        uint256 amount0,
        uint256 amount1
    );

    event FeesCollected(
        uint64 chainId,
        address pool,
        address sender,
        address recipient,
        uint256 amount0,
        uint256 amount1
    );

    function onIncreaseLiquidityEvent(
        EventContext memory ctx,
        UniswapV3Pool$IncreaseLiquidityEventParams memory inputs
    ) external override {
        emit LiquidityAdded(
            uint64(block.chainid),
            ctx.txn.call.callee,
            inputs.owner,
            inputs.tickLower,
            inputs.tickUpper,
            inputs.amount,
            inputs.amount0,
            inputs.amount1
        );
    }

    function onDecreaseLiquidityEvent(
        EventContext memory ctx,
        UniswapV3Pool$DecreaseLiquidityEventParams memory inputs
    ) external override {
        emit LiquidityRemoved(
            uint64(block.chainid),
            ctx.txn.call.callee,
            inputs.owner,
            inputs.tickLower,
            inputs.tickUpper,
            inputs.amount,
            inputs.amount0,
            inputs.amount1
        );
    }

    function onCollectEvent(
        EventContext memory ctx,
        UniswapV3Pool$CollectEventParams memory inputs
    ) external override {
        emit FeesCollected(
            uint64(block.chainid),
            ctx.txn.call.callee,
            inputs.sender,
            inputs.recipient,
            inputs.amount0,
            inputs.amount1
        );
    }
}

// Uniswap V2 Swap listener for tracking all swap events
contract UniswapV2SwapListener {
    event UniswapV2Swap(
        uint64 chainId,
        address pair,
        address sender,
        address to,
        uint256 amount0In,
        uint256 amount1In,
        uint256 amount0Out,
        uint256 amount1Out,
        bytes32 txHash
    );

    function onSwapEvent(
        bytes memory ctx,
        address sender,
        uint256 amount0In,
        uint256 amount1In,
        uint256 amount0Out,
        uint256 amount1Out,
        address to
    ) external {
        emit UniswapV2Swap(
            uint64(block.chainid),
            msg.sender, // pair address
            sender,
            to,
            amount0In,
            amount1In,
            amount0Out,
            amount1Out,
            blockhash(block.number - 1) // approximate tx hash
        );
    }

    function triggerOnSwapEvent() view public returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV2Pair",
            selector: 0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822, // Swap event signature
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onSwapEvent.selector
        });
    }
}

// Uniswap V3 Swap listener for tracking all swap events
contract UniswapV3SwapListener {
    event UniswapV3Swap(
        uint64 chainId,
        address pool,
        address sender,
        address recipient,
        int256 amount0,
        int256 amount1,
        uint160 sqrtPriceX96,
        uint128 liquidity,
        int24 tick,
        bytes32 txHash
    );

    function onSwapEvent(
        bytes memory ctx,
        address sender,
        address recipient,
        int256 amount0,
        int256 amount1,
        uint160 sqrtPriceX96,
        uint128 liquidity,
        int24 tick
    ) external {
        emit UniswapV3Swap(
            uint64(block.chainid),
            msg.sender, // pool address
            sender,
            recipient,
            amount0,
            amount1,
            sqrtPriceX96,
            liquidity,
            tick,
            blockhash(block.number - 1) // approximate tx hash
        );
    }

    function triggerOnSwapEvent() view public returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Pool",
            selector: 0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67, // Swap event signature
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onSwapEvent.selector
        });
    }
}

