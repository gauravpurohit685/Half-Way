// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import { Script, console } from "forge-std/Script.sol";
import { HelloDestination } from "../src/hello/HelloDestination.sol";

contract DeployHelloDestinationSepolia is Script {
    address constant SEPOLIA_CALLBACK_PROXY = 0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA;

    function run(address reactiveContract) external returns (address) {
        require(block.chainid == 11155111, "Must be Sepolia (11155111)");
        require(reactiveContract != address(0), "Zero reactiveContract");

        vm.startBroadcast();
        HelloDestination destination = new HelloDestination(
            payable(SEPOLIA_CALLBACK_PROXY),
            reactiveContract
        );
        vm.stopBroadcast();

        console.log("HelloDestination (Sepolia) deployed to:", address(destination));
        return address(destination);
    }
}
