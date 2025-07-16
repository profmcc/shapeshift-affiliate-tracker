// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "lib/sim-idx-sol/src/Triggers.sol";
import "lib/sim-idx-sol/src/Context.sol";

function UniswapV3Pool$Abi() pure returns (Abi memory) {
    return Abi("UniswapV3Pool");
}

struct UniswapV3Pool$IncreaseLiquidityEventParams {
    address owner;
    int24 tickLower;
    int24 tickUpper;
    uint128 amount;
    uint256 amount0;
    uint256 amount1;
}

struct UniswapV3Pool$DecreaseLiquidityEventParams {
    address owner;
    int24 tickLower;
    int24 tickUpper;
    uint128 amount;
    uint256 amount0;
    uint256 amount1;
}

struct UniswapV3Pool$CollectEventParams {
    address sender;
    address recipient;
    uint256 amount0;
    uint256 amount1;
}

abstract contract UniswapV3Pool$OnIncreaseLiquidityEvent {
    function onIncreaseLiquidityEvent(EventContext memory ctx, UniswapV3Pool$IncreaseLiquidityEventParams memory inputs) virtual external;

    function triggerOnIncreaseLiquidityEvent() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Pool",
            selector: bytes32(0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f),
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onIncreaseLiquidityEvent.selector
        });
    }
}

abstract contract UniswapV3Pool$OnDecreaseLiquidityEvent {
    function onDecreaseLiquidityEvent(EventContext memory ctx, UniswapV3Pool$DecreaseLiquidityEventParams memory inputs) virtual external;

    function triggerOnDecreaseLiquidityEvent() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Pool",
            selector: bytes32(0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4),
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onDecreaseLiquidityEvent.selector
        });
    }
}

abstract contract UniswapV3Pool$OnCollectEvent {
    function onCollectEvent(EventContext memory ctx, UniswapV3Pool$CollectEventParams memory inputs) virtual external;

    function triggerOnCollectEvent() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Pool",
            selector: bytes32(0x40d0efd1a53d60ecbf40971b9d9e18502887ace780a0564668d6d65605f3c5de),
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onCollectEvent.selector
        });
    }
} 