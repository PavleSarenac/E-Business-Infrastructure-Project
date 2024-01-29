// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

contract Order {
    address payable customerEthereumAddress;
    address payable ownerEthereumAddress;
    address payable courierEtheremumAddress;

    uint orderPriceInWei;
    bool didCustomerPayForTheOrderFlag = false;
    bool lock = false;

    event CustomerPaidForTheOrder(uint orderId);
    event CourierPickedUpTheOrder(uint orderId);
    event CustomerConfirmedOrderDelivery(uint orderId);

    modifier doesCustomerHaveEnoughMoney {
        require(msg.sender.balance >= orderPriceInWei, "Insufficient funds.");
        _;
    }

    modifier didCustomerNotPayForTheOrder {
        require(!didCustomerPayForTheOrderFlag, "Transfer already complete.");
        _;
    }

    modifier isContractLocked {
        require(!lock, "Contract is no longer usable because order processing is done.");
        _;
    }

    modifier didCustomerPayForTheOrder {
        require(address(this).balance == orderPriceInWei, "Transfer not complete.");
        _;
    }

    modifier isValidCustomerEthereumAddress {
        require(payable(msg.sender) == customerEthereumAddress, "Invalid customer account.");
        _;
    }

    modifier didCourierPickUpTheOrder {
        require(courierEtheremumAddress != address(0), "Delivery not complete.");
        _;
    }

    constructor(address payable _customerEthereumAddress, uint _orderPriceInWei)
    isContractLocked {
        customerEthereumAddress = _customerEthereumAddress;
        ownerEthereumAddress = payable(msg.sender);
        orderPriceInWei = _orderPriceInWei;
    }

    function customerPayOrder(uint orderId) external payable
    isContractLocked doesCustomerHaveEnoughMoney didCustomerNotPayForTheOrder {
        didCustomerPayForTheOrderFlag = true;

        emit CustomerPaidForTheOrder(orderId);
    }

    function courierPickUpOrder(address payable _courierEthereumAddress, uint orderId) external
    isContractLocked didCustomerPayForTheOrder {
        courierEtheremumAddress = _courierEthereumAddress;

        emit CourierPickedUpTheOrder(orderId);
    }

    function customerConfirmDelivery(uint orderId) external
    isContractLocked isValidCustomerEthereumAddress didCustomerPayForTheOrder didCourierPickUpTheOrder {
        uint totalBalance = address(this).balance;
        uint ownerShare = (totalBalance * 80) / 100;
        uint courierShare = totalBalance - ownerShare;

        ownerEthereumAddress.transfer(ownerShare);
        courierEtheremumAddress.transfer(courierShare);

        lock = true;
        emit CustomerConfirmedOrderDelivery(orderId);
    }
}