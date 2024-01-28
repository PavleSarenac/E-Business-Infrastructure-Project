// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

contract Order {
    address payable customerEthereumAddress;
    address payable ownerEthereumAddress;
    address payable courierEtheremumAddress;

    constructor(address payable _customerEthereumAddress) {
        customerEthereumAddress = _customerEthereumAddress;
        ownerEthereumAddress = payable(msg.sender);
    }
}