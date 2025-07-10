# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Exceptions for module."""


class SysctlConnectedOSNotSupported(Exception):
    """Handle Sysctl unsupported os exceptions."""


class SysctlException(Exception):
    """Handle Sysctl exceptions."""


class SysctlExecutionError(Exception):
    """Handle Sysctl execution errors."""
