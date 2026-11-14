// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MockERC20
 * @notice Testnet-only ERC20 token with a bounded public faucet for Phase 2 testing.
 * @dev Explicitly designated for testnets. Not a real economic asset.
 */
contract MockERC20 is ERC20, Ownable {
    uint8 private immutable _decimals;
    uint256 public constant FAUCET_LIMIT = 1_000 ether;

    error FaucetLimitExceeded(uint256 requested, uint256 maxAllowed);

    event FaucetDripped(address indexed recipient, uint256 amount);

    constructor(string memory name_, string memory symbol_, uint8 decimals_, address initialOwner_)
        ERC20(name_, symbol_)
        Ownable(initialOwner_)
    {
        _decimals = decimals_;
    }

    /// @notice Returns the token decimals.
    function decimals() public view virtual override returns (uint8) {
        return _decimals;
    }

    /// @notice Mints tokens to a designated recipient (Owner only).
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    /// @notice Public faucet for testing within bounded limit.
    /// @param amount Amount to mint (must be <= FAUCET_LIMIT).
    function faucet(uint256 amount) external {
        if (amount > FAUCET_LIMIT) {
            revert FaucetLimitExceeded(amount, FAUCET_LIMIT);
        }
        _mint(msg.sender, amount);
        emit FaucetDripped(msg.sender, amount);
    }
}
