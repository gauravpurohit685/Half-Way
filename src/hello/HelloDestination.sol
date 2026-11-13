// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import { AbstractCallback } from "@reactive-lib-omni/base/AbstractCallback.sol";
import { IPayable } from "@reactive-lib-omni/interfaces/IPayable.sol";

/**
 * @title HelloDestination
 * @notice Destination contract receiving callbacks from Reactive Lasna.
 */
contract HelloDestination is AbstractCallback {
    event Pong(
        address indexed sender,
        uint256 indexed pingId,
        uint256 originBlock,
        uint256 arrivalTimestamp
    );

    mapping(uint256 => uint256) public receivedPings;
    uint256 public pongCount;

    constructor(
        address payable callbackProxy_,
        address callbackSender_
    ) AbstractCallback(IPayable(callbackProxy_), callbackSender_) {}

    function callback(
        address sender,
        uint256 pingId,
        uint256 originBlock
    ) external onlyCallbackSender(sender) {
        pongCount++;
        receivedPings[pingId] = block.timestamp;
        emit Pong(sender, pingId, originBlock, block.timestamp);
    }
}
