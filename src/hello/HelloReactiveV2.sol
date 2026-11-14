// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {AbstractReactive} from "@reactive-lib-omni/base/AbstractReactive.sol";
import {ISystemContract} from "@reactive-lib-omni/interfaces/ISystemContract.sol";

/**
 * @title HelloReactiveV2
 * @notice Reactive contract on Reactive Lasna intercepting Pings on Base Sepolia and triggering Pongs on destination chain.
 */
contract HelloReactiveV2 is AbstractReactive {
    event HelloReacted(
        uint256 indexed chainId, address indexed originContract, uint256 indexed pingId, uint256 originBlock
    );

    uint64 public constant CALLBACK_GAS_LIMIT = 300000;

    uint256 public immutable PING_TOPIC_0;
    address public immutable ORIGIN_CONTRACT;
    uint256 public immutable ORIGIN_CHAIN_ID;

    address public destinationContract;
    uint256 public destChainId;
    address public owner;

    uint256 public reactionsCount;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor(
        uint256 originChainId_,
        address originContract_,
        uint256 destChainId_,
        address destinationContract_,
        uint256 pingTopic0_
    ) payable {
        require(originContract_ != address(0), "Zero origin");
        owner = msg.sender;
        ORIGIN_CHAIN_ID = originChainId_;
        ORIGIN_CONTRACT = originContract_;
        destChainId = destChainId_;
        destinationContract = destinationContract_;
        PING_TOPIC_0 = pingTopic0_;

        SYSTEM.subscribe(
            originChainId_, originContract_, pingTopic0_, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
        );
    }

    function setDestination(uint256 destChainId_, address destinationContract_) external onlyOwner {
        require(destinationContract_ != address(0), "Zero destination");
        destChainId = destChainId_;
        destinationContract = destinationContract_;
    }

    function react(LogRecord calldata log_) external onlySystem {
        require(log_.chainId == ORIGIN_CHAIN_ID, "Invalid origin chain");
        require(log_.contractAddress == ORIGIN_CONTRACT, "Invalid origin contract");

        uint256 pingId = log_.topic2;
        reactionsCount++;

        emit HelloReacted(log_.chainId, log_.contractAddress, pingId, log_.blockNumber);

        if (destinationContract != address(0) && destChainId != 0) {
            bytes memory payload =
                abi.encodeWithSignature("callback(address,uint256,uint256)", address(0), pingId, log_.blockNumber);

            ISystemContract.CallbackConfiguration_V_1_0 memory config = ISystemContract.CallbackConfiguration_V_1_0({
                chainId: destChainId, recipient: destinationContract, gasLimit: CALLBACK_GAS_LIMIT, payload: payload
            });

            SYSTEM.requestCallbackV_1_0(config);
        }
    }
}
