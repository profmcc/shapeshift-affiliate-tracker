// SPDX-License-Identifier: Unlicense
pragma solidity ^0.8.13;

import {FunctionContext, EventContext, CallFrame, TransactionContext, ContractVerificationSource, CallType} from "sim-idx-sol/Context.sol";

library MockContexts {
    function mockFunctionContext() internal pure returns (FunctionContext memory) {
        return FunctionContext({
            txn: mockBaseContext()
        });
    }

    function mockEventContext() internal pure returns (EventContext memory) { 
        return EventContext({
            txn: mockBaseContext()
        });
    }

    function mockBaseContext() internal pure returns (TransactionContext memory) {
        return TransactionContext({
            call: mockCallFrame(),
            hash: bytes32(0),
            chainId: 1
        });
    }

    function mockCallFrame() internal pure returns (CallFrame memory) {
        return CallFrame({
            caller: address(0x2121212121212121212121212121212121212121),
            callee: address(0x4242424242424242424242424242424242424242),
            value: 0,
            callType: CallType.UNKNOWN,
            callDepth: 0,
            verificationSource: ContractVerificationSource.Unspecified
        });
    }
}
