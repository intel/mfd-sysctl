# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for LINUX OS."""

import logging
import re

from mfd_typing import OSName
from mfd_common_libs import add_logging_level, log_levels, os_supported
from .mfd_sysctl import Sysctl
from .exceptions import SysctlException, SysctlExecutionError

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class LinuxSysctl(Sysctl):
    """Class to handle Sysctl in Linux."""

    __init__ = os_supported(OSName.LINUX)(Sysctl.__init__)

    def set_busy_poll(self, value: int = 0) -> str:
        """
        Set sysctl.net.core.busy_poll to value.

        :param value: value to set
        :raises SysctlExecutionError: if the sysctl command execution failed
        :return: sysctl output
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Setting sysctl busy poll value")
        command = f"{self._tool_exec} -w net.core.busy_poll={value}"
        output = self._connection.execute_command(command)
        if output.stderr:
            raise SysctlExecutionError(f"Error while setting busy poll value, {output.stderr}")
        return output.stdout

    def get_busy_poll(self) -> str:
        """Get sysctl.net.core.busy_poll value.

        :raises SysctlExecutionError: if the sysctl command execution failed
        :return: sysctl output
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Getting sysctl busy poll value")
        command = f"{self._tool_exec} -n net.core.busy_poll"
        output = self._connection.execute_command(command)
        if output.stderr:
            raise SysctlExecutionError(f"Error while getting busy poll value, {output.stderr}")
        return output.stdout

    def change_network_buffers_size(self, buffer_size: int = 26214400) -> None:
        """
        Set Linux network buffers to desired size.

        :param buffer_size: Desired size of buffer in bytes.
        Default value of buffer_size set to the maximum package size of 26214400 bytes.
        :raises SysctlExecutionError: if the sysctl command execution failed
        """
        core_buffers = ("net/core/rmem_max", "net/core/wmem_max")
        ipv4_buffers = ("net/ipv4/udp_mem", "net/ipv4/tcp_mem", "net/ipv4/tcp_wmem", "net/ipv4/tcp_rmem")

        logger.log(
            level=log_levels.MODULE_DEBUG,
            msg=f"Setting network buffer max size to {buffer_size / pow(1024, 2):.2f} megabytes",
        )
        for _buffer in core_buffers:
            command = f"{self._tool_exec} -w {_buffer}={buffer_size!s}"
            output = self._connection.execute_command(command)
            if output.stderr:
                raise SysctlExecutionError(f"Error while setting core buffer size, {output.stderr}")

        for _buffer in ipv4_buffers:
            command = f"{self._tool_exec} -w {_buffer}='{buffer_size!s} {buffer_size!s} {buffer_size!s}'"
            output = self._connection.execute_command(command)
            if output.stderr:
                raise SysctlExecutionError(f"Error while setting ipv4 buffer size, {output.stderr}")

    def set_ipv6_autoconf(self, interface: str, enable: bool = True) -> bool:
        """Enable/Disable ipv6 autoconfiguration status.

        :param interface: Name of an interface
        :param enable: True for enabling and False for disabling
        :raises SysctlExecutionError: when sysctl command execution failed
        :return: True for success
        """
        value = "1" if enable is True else "0"
        cmds = [
            f"{self._tool_exec} -w net.ipv6.conf.{interface}.autoconf={value}",
            f"{self._tool_exec} -w net.ipv6.conf.{interface}.accept_ra={value}",
        ]
        for cmd in cmds:
            output = self._connection.execute_command(cmd)
            if output.stderr:
                raise SysctlExecutionError(f"Error while setting sysctl value, {output.stderr}")
            if not output.return_code == 0:
                return False
        return True

    def is_ipv6_autoconf_enabled(self, interface: str) -> bool:
        """Get ipv6 autoconfiguration status enabled or disabled.

        :param interface: Name of an interface
        :raises SysctlExecutionError: when sysctl command execution failed
        :raises SysctlException: if output isn't recognised
        :return: True for enabled and False for disabled
        """
        cmds = [
            f"{self._tool_exec} net.ipv6.conf.{interface}.autoconf",
            f"{self._tool_exec} net.ipv6.conf.{interface}.accept_ra",
        ]
        for cmd in cmds:
            output = self._connection.execute_command(cmd)
            if output.stderr:
                raise SysctlExecutionError(f"Error while getting sysctl value, {output.stderr}")
            val_match = re.match(rf"{cmd.split(' ')[1]} = (?P<value>\d)", output.stdout)
            if val_match:
                val = int(val_match.group("value"))
                if not val:
                    return False
            else:
                raise SysctlException("Output from sysctl not recognized")
        return True
