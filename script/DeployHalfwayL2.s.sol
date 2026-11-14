// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { MockERC20 } from "../src/tokens/MockERC20.sol";
import { HalfPair } from "../src/amm/HalfPair.sol";
import { HalfwayExecutor } from "../src/vault/HalfwayExecutor.sol";

contract DeployHalfwayL2 is Script {
    address public constant BASE_SEPOLIA_PROXY = 0xa6eA49Ed671B8a4dfCDd34E36b7a75Ac79B8A5a6;
    address public constant UNICHAIN_SEPOLIA_PROXY = 0x9299472A6399Fd1027ebF067571Eb3e3D7837FC4;

    function run()
        external
        returns (
            address token0Addr,
            address token1Addr,
            address poolAddr,
            address executorAddr
        )
    {
        uint256 chainId = block.chainid;
        address callbackProxy;
        if (chainId == 84532) {
            callbackProxy = BASE_SEPOLIA_PROXY;
        } else if (chainId == 1301) {
            callbackProxy = UNICHAIN_SEPOLIA_PROXY;
        } else {
            revert("INVALID_CHAIN: Must be Base Sepolia (84532) or Unichain Sepolia (1301)");
        }

        address reactiveContract = vm.envAddress("REACTIVE_CONTRACT_ADDRESS");
        require(reactiveContract != address(0), "MISSING_REACTIVE_ADDRESS");

        vm.startBroadcast();

        // 1. Deploy test tokens
        MockERC20 mHalf = new MockERC20("Halfway Test Token", "mHALF", 18, msg.sender);
        MockERC20 mWeth = new MockERC20("Wrapped Ether Test", "mWETH", 18, msg.sender);

        address t0 = address(mHalf) < address(mWeth) ? address(mHalf) : address(mWeth);
        address t1 = address(mHalf) < address(mWeth) ? address(mWeth) : address(mHalf);

        token0Addr = t0;
        token1Addr = t1;

        // 2. Deploy Constant-Product AMM Pool
        HalfPair pool = new HalfPair(t0, t1);
        poolAddr = address(pool);

        // 3. Deploy HalfwayExecutor vault
        HalfwayExecutor executor = new HalfwayExecutor(
            payable(callbackProxy),
            reactiveContract,
            t0,
            t1,
            poolAddr,
            msg.sender
        );
        executorAddr = address(executor);

        // 4. Seed Pool Liquidity: 100 mHALF and 100 mWETH
        mHalf.mint(msg.sender, 1000 ether);
        mWeth.mint(msg.sender, 1000 ether);

        mHalf.transfer(poolAddr, 100 ether);
        mWeth.transfer(poolAddr, 100 ether);
        pool.mint(msg.sender);

        // 5. Seed Vault Inventory: 20 mHALF and 20 mWETH
        mHalf.approve(executorAddr, type(uint256).max);
        mWeth.approve(executorAddr, type(uint256).max);
        uint256 amt0 = t0 == address(mHalf) ? 20 ether : 20 ether;
        uint256 amt1 = t1 == address(mWeth) ? 20 ether : 20 ether;
        executor.deposit(amt0, amt1, msg.sender);

        console.log("=== L2 DEPLOYMENT SUMMARY (Chain ID:", chainId, ") ===");
        console.log("Token0:", t0);
        console.log("Token1:", t1);
        console.log("HalfPair:", poolAddr);
        console.log("HalfwayExecutor:", executorAddr);
        console.log("CallbackProxy:", callbackProxy);
        console.log("Authorized Reactive:", reactiveContract);

        vm.stopBroadcast();
    }
}
