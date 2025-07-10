# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Enums for Sysctl module."""

from enum import Enum


class PowerStates(Enum):
    """Enum class for Sysctl powerstates."""

    S1 = "standby"
    S3 = "mem"
    S4 = "disk"
    S0 = "on"
    S5 = "off"


class InterruptMode(Enum):
    """Enum class for interrupt mode."""

    MSIX = "msix"
    MSI = "msi"
    LEGACY = "legacy"


class FlowCtrlCounter(Enum):
    """Enum class for Flow control counter."""

    XON_TX = "xon_txd"
    XON_RX = "xon_recvd"
    XOFF_TX = "xoff_txd"
    XOFF_RX = "xoff_recvd"
