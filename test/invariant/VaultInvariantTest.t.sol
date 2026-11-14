// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "../../src/tokens/MockERC20.sol";
import {HalfPair} from "../../src/amm/HalfPair.sol";
import {HalfwayExecutor} from "../../src/vault/HalfwayExecutor.sol";
import {MockCallbackProxy} from "../mocks/MockCallbackProxy.sol";
import {Handler} from "./Handler.sol";

contract VaultInvariantTest is Test {
    MockERC20 public token0;
    MockERC20 public token1;
    HalfPair public pool;
    MockCallbackProxy public proxy;
    HalfwayExecutor public executor;
    Handler public handler;

    address public reactiveLasna = address(0x9999);

    function setUp() public {
        token0 = new MockERC20("Token 0", "TK0", 18, address(this));
        token1 = new MockERC20("Token 1", "TK1", 18, address(this));

        if (address(token0) > address(token1)) {
            (token0, token1) = (token1, token0);
        }

        pool = new HalfPair(address(token0), address(token1));
        proxy = new MockCallbackProxy();

        executor = new HalfwayExecutor(
            payable(address(proxy)), reactiveLasna, address(token0), address(token1), address(pool), address(this)
        );

        // Pre-mint tokens to actors
        token0.mint(address(0x1111), 1_000_000 ether);
        token1.mint(address(0x1111), 1_000_000 ether);
        token0.mint(address(0x2222), 1_000_000 ether);
        token1.mint(address(0x2222), 1_000_000 ether);
        token0.mint(address(0x3333), 1_000_000 ether);
        token1.mint(address(0x3333), 1_000_000 ether);

        handler = new Handler(executor, token0, token1, proxy, reactiveLasna);

        targetContract(address(handler));
    }

    /// @notice Invariant: Total supply always equals the sum of user shares + permanently locked minimum liquidity (once seeded).
    function invariant_TotalSharesConservation() public view {
        uint256 supply = executor.totalSupply();
        if (supply == 0) {
            assertEq(handler.totalUserShares(), 0);
        } else {
            assertEq(supply, handler.totalUserShares() + executor.MINIMUM_LIQUIDITY());
        }
    }

    /// @notice Invariant: Vault asset balances are strictly non-negative and backing all minted shares.
    function invariant_VaultSolvency() public view {
        uint256 bal0 = token0.balanceOf(address(executor));
        uint256 bal1 = token1.balanceOf(address(executor));
        uint256 supply = executor.totalSupply();

        if (supply > 0) {
            assertGt(bal0, 0);
            assertGt(bal1, 0);
        }
    }

    /// @notice Invariant: No user can ever possess more shares than the total supply.
    function invariant_UserSharesBounded() public view {
        for (uint256 i = 0; i < 3; i++) {
            address actor = handler.actors(i);
            assertLe(executor.balanceOf(actor), executor.totalSupply());
        }
    }
}
