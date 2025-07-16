// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "forge-std/Script.sol";


enum TriggerType {
    FUNCTION,
    EVENT
}

enum RawTriggerType {
    CALL,
    BLOCK,
    LOG
}

struct Trigger {
    string abiName;
    bytes32 selector;
    TriggerType triggerType;
    bytes32 listenerCodehash;
    bytes32 handlerSelector;
}

struct RawTrigger {
    RawTriggerType triggerType;
    bytes32 handlerSelector;
    bytes32 listenerCodehash;
}

struct ContractTarget {
    ChainIdContract targetContract;
    Trigger trigger;
    bytes32 handlerSelector;
    bytes32 listenerCodehash;
}

struct ChainIdContract {
    uint256 chainId;
    address contractAddress;
}

struct Abi {
    string name;
}

struct AbiTarget {
    ChainIdAbi targetAbi;
    Trigger trigger;
    bytes32 handlerSelector;
    bytes32 listenerCodehash;
}

struct ChainIdAbi {
    uint256 chainId;
    Abi abi;
}

struct ChainIdGlobal {
    uint256 chainId;
}

struct CustomTriggerContractTarget {
    ChainIdContract targetContract;
    bytes32 handlerSelector;
    bytes32 listenerCodehash;
}

struct CustomTriggerTypeAbiTarget {
    ChainIdAbi targetAbi;
    bytes32 handlerSelector;
    bytes32 listenerCodehash;
}

struct GlobalTarget {
    ChainIdGlobal chainId;
    RawTriggerType triggerType;
    bytes32 handlerSelector;
    bytes32 listenerCodehash;
}

abstract contract BaseTriggers {
    ContractTarget[] _contractTargets;
    AbiTarget[] _abiTargets;
    GlobalTarget[] _globalTargets;

    function triggers() external virtual;

    function addTrigger(ChainIdContract memory targetContract, Trigger memory triggerFunction) internal {
        _contractTargets.push(ContractTarget({
            targetContract: targetContract,
            trigger: triggerFunction,
            handlerSelector: triggerFunction.handlerSelector,
            listenerCodehash: triggerFunction.listenerCodehash
        }));
    }

    function addTriggers(ChainIdContract memory targetContract, Trigger[] memory triggers_) internal {
        for (uint256 i = 0; i < triggers_.length; i++) {
            addTrigger(targetContract, triggers_[i]);
        }
    }

    function addTrigger(ChainIdAbi memory targetAbi, Trigger memory triggerFunction) internal {
        _abiTargets.push(AbiTarget({
            targetAbi: targetAbi,
            trigger: triggerFunction,
            handlerSelector: triggerFunction.handlerSelector,
            listenerCodehash: triggerFunction.listenerCodehash
        }));
    }

    function addTriggers(ChainIdAbi memory targetAbi, Trigger[] memory triggers_) internal {
        for (uint256 i = 0; i < triggers_.length; i++) {
            addTrigger(targetAbi, triggers_[i]);
        }
    }

    function addTrigger(ChainIdGlobal memory chainId, RawTrigger memory target) internal {
        _globalTargets.push(GlobalTarget({
            chainId: chainId,
            triggerType: target.triggerType,
            handlerSelector: target.handlerSelector,
            listenerCodehash: target.listenerCodehash
        }));
    }

    function addTriggers(ChainIdGlobal memory chainId, RawTrigger[] memory triggers_) internal {
        for (uint256 i = 0; i < triggers_.length; i++) {
            addTrigger(chainId, triggers_[i]);
        }
    }

    function getSimTargets() view external returns (AbiTarget[] memory, ContractTarget[] memory, GlobalTarget[] memory) {
        return (_abiTargets, _contractTargets, _globalTargets);
    }
}
