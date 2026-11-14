// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {IPayable} from "@reactive-lib-omni/interfaces/IPayable.sol";

/**
 * @title MockCallbackProxy
 * @notice Mock destination CallbackProxy that injects the authorized sender into callback payloads.
 */
contract MockCallbackProxy is IPayable {
    mapping(address => uint256) public debtMap;

    receive() external payable {}

    function debt(address client_) external view override returns (uint256) {
        return debtMap[client_];
    }

    /**
     * @notice Simulates relaying a callback from Lasna to the destination executor.
     * @param target Target contract (HalfwayExecutor).
     * @param sender The authorized reactive contract address on Lasna.
     * @param rawPayload The raw payload originally emitted by requestCallbackV_1_0.
     */
    function relayCallback(address target, address sender, bytes memory rawPayload)
        external
        returns (bool success, bytes memory returnData)
    {
        // The first 4 bytes are function selector.
        // The next 32 bytes (offset 4 to 36) hold the first parameter: address sender.
        // The proxy replaces those 32 bytes with the actual authenticated sender.
        bytes memory modifiedPayload = rawPayload;
        assembly {
            // Address is right-aligned in 32-byte word
            mstore(add(modifiedPayload, 36), sender)
        }

        (success, returnData) = target.call(modifiedPayload);
        require(success, string(returnData));
    }
}
