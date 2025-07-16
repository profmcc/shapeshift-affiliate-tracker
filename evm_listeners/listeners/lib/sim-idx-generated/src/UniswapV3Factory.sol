// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "lib/sim-idx-sol/src/Triggers.sol";
import "lib/sim-idx-sol/src/Context.sol";

function UniswapV3Factory$Abi() pure returns (Abi memory) {
    return Abi("UniswapV3Factory");
}
struct UniswapV3Factory$createPoolFunctionInputs {
    address tokenA;
    address tokenB;
    uint24 fee;
}

struct UniswapV3Factory$createPoolFunctionOutputs {
    address pool;
}

struct UniswapV3Factory$enableFeeAmountFunctionInputs {
    uint24 fee;
    int24 tickSpacing;
}

struct UniswapV3Factory$feeAmountTickSpacingFunctionInputs {
    uint24 outArg0;
}

struct UniswapV3Factory$feeAmountTickSpacingFunctionOutputs {
    int24 outArg0;
}

struct UniswapV3Factory$getPoolFunctionInputs {
    address outArg0;
    address outArg1;
    uint24 outArg2;
}

struct UniswapV3Factory$getPoolFunctionOutputs {
    address outArg0;
}

struct UniswapV3Factory$ownerFunctionOutputs {
    address outArg0;
}

struct UniswapV3Factory$parametersFunctionOutputs {
    address factory;
    address token0;
    address token1;
    uint24 fee;
    int24 tickSpacing;
}

struct UniswapV3Factory$setOwnerFunctionInputs {
    address _owner;
}

struct UniswapV3Factory$FeeAmountEnabledEventParams {
    uint24 fee;
    int24 tickSpacing;
}

struct UniswapV3Factory$OwnerChangedEventParams {
    address oldOwner;
    address newOwner;
}

struct UniswapV3Factory$PoolCreatedEventParams {
    address token0;
    address token1;
    uint24 fee;
    int24 tickSpacing;
    address pool;
}

abstract contract UniswapV3Factory$OnFeeAmountEnabledEvent {
    function onFeeAmountEnabledEvent(EventContext memory ctx, UniswapV3Factory$FeeAmountEnabledEventParams memory inputs) virtual external;

    function triggerOnFeeAmountEnabledEvent() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes32(0xc66a3fdf07232cdd185febcc6579d408c241b47ae2f9907d84be655141eeaecc),
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onFeeAmountEnabledEvent.selector
        });
    }
}

abstract contract UniswapV3Factory$OnOwnerChangedEvent {
    function onOwnerChangedEvent(EventContext memory ctx, UniswapV3Factory$OwnerChangedEventParams memory inputs) virtual external;

    function triggerOnOwnerChangedEvent() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes32(0xb532073b38c83145e3e5135377a08bf9aab55bc0fd7c1179cd4fb995d2a5159c),
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onOwnerChangedEvent.selector
        });
    }
}

abstract contract UniswapV3Factory$OnPoolCreatedEvent {
    function onPoolCreatedEvent(EventContext memory ctx, UniswapV3Factory$PoolCreatedEventParams memory inputs) virtual external;

    function triggerOnPoolCreatedEvent() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes32(0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118),
            triggerType: TriggerType.EVENT,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onPoolCreatedEvent.selector
        });
    }
}

abstract contract UniswapV3Factory$OnCreatePoolFunction {
    function onCreatePoolFunction(FunctionContext memory ctx, UniswapV3Factory$createPoolFunctionInputs memory inputs, UniswapV3Factory$createPoolFunctionOutputs memory outputs) virtual external;

    function triggerOnCreatePoolFunction() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes4(0xa1671295),
            triggerType: TriggerType.FUNCTION,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onCreatePoolFunction.selector
        });
    }
}

abstract contract UniswapV3Factory$OnEnableFeeAmountFunction {
    function onEnableFeeAmountFunction(FunctionContext memory ctx, UniswapV3Factory$enableFeeAmountFunctionInputs memory inputs) virtual external;

    function triggerOnEnableFeeAmountFunction() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes4(0x8a7c195f),
            triggerType: TriggerType.FUNCTION,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onEnableFeeAmountFunction.selector
        });
    }
}

abstract contract UniswapV3Factory$OnFeeAmountTickSpacingFunction {
    function onFeeAmountTickSpacingFunction(FunctionContext memory ctx, UniswapV3Factory$feeAmountTickSpacingFunctionInputs memory inputs, UniswapV3Factory$feeAmountTickSpacingFunctionOutputs memory outputs) virtual external;

    function triggerOnFeeAmountTickSpacingFunction() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes4(0x22afcccb),
            triggerType: TriggerType.FUNCTION,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onFeeAmountTickSpacingFunction.selector
        });
    }
}

abstract contract UniswapV3Factory$OnGetPoolFunction {
    function onGetPoolFunction(FunctionContext memory ctx, UniswapV3Factory$getPoolFunctionInputs memory inputs, UniswapV3Factory$getPoolFunctionOutputs memory outputs) virtual external;

    function triggerOnGetPoolFunction() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes4(0x1698ee82),
            triggerType: TriggerType.FUNCTION,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onGetPoolFunction.selector
        });
    }
}

abstract contract UniswapV3Factory$OnOwnerFunction {
    function onOwnerFunction(FunctionContext memory ctx, UniswapV3Factory$ownerFunctionOutputs memory outputs) virtual external;

    function triggerOnOwnerFunction() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes4(0x8da5cb5b),
            triggerType: TriggerType.FUNCTION,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onOwnerFunction.selector
        });
    }
}

abstract contract UniswapV3Factory$OnParametersFunction {
    function onParametersFunction(FunctionContext memory ctx, UniswapV3Factory$parametersFunctionOutputs memory outputs) virtual external;

    function triggerOnParametersFunction() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes4(0x89035730),
            triggerType: TriggerType.FUNCTION,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onParametersFunction.selector
        });
    }
}

abstract contract UniswapV3Factory$OnSetOwnerFunction {
    function onSetOwnerFunction(FunctionContext memory ctx, UniswapV3Factory$setOwnerFunctionInputs memory inputs) virtual external;

    function triggerOnSetOwnerFunction() view external returns (Trigger memory) {
        return Trigger({
            abiName: "UniswapV3Factory",
            selector: bytes4(0x13af4035),
            triggerType: TriggerType.FUNCTION,
            listenerCodehash: address(this).codehash,
            handlerSelector: this.onSetOwnerFunction.selector
        });
    }
}

contract UniswapV3Factory$EmitAllEvents is
  UniswapV3Factory$OnFeeAmountEnabledEvent,
UniswapV3Factory$OnOwnerChangedEvent,
UniswapV3Factory$OnPoolCreatedEvent
{
  event FeeAmountEnabled(uint24 fee, int24 tickSpacing);
event OwnerChanged(address oldOwner, address newOwner);
event PoolCreated(address token0, address token1, uint24 fee, int24 tickSpacing, address pool);

  function onFeeAmountEnabledEvent(EventContext memory ctx, UniswapV3Factory$FeeAmountEnabledEventParams memory inputs) virtual external override {
    emit FeeAmountEnabled(inputs.fee, inputs.tickSpacing);
  }
function onOwnerChangedEvent(EventContext memory ctx, UniswapV3Factory$OwnerChangedEventParams memory inputs) virtual external override {
    emit OwnerChanged(inputs.oldOwner, inputs.newOwner);
  }
function onPoolCreatedEvent(EventContext memory ctx, UniswapV3Factory$PoolCreatedEventParams memory inputs) virtual external override {
    emit PoolCreated(inputs.token0, inputs.token1, inputs.fee, inputs.tickSpacing, inputs.pool);
  }

  function allTriggers() view external returns (Trigger[] memory) {
    Trigger[] memory triggers = new Trigger[](3);
    triggers[0] = this.triggerOnFeeAmountEnabledEvent();
    triggers[1] = this.triggerOnOwnerChangedEvent();
    triggers[2] = this.triggerOnPoolCreatedEvent();
    return triggers;
  }
}