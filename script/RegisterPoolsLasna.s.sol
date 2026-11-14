// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { HalfwayReactive } from "../src/reactive/HalfwayReactive.sol";

contract RegisterPoolsLasna is Script {
    uint256 public constant ALLOWED_CHAIN_ID = 5318007; // Reactive Lasna

    function run() external {
        require(block.chainid == ALLOWED_CHAIN_ID, "INVALID_CHAIN: Must be Reactive Lasna (5318007)");

        address reactiveAddr = vm.envAddress("REACTIVE_CONTRACT_ADDRESS");
        address basePool = vm.envAddress("BASE_POOL_ADDRESS");
        address baseExecutor = vm.envAddress("BASE_EXECUTOR_ADDRESS");
        address unichainPool = vm.envAddress("UNICHAIN_POOL_ADDRESS");
        address unichainExecutor = vm.envAddress("UNICHAIN_EXECUTOR_ADDRESS");

        require(reactiveAddr != address(0), "MISSING_REACTIVE");
        require(basePool != address(0) && baseExecutor != address(0), "MISSING_BASE_DATA");
        require(unichainPool != address(0) && unichainExecutor != address(0), "MISSING_UNICHAIN_DATA");

        vm.startBroadcast();

        HalfwayReactive reactive = HalfwayReactive(payable(reactiveAddr));

        // Register Base Sepolia pool (Chain ID 84532)
        reactive.registerPool(
            84532,
            basePool,
            baseExecutor,
            18,
            18,
            30 // 0.30% fee
        );
        console.log("Registered Base Sepolia Pool:", basePool);

        // Register Unichain Sepolia pool (Chain ID 1301)
        reactive.registerPool(
            1301,
            unichainPool,
            unichainExecutor,
            18,
            18,
            30 // 0.30% fee
        );
        console.log("Registered Unichain Sepolia Pool:", unichainPool);

        vm.stopBroadcast();
    }
}
