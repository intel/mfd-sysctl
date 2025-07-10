# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Main module."""

import logging
import re

from typing import Union, TYPE_CHECKING
from mfd_base_tool import ToolTemplate
from mfd_base_tool.exceptions import ToolNotAvailable
from mfd_typing import OSName, OSBitness
from mfd_common_libs import add_logging_level, log_levels
from .exceptions import SysctlException, SysctlExecutionError, SysctlConnectedOSNotSupported

if TYPE_CHECKING:
    from mfd_connect import Connection

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class Sysctl(ToolTemplate):
    """Class for Sysctl."""

    def __new__(cls, connection: "Connection"):
        """
        Choose Sysctl subclass based on provided connection object.

        :param connection: connection
        :return: instance of LinuxSysctl subclass
        """
        if cls != Sysctl:
            return super().__new__(cls)

        from .linux import LinuxSysctl
        from .freebsd import FreebsdSysctl

        os_name = connection.get_os_name()
        os_name_to_class = {
            OSName.LINUX: LinuxSysctl,
            OSName.FREEBSD: FreebsdSysctl,
        }

        if os_name not in os_name_to_class.keys():
            raise SysctlConnectedOSNotSupported(f"Not supported OS for Sysctl: {os_name}")

        owner_class = os_name_to_class.get(os_name)
        return super().__new__(owner_class)

    def __init__(self, connection: "Connection") -> None:
        """Initialize SYSCTL."""
        super().__init__(connection=connection)

    tool_executable_name = {
        (OSName.LINUX, OSBitness.OS_32BIT): "sysctl",
        (OSName.LINUX, OSBitness.OS_64BIT): "sysctl",
        (OSName.FREEBSD, OSBitness.OS_32BIT): "sysctl",
        (OSName.FREEBSD, OSBitness.OS_64BIT): "sysctl",
    }

    def _get_tool_exec_factory(self) -> str:
        """Get correct tool name.

        :return: tool name
        """
        return self.tool_executable_name[(self._connection.get_os_name(), self._connection.get_os_bitness())]

    def get_version(self) -> str:
        """
        Get version of tool.

        :raises: SysctlExecutionError when execution failed or SysctlException when version not found
        :return: tool version
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Getting version of {self._tool_exec}")
        if self._connection.get_os_name().value == "Linux":
            try:
                output = self._connection.execute_command(
                    f"{self._tool_exec} -V", expected_return_codes=None, stderr_to_stdout=True
                ).stdout
                invalid_regex = "sysctl: (invalid|illegal) option"
                if re.search(invalid_regex, output):
                    raise SysctlExecutionError("Invalid option executed")
                regex = r"(?P<ver>[\d\.]+)"
                match = re.search(regex, output)
                if match:
                    return match.group("ver")
                else:
                    raise SysctlException("Version not found")
            except SysctlExecutionError as e:
                raise SysctlExecutionError("Version not found") from e
        if self._connection.get_os_name().value == "FreeBSD":
            logger.log(
                level=log_levels.MODULE_DEBUG, msg=f"There is no support to check {self._tool_exec} version in FREEBSD"
            )
            return "N/A"

    def check_if_available(self) -> None:
        """
        Check if tool is available in system.

        :raises ToolNotAvailable when tool not available.
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Check if Sysctl is available")
        if self._connection.get_os_name().value == "Linux":
            command = f"{self._tool_exec} -V"
            self._connection.execute_command(command, custom_exception=ToolNotAvailable)
        if self._connection.get_os_name().value == "FreeBSD":
            command = f"{self._tool_exec} -i does.not.exist"
            self._connection.execute_command(command, custom_exception=ToolNotAvailable)

    def get_current_module_version_unix(self, module: str) -> Union[str, None]:
        """Get current module version.

        :param module: Name of a module
        :raises SysctlExecutionError: when sysctl command execution failed
        :raises SysctlException: if output parsing failed
        :return: version of module if success, else returns None
        """
        if "BSD" in self._connection.get_os_name().value:
            command = f"{self._tool_exec} -n dev.{module}.0.iflib.driver_version"
            output = self._connection.execute_command(command)
            if output.stderr:
                raise SysctlExecutionError(f"Error while executing sysctl value, {output.stderr}")
            if output.return_code == 0:
                return output.stdout.strip()
            command = f"{self._tool_exec} -n dev.{module}.0.%desc"
            output = self._connection.execute_command(command)
            if output.stderr:
                raise SysctlExecutionError(f"Error while executing sysctl value, {output.stderr}")
            if output.return_code == 0:
                return output.stdout.split()[-1]
            return None

        if "Linux" not in self._connection.get_os_name().value:
            return None

        command = "modinfo " + module + " | grep -w version"
        output = self._connection.execute_command(command, shell=True)
        if output.stderr:
            raise SysctlExecutionError(f"Error while executing sysctl value, {output.stderr}")

        module_installed_version = output.stdout.split()
        if not module_installed_version:
            raise SysctlException(f"Could not parse modinfo output to find current module version: {output.stdout}")

        return module_installed_version[1].replace("-unreleased", "").replace("-", "_")
