// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "forge-std/Script.sol";
import {
    AbiTarget,
    ContractTarget,
    GlobalTarget,
    TriggerType,
    RawTriggerType
} from "lib/sim-idx-sol/src/Triggers.sol";
import {Triggers} from "src/Main.sol";

// TODO: This script should be hidden from the user
contract HookScript is Script {
    Triggers listener;

    function setUp() public {
        listener = new Triggers();
        listener.triggers();
    }

    function run(string calldata outputFile) public {
        vm.startBroadcast();

        (
            AbiTarget[] memory abiTargets,
            ContractTarget[] memory contractTargets,
            GlobalTarget[] memory globalTargets
        ) = listener.getSimTargets();

        string[] memory serializedAbiTargets = serializeAbiTarget(abiTargets);
        string[] memory serializedContractTargets = serializeContractTarget(contractTargets);
        string[] memory serializedGlobalTargets = serializeGlobalTarget(globalTargets);

        string[] memory combined = concat(serializedAbiTargets, serializedContractTargets);
        combined = concat(combined, serializedGlobalTargets);

        string memory serializedTargets = string.concat("[", commaSeparate(combined), "]");

        vm.writeFile(outputFile, serializedTargets);
        vm.stopBroadcast();
    }

    function serializeContractTarget(ContractTarget[] memory target) internal returns (string[] memory) {
        string[] memory serializedTargets = new string[](target.length);
        for (uint256 i = 0; i < target.length; i++) {
            string memory objectKey = "target";
            vm.serializeUint(objectKey, "chain_id", target[i].targetContract.chainId);
            vm.serializeString(objectKey, "abi_name", target[i].trigger.abiName);
            vm.serializeAddress(objectKey, "target_contract", target[i].targetContract.contractAddress);
            bytes memory functionSelector = abi.encode(target[i].trigger.selector);
            vm.serializeBytes(objectKey, "target_selector", functionSelector);
            vm.serializeString(objectKey, "target_type", "contract");
            vm.serializeString(objectKey, "trigger_type", target[i].trigger.triggerType.toString());
            vm.serializeBytes32(objectKey, "listener_codehash", target[i].trigger.listenerCodehash);
            serializedTargets[i] = vm.serializeBytes32(objectKey, "handler_selector", target[i].handlerSelector);
        }
        return serializedTargets;
    }

    function serializeAbiTarget(AbiTarget[] memory target) internal returns (string[] memory) {
        string[] memory serializedTargets = new string[](target.length);
        for (uint256 i = 0; i < target.length; i++) {
            string memory objectKey = "target";
            vm.serializeUint(objectKey, "chain_id", target[i].targetAbi.chainId);
            vm.serializeString(objectKey, "abi_name", target[i].targetAbi.abi.name);
            bytes memory functionSelector = abi.encode(target[i].trigger.selector);
            vm.serializeBytes(objectKey, "target_selector", functionSelector);
            vm.serializeString(objectKey, "target_type", "abi");
            vm.serializeString(objectKey, "trigger_type", target[i].trigger.triggerType.toString());
            vm.serializeBytes32(objectKey, "listener_codehash", target[i].trigger.listenerCodehash);
            serializedTargets[i] = vm.serializeBytes32(objectKey, "handler_selector", target[i].handlerSelector);
        }
        return serializedTargets;
    }

    function serializeGlobalTarget(GlobalTarget[] memory target) internal returns (string[] memory) {
        string[] memory serializedTargets = new string[](target.length);
        for (uint256 i = 0; i < target.length; i++) {
            string memory objectKey = "generic_target";
            vm.serializeString(objectKey, "trigger_type", target[i].triggerType.toString());
            vm.serializeUint(objectKey, "chain_id", target[i].chainId.chainId);
            vm.serializeString(objectKey, "target_type", "global");
            vm.serializeBytes32(objectKey, "listener_codehash", target[i].listenerCodehash);
            serializedTargets[i] = vm.serializeBytes32(objectKey, "handler_selector", target[i].handlerSelector);
        }
        return serializedTargets;
    }

    function concat(string[] memory a, string[] memory b) internal pure returns (string[] memory) {
        string[] memory combined = new string[](a.length + b.length);
        for (uint256 i = 0; i < a.length; i++) {
            combined[i] = a[i];
        }
        for (uint256 i = 0; i < b.length; i++) {
            combined[a.length + i] = b[i];
        }
        return combined;
    }

    function commaSeparate(string[] memory targets) internal pure returns (string memory) {
        string memory out = "";
        for (uint256 i = 0; i < targets.length; i++) {
            if (i > 0) {
                out = string.concat(out, ",", targets[i]);
            } else {
                out = string.concat(out, targets[i]);
            }
        }
        return out;
    }
}

library CustomTriggerTypeLib {
    function toString(TriggerType triggerType) internal pure returns (string memory) {
        if (triggerType == TriggerType.FUNCTION) {
            return "function";
        } else if (triggerType == TriggerType.EVENT) {
            return "event";
        } else {
            revert("Invalid trigger type");
        }
    }

    function toString(RawTriggerType triggerType) internal pure returns (string memory) {
        if (triggerType == RawTriggerType.CALL) {
            return "call";
        } else if (triggerType == RawTriggerType.BLOCK) {
            return "block";
        } else if (triggerType == RawTriggerType.LOG) {
            return "log";
        } else {
            revert("Invalid trigger type");
        }
    }
}

using CustomTriggerTypeLib for TriggerType;
using CustomTriggerTypeLib for RawTriggerType;
