// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import { Script, console } from "forge-std/Script.sol";
import { HelloReactiveV2 } from "../src/hello/HelloReactiveV2.sol";

contract DeployHelloReactiveV2 is Script {
    function run(
        uint256 originChainId,
        address originContract,
        uint256 destChainId,
        address destinationContract
    ) external returns (address) {
        require(block.chainid == 5318007, "Must be Reactive Lasna (5318007)");
        require(originContract != address(0), "Zero originContract");
        require(destinationContract != address(0), "Zero destinationContract");

        uint256 pingTopic0 = uint256(keccak256("Ping(address,uint256,uint256,uint256)"));

        vm.startBroadcast();
        // Deploy and fund with 1.0 lREACT for subscription and execution fees
        HelloReactiveV2 reactive = (new HelloReactiveV2){ value: 1.0 ether }(
            originChainId,
            originContract,
            destChainId,
            destinationContract,
            pingTopic0
        );
        vm.stopBroadcast();

        console.log("HelloReactiveV2 deployed to:", address(reactive));
        return address(reactive);
    }
}
