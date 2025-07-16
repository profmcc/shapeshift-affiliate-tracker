// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {RawTriggerType, RawTrigger} from "./Triggers.sol";
import {RawCallContext, RawBlockContext, RawLogContext} from "./Context.sol";

abstract contract Raw$OnCall {
    function onCall(RawCallContext memory ctx) virtual external;

    function triggerOnCall() external view returns (RawTrigger memory) {
        return RawTrigger({
            triggerType: RawTriggerType.CALL,
            handlerSelector: this.onCall.selector,
            listenerCodehash: address(this).codehash
        });
    }
}

abstract contract Raw$OnBlock {
    function onBlock(RawBlockContext memory ctx) external virtual;

    function triggerOnBlock() external view returns (RawTrigger memory) {
        return RawTrigger({
            triggerType: RawTriggerType.BLOCK,
            handlerSelector: this.onBlock.selector,
            listenerCodehash: address(this).codehash
        });
    }
}

abstract contract Raw$OnLog {
    function onLog(RawLogContext memory ctx) external virtual;

    function triggerOnLog() external view returns (RawTrigger memory) {
        return RawTrigger({
            triggerType: RawTriggerType.LOG,
            handlerSelector: this.onLog.selector,
            listenerCodehash: address(this).codehash
        });
    }
}
