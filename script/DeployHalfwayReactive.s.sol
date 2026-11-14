// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { HalfwayReactive } from "../src/reactive/HalfwayReactive.sol";

contract DeployHalfwayReactive is Script {
    uint256 public constant ALLOWED_CHAIN_ID = 5318007; // Reactive Lasna

    function run() external returns (address reactiveAddr) {
        require(block.chainid == ALLOWED_CHAIN_ID, "INVALID_CHAIN: Must be Reactive Lasna (5318007)");

        vm.startBroadcast();

        HalfwayReactive reactive = new HalfwayReactive{ value: 1.0 ether }(
            50,        // threshold: 50 bps
            10,        // safety margin: 10 bps
            0.005 ether, // max trade size: 0.005 ether per leg
            5,         // cooldown: 5 seconds
            60         // max staleness: 60 seconds
        );

        reactiveAddr = address(reactive);
        console.log("HalfwayReactive deployed at:", reactiveAddr);
        console.log("Funded with 1.0 lREACT");

        vm.stopBroadcast();
    }
}
