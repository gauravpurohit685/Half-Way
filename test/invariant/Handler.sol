// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "../../src/tokens/MockERC20.sol";
import {HalfwayExecutor} from "../../src/vault/HalfwayExecutor.sol";
import {MockCallbackProxy} from "../mocks/MockCallbackProxy.sol";

contract Handler is Test {
    HalfwayExecutor public executor;
    MockERC20 public token0;
    MockERC20 public token1;
    MockCallbackProxy public proxy;
    address public reactiveLasna;

    address[] public actors;
    address internal currentActor;

    mapping(address => uint256) public userShares;
    uint256 public totalUserShares;

    constructor(
        HalfwayExecutor executor_,
        MockERC20 token0_,
        MockERC20 token1_,
        MockCallbackProxy proxy_,
        address reactiveLasna_
    ) {
        executor = executor_;
        token0 = token0_;
        token1 = token1_;
        proxy = proxy_;
        reactiveLasna = reactiveLasna_;

        actors.push(address(0x1111));
        actors.push(address(0x2222));
        actors.push(address(0x3333));

        for (uint256 i = 0; i < actors.length; i++) {
            vm.startPrank(actors[i]);
            token0.approve(address(executor), type(uint256).max);
            token1.approve(address(executor), type(uint256).max);
            vm.stopPrank();
        }
    }

    function deposit(uint256 actorIndex, uint256 amount) external {
        currentActor = actors[actorIndex % actors.length];
        amount = bound(amount, 100_000, 100 ether);

        vm.prank(currentActor);
        uint256 shares = executor.deposit(amount, amount, currentActor);
        userShares[currentActor] += shares;
        totalUserShares += shares;
    }

    function withdraw(uint256 actorIndex, uint256 shares) external {
        currentActor = actors[actorIndex % actors.length];
        uint256 balance = executor.balanceOf(currentActor);
        if (balance == 0) return;

        shares = bound(shares, 1, balance);

        vm.prank(currentActor);
        executor.withdraw(shares, currentActor);
        userShares[currentActor] -= shares;
        totalUserShares -= shares;
    }
}
