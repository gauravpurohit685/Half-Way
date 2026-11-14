// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {ISystemContract} from "@reactive-lib-omni/interfaces/ISystemContract.sol";

/**
 * @title MockSystemContract
 * @notice Mock implementation of the Reactive Omni System Contract (0x888...888) for testing.
 */
contract MockSystemContract is ISystemContract {
    struct Subscription {
        uint256 chainId;
        address originContract;
        uint256 topic0;
        uint256 topic1;
        uint256 topic2;
        uint256 topic3;
    }

    Subscription[] public subscriptions;
    CallbackConfiguration_V_1_0[] public requestedCallbacks;

    mapping(address => uint256) public debtMap;

    receive() external payable {}

    function debt(address client_) external view override returns (uint256) {
        return debtMap[client_];
    }

    function setDebt(address client_, uint256 debt_) external {
        debtMap[client_] = debt_;
    }

    function subscribe(
        uint256 chainId_,
        address contract_,
        uint256 topic0_,
        uint256 topic1_,
        uint256 topic2_,
        uint256 topic3_
    ) external override {
        subscriptions.push(
            Subscription({
                chainId: chainId_,
                originContract: contract_,
                topic0: topic0_,
                topic1: topic1_,
                topic2: topic2_,
                topic3: topic3_
            })
        );
    }

    function unsubscribe(
        uint256,
        /* chainId_ */
        address,
        /* contract_ */
        uint256,
        /* topic0_ */
        uint256,
        /* topic1_ */
        uint256,
        /* topic2_ */
        uint256 /* topic3_ */
    )
        external
        override
    {}

    function requestCallback(
        CallbackVersion,
        /* version_ */
        bytes memory /* config_ */
    )
        external
        override
    {}

    function requestCallbackV_1_0(CallbackConfiguration_V_1_0 memory config_) external override {
        requestedCallbacks.push(config_);
    }

    function getSubscriptionCount() external view returns (uint256) {
        return subscriptions.length;
    }

    function getRequestedCallbackCount() external view returns (uint256) {
        return requestedCallbacks.length;
    }

    function getRequestedCallback(uint256 index) external view returns (CallbackConfiguration_V_1_0 memory) {
        require(index < requestedCallbacks.length, "Index out of bounds");
        return requestedCallbacks[index];
    }
}
