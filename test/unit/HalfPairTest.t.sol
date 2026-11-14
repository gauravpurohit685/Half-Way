// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "../../src/tokens/MockERC20.sol";
import {HalfPair} from "../../src/amm/HalfPair.sol";

contract HalfPairTest is Test {
    MockERC20 public tokenA;
    MockERC20 public tokenB;
    HalfPair public pair;

    address public user = address(0x1111);

    function setUp() public {
        tokenA = new MockERC20("Test Token A", "TKA", 18, address(this));
        tokenB = new MockERC20("Test Token B", "TKB", 18, address(this));

        pair = new HalfPair(address(tokenA), address(tokenB));

        tokenA.mint(address(this), 10_000 ether);
        tokenB.mint(address(this), 10_000 ether);
    }

    function test_InitialLiquidityMint() public {
        tokenA.transfer(address(pair), 100 ether);
        tokenB.transfer(address(pair), 100 ether);

        uint256 liquidity = pair.mint(address(this));
        assertGt(liquidity, 0);
        assertEq(pair.balanceOf(address(0)), pair.MINIMUM_LIQUIDITY());
        assertEq(pair.totalSupply(), liquidity + pair.MINIMUM_LIQUIDITY());

        (uint112 r0, uint112 r1,) = pair.getReserves();
        assertEq(r0, 100 ether);
        assertEq(r1, 100 ether);
    }

    function test_SwapConstantProduct() public {
        tokenA.transfer(address(pair), 100 ether);
        tokenB.transfer(address(pair), 100 ether);
        pair.mint(address(this));

        // Swap 1 ether of token0 for token1
        address t0 = pair.token0();
        address t1 = pair.token1();

        MockERC20(t0).mint(user, 1 ether);

        vm.startPrank(user);
        MockERC20(t0).transfer(address(pair), 1 ether);

        (uint112 r0, uint112 r1,) = pair.getReserves();
        uint256 expectedOut = pair.getAmountOut(1 ether, r0, r1);

        pair.swap(0, expectedOut, user, "");
        vm.stopPrank();

        assertEq(MockERC20(t1).balanceOf(user), expectedOut);
        assertGt(expectedOut, 0);
    }
}
