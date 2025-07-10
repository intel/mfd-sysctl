# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Tests for `mfd_sysctl` package."""

from textwrap import dedent

import re
import pytest
from mfd_connect import SSHConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_typing import OSName, OSBitness

from mfd_sysctl import Sysctl
from mfd_sysctl.linux import LinuxSysctl
from mfd_sysctl.freebsd import FreebsdSysctl
from mfd_sysctl.exceptions import SysctlException, SysctlExecutionError, SysctlConnectedOSNotSupported


class TestMfdSysctl:
    @pytest.fixture()
    def sysctl(self, mocker):
        mocker.patch("mfd_sysctl.Sysctl.check_if_available", mocker.create_autospec(Sysctl.check_if_available))
        mocker.patch(
            "mfd_sysctl.Sysctl.get_version",
            mocker.create_autospec(Sysctl.get_version, return_value="3.3.12"),
        )
        mocker.patch(
            "mfd_sysctl.Sysctl._get_tool_exec_factory",
            mocker.create_autospec(Sysctl._get_tool_exec_factory, return_value="sysctl"),
        )
        conn = mocker.create_autospec(SSHConnection)
        conn.get_os_name.return_value = OSName.LINUX
        sysctl = Sysctl(connection=conn)
        mocker.stopall()
        return sysctl

    @pytest.mark.parametrize(
        "os_name, os_type, result",
        [(OSName.LINUX, OSBitness.OS_32BIT, "sysctl"), (OSName.LINUX, OSBitness.OS_64BIT, "sysctl")],
    )
    def test__get_tool_exec_factory(self, sysctl, os_name, os_type, result):
        sysctl._connection.get_os_name.return_value = os_name
        sysctl._connection.get_os_bitness.return_value = os_type
        assert sysctl._get_tool_exec_factory() == result

    def test_constructor_returns_linux_instance(self, mocker):
        mocker.patch("mfd_sysctl.Sysctl.check_if_available", mocker.create_autospec(Sysctl.check_if_available))
        mocker.patch(
            "mfd_sysctl.Sysctl.get_version",
            mocker.create_autospec(Sysctl.get_version, return_value="3.3.12"),
        )
        mocker.patch(
            "mfd_sysctl.Sysctl._get_tool_exec_factory",
            mocker.create_autospec(Sysctl._get_tool_exec_factory, return_value="sysctl"),
        )
        conn = mocker.create_autospec(SSHConnection)
        conn.get_os_name.return_value = OSName.LINUX
        assert re.search("LinuxSysctl", str(Sysctl(connection=conn)))

    def test_linux_owner_created(self, mocker, sysctl):
        conn = mocker.create_autospec(SSHConnection)
        conn.get_os_name.return_value = OSName.LINUX
        assert isinstance(sysctl.__new__(LinuxSysctl, connection=conn), LinuxSysctl)

    def test_wrong_owner_created(self, mocker, sysctl):
        conn = mocker.create_autospec(SSHConnection)
        conn.get_os_name.return_value = OSName.FREEBSD
        assert not isinstance(sysctl.__new__(LinuxSysctl, connection=conn), FreebsdSysctl)

    def test_unsupported_os(self, mocker):
        conn = mocker.create_autospec(SSHConnection)
        conn.get_os_name.return_value = OSName.EFISHELL
        with pytest.raises(SysctlConnectedOSNotSupported):
            Sysctl(connection=conn)

    def test_get_version(self, sysctl):
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="3.3.12"
        )
        assert sysctl.get_version() == "3.3.12"

    def test_get_version_not_found(self, sysctl):
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=""
        )
        with pytest.raises(SysctlException, match="Version not found"):
            sysctl.get_version()

    def test_get_version_with_invalid_option(self, sysctl):
        sysctl._connection.execute_command.side_effect = SysctlExecutionError()
        with pytest.raises(SysctlExecutionError):
            sysctl.get_version()

    def test_check_if_available(self, sysctl):
        output = dedent("sysctl from procps-ng 3.3.12")
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="sysctl -V", stdout=output, return_code=0, stderr=""
        )
        sysctl.check_if_available()

    def test_set_busy_poll(self, sysctl):
        output = dedent("net.core.busy_poll = 0")
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout=output, return_code=0, stderr=""
        )
        assert sysctl.set_busy_poll() == output

    def test_set_busy_poll_with_error_in_output(self, sysctl):
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr="Error while setting busy poll value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl.set_busy_poll()

    def test_get_busy_poll(self, sysctl):
        output = dedent("0")
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl.get_busy_poll() == output

    def test_get_busy_poll_with_error_in_output(self, sysctl):
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr="Error while getting busy poll value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl.get_busy_poll()

    def test_change_network_buffers_size(self, sysctl):
        output = dedent("26214400")
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout=output, return_code=0, stderr=""
        )
        sysctl.change_network_buffers_size()

    def test_change_network_buffers_size_with_error_in_output(self, sysctl):
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout="", return_code=0, stderr="Error while setting core buffer size"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl.change_network_buffers_size()

    def test_adapter_set_ipv6_autoconf(self, sysctl):
        output = True
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=True, return_code=0, stderr=""
        )
        assert sysctl.set_ipv6_autoconf("lo") == output

    def test_adapter_set_ipv6_autoconf_error_in_output(self, sysctl):
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=True, return_code=0, stderr="Error while setting sysctl value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl.set_ipv6_autoconf("lo")

    def test_adapter_is_ipv6_autoconf_enabled_error_in_output(self, sysctl):
        sysctl._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=True, return_code=0, stderr="Error while getting sysctl value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl.is_ipv6_autoconf_enabled("lo")

    def test_adapter_is_ipv6_autoconf_enabled_unrecognised_output(self, sysctl):
        sysctl._connection.execute_command.side_effect = SysctlException()
        with pytest.raises(SysctlException):
            sysctl.is_ipv6_autoconf_enabled("lo")

    @pytest.mark.parametrize(
        "output_autoconf, output_accept_ra, expected",
        [
            ("net.ipv6.conf.lo.autoconf = 1", "net.ipv6.conf.lo.accept_ra = 1", True),
            ("net.ipv6.conf.lo.autoconf = 0", "net.ipv6.conf.lo.accept_ra = 0", False),
        ],
    )
    def test_adapter_is_ipv6_autoconf(self, sysctl, output_autoconf, output_accept_ra, expected):
        sysctl._connection.execute_command.side_effect = [
            ConnectionCompletedProcess(args="command", stdout=dedent(output_autoconf), return_code=0, stderr=""),
            ConnectionCompletedProcess(args="command", stdout=dedent(output_accept_ra), return_code=0, stderr=""),
        ]
        assert sysctl.is_ipv6_autoconf_enabled("lo") is expected
