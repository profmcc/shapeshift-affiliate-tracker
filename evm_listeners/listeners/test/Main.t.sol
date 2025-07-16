// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Test, console} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {Listener} from "../src/Main.sol";
import "sim-idx-sol/Simidx.sol";
import "sim-idx-generated/Generated.sol";
import {MockContexts} from "sim-idx-sol/test/MockContexts.sol";

contract ListenerTest is Test {
    Listener public listener;

    function setUp() public {
        listener = new Listener();
        vm.recordLogs();
    }

    function test_onCreatePool() public {
        FunctionContext memory ctx = MockContexts.mockFunctionContext();

        listener.onCreatePoolFunction(
            ctx,
            UniswapV3Factory$createPoolFunctionInputs({tokenA: 0x8ce8725A65DaE7d3D5543372D5415f4F8ad448f9, tokenB: 0x8ce8725A65DaE7d3D5543372D5415f4F8ad448f9, fee: 1}),
            UniswapV3Factory$createPoolFunctionOutputs({pool: 0x8ce8725A65DaE7d3D5543372D5415f4F8ad448f9})
        );

        Vm.Log[] memory entries = vm.getRecordedLogs();
        assertEq(entries.length, 1);
        assertEq(entries[0].topics.length, 1);
        assertEq(entries[0].topics[0], keccak256("PoolCreated(uint64,address,address,address,address,uint24)"));
        (uint64 chainId, address _callee, address pool, address token0, address token1, uint24 fee) = abi.decode(entries[0].data, (uint64, address, address, address, address, uint24));
        assertEq(chainId, 31337);
        assertEq(_callee, ctx.txn.call.callee);
        assertEq(pool, 0x8ce8725A65DaE7d3D5543372D5415f4F8ad448f9);
        assertEq(token0, 0x8ce8725A65DaE7d3D5543372D5415f4F8ad448f9);
        assertEq(token1, 0x8ce8725A65DaE7d3D5543372D5415f4F8ad448f9);
        assertEq(fee, 1);
    }

    function testFuzz_onCreatePool(address callee, address tokenA, address tokenB, uint24 fee) public {
        FunctionContext memory ctx = MockContexts.mockFunctionContext();
        ctx.txn.call.callee = callee;

        listener.onCreatePoolFunction(
            ctx,
            UniswapV3Factory$createPoolFunctionInputs({tokenA: tokenA, tokenB: tokenB, fee: fee}),
            UniswapV3Factory$createPoolFunctionOutputs({pool: 0x8ce8725A65DaE7d3D5543372D5415f4F8ad448f9})
        );

        Vm.Log[] memory entries = vm.getRecordedLogs();
        assertEq(entries.length, 1);
        assertEq(entries[0].topics.length, 1);
        assertEq(entries[0].topics[0], keccak256("PoolCreated(uint64,address,address,address,address,uint24)"));
        (uint64 chainId, address _callee, address pool, address _token0, address _token1, uint24 _fee) = abi.decode(entries[0].data, (uint64, address, address, address, address, uint24));
        assertEq(chainId, 31337);
        assertEq(_callee, callee);
        assertEq(pool, 0x8ce8725A65DaE7d3D5543372D5415f4F8ad448f9);
        assertEq(_token0, tokenA);
        assertEq(_token1, tokenB);
        assertEq(_fee, fee);
    }
}
