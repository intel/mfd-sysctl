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
from mfd_sysctl.freebsd import FreebsdSysctl
from mfd_sysctl.exceptions import SysctlException, SysctlExecutionError
from mfd_sysctl.enums import InterruptMode, FlowCtrlCounter


class TestMfdSysctl:
    def test_pass(self):
        assert True

    @pytest.fixture()
    def sysctl_freebsd(self, mocker):
        mocker.patch("mfd_sysctl.Sysctl.check_if_available", mocker.create_autospec(Sysctl.check_if_available))
        mocker.patch(
            "mfd_sysctl.Sysctl.get_version",
            mocker.create_autospec(Sysctl.get_version, return_value="N/A"),
        )
        mocker.patch(
            "mfd_sysctl.Sysctl._get_tool_exec_factory",
            mocker.create_autospec(Sysctl._get_tool_exec_factory, return_value="sysctl"),
        )
        conn = mocker.create_autospec(SSHConnection)
        conn.get_os_name.return_value = OSName.FREEBSD
        conn.get_os_bitness.return_value = OSBitness.OS_32BIT
        sysctl_freebsd = Sysctl(connection=conn)
        mocker.stopall()
        return sysctl_freebsd

    @pytest.mark.parametrize(
        "os_name, os_type, result",
        [(OSName.FREEBSD, OSBitness.OS_32BIT, "sysctl"), (OSName.FREEBSD, OSBitness.OS_64BIT, "sysctl")],
    )
    def test_adapter_get_tool_exec_factory(self, sysctl_freebsd, os_name, os_type, result):
        sysctl_freebsd._connection.get_os_name.return_value = os_name
        sysctl_freebsd._connection.get_os_bitness.return_value = os_type
        assert sysctl_freebsd._get_tool_exec_factory() == result

    def test_constructor_returns_freebsd_instance(self, mocker):
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
        conn.get_os_name.return_value = OSName.FREEBSD
        assert re.search("FreebsdSysctl", str(Sysctl(connection=conn)))

    def test_freebsd_owner_created(self, mocker, sysctl_freebsd):
        conn = mocker.create_autospec(SSHConnection)
        conn.get_os_name.return_value = OSName.FREEBSD
        assert isinstance(sysctl_freebsd.__new__(FreebsdSysctl, connection=conn), FreebsdSysctl)

    def test_adapter_get_version(self, sysctl_freebsd):
        output = dedent("N/A")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output
        )
        assert sysctl_freebsd.get_version() == output

    def test_get_sysctl_value_int_output(self, sysctl_freebsd):
        output = dedent("3")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_sysctl_value("sysctl -n dev.igb.0.fc") == int(output)

    def test_get_sysctl_value_str_output(self, sysctl_freebsd):
        output = dedent("7.6.1-k")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_sysctl_value("dev.igb.0.iflib.driver_version") == output

    def test_get_sysctl_value_with_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr="Error while getting sysctl value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd.get_sysctl_value("dev.igb.0.iflib.driver_version")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=1, stderr="unknown oid: dev.igb.0.iflib.non-existent"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd.get_sysctl_value("dev.igb.0.iflib.non-existent")

    def test_set_sysctl_value(self, sysctl_freebsd):
        output = dedent("3")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.set_sysctl_value("sysctl dev.igb.0.fc", 3) == output

    def test_set_sysctl_value_with_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=1, stderr="Error while setting sysctl value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd.set_sysctl_value("sysctl dev.igb.0.fc", 3)

    def test__transform_power_state(self, sysctl_freebsd):
        output = dedent("disk")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd._transform_power_state("S4").value == output

    def test__transform_power_state_wrong_output(self, sysctl_freebsd):
        output = dedent("mem")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd._transform_power_state("S4") != output

    def test__transform_power_state_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout="", return_code=0, stderr="S6 state is unknown"
        )
        with pytest.raises(SysctlException):
            sysctl_freebsd._transform_power_state("S6")

    def test_get_available_power_states(self, sysctl_freebsd):
        output = ["disk", "off"]
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout="S4", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_available_power_states()[0].value == output[0]

    def test_get_available_power_states_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout="", return_code=0, stderr="state is unknown"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd.get_available_power_states()

    def test_get_log_cpu_no(self, sysctl_freebsd):
        output = dedent("44")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_log_cpu_no() == int(output)

    def test_get_log_cpu_no_zero_return(self, sysctl_freebsd):
        output = dedent("0")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_log_cpu_no() != output

    def test_get_log_cpu_no_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout="", return_code=0, stderr="No such file or directory"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd.get_log_cpu_no()

    def test_set_icmp_echo(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout="", return_code=0, stderr=""
        )
        sysctl_freebsd.set_icmp_echo()

    def test_set_icmp_echo_return_false(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.side_effect = SysctlException()
        with pytest.raises(SysctlException):
            sysctl_freebsd.set_icmp_echo()

    def test_get_interrupt_mode(self, sysctl_freebsd):
        output = dedent("msix")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="1", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_interrupt_mode().value == output

    def test_get_interrupt_mode_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout="", return_code=0, stderr="Error while getting sysctl value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd.get_interrupt_mode()

    def test_set_interrupt_mode(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr=""
        )
        sysctl_freebsd.set_interrupt_mode(InterruptMode.MSIX)

    def test_set_interrupt_mode_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="command", stdout="", return_code=0, stderr="Error while setting sysctl value"
        )
        with pytest.raises(SysctlException):
            sysctl_freebsd.set_interrupt_mode("msis")

    def test__get_sysctl_value(self, sysctl_freebsd):
        output = dedent("7.6.1-k")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd._get_sysctl_value("iflib.driver_version", "igb0") == output

    def test__set_sysctl_value(self, sysctl_freebsd):
        output = dedent("dev.igb.0.fc: 3 -> 1")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd._set_sysctl_value("fc", 1, "igb0") == output

    def test_adapter_get_driver_version(self, sysctl_freebsd):
        output = dedent("7.6.1-k")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_driver_version("igb0") == output

    def test_adapter_get_vlan_filter(self, sysctl_freebsd):
        output = dedent(
            """
                PF Filters:
                f8:f2:DE:AD:BE:EF, vlan   -1, flags 000000
                01:00:DE:AD:BE:EF, vlan   -1, flags 0x0002)
                """
        )
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="sysctl dev.ixl.0.debug.filter_list", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_vlan_filter("igb0") == output

    def test_adapter_set_fwlldp_100G_adapter(self, sysctl_freebsd):
        output = dedent("dev.ixl.0.fw_lldp_agent: 1")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.set_fwlldp("igb0", is_100g_adapter=True, enabled=True) == output

    def test_adapter_set_fwlldp_non_100G_adapter(self, sysctl_freebsd):
        output = dedent("dev.ixl.0.fw_lldp: 1")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.set_fwlldp("igb0", is_100g_adapter=False, enabled=True) == output

    def test_adapter_set_fwlldp_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr="Error while setting sysctl value"
        )
        with pytest.raises(SysctlException):
            sysctl_freebsd.set_fwlldp("igb0", is_100g_adapter=True, enabled=True)

    def test_adapter_get_fwlldp(self, sysctl_freebsd):
        output = True
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="1", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_fwlldp("igb0", is_100g_adapter=True) == output

    def test_adapter_get_fwlldp_incorrect_setting(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.side_effect = SysctlException()
        with pytest.raises(SysctlException):
            sysctl_freebsd.get_fwlldp("igb0", is_100g_adapter=True)

    def test_adapter_set_flow_ctrl_tx(self, sysctl_freebsd):
        output = dedent("3")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.set_flow_ctrl("igb0", "tx", True) == output

    def test_adapter_set_flow_ctrl_rx(self, sysctl_freebsd):
        output = dedent("2")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.set_flow_ctrl("igb0", "rx", False) == output

    def test_adapter_set_flow_ctrl_autoneg_enable(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.side_effect = SysctlException
        with pytest.raises(SysctlException):
            sysctl_freebsd.set_flow_ctrl("igb0", "autoneg", True)

    def test_adapter_set_flow_ctrl_autoneg_disable(self, sysctl_freebsd):
        output = dedent("FreeBSD doesn't support flow control autonegotiation")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.set_flow_ctrl("igb0", "autoneg", False) == output

    def test_adapter__get_sysctl_flow_ctrl(self, sysctl_freebsd):
        output = {"rx"}
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="1", return_code=0, stderr=""
        )
        assert sysctl_freebsd._get_sysctl_flow_ctrl("igb0") == output

    def test_adapter__get_sysctl_flow_ctrl_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="1", return_code=0, stderr="Error while getting sysctl value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd._get_sysctl_flow_ctrl("igb0")

    def test_adapter_get_flow_ctrl_status_tx_enabled(self, sysctl_freebsd):
        output = True
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="3", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_flow_ctrl_status("igb0", "tx") == output

    def test_adapter_get_flow_ctrl_status_tx_disabled(self, sysctl_freebsd):
        output = False
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="1", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_flow_ctrl_status("igb0", "tx") == output

    def test_adapter_get_flow_ctrl_status_rx_enabled(self, sysctl_freebsd):
        output = True
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="3", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_flow_ctrl_status("igb0", "rx") == output

    def test_adapter_get_flow_ctrl_status_rx(self, sysctl_freebsd):
        output = False
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="2", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_flow_ctrl_status("igb0", "rx") == output

    def test_adapter_get_flow_ctrl_status_autoneg(self, sysctl_freebsd):
        output = False
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_flow_ctrl_status("igb0", "autoneg") == output

    def test_adapter_get_flow_ctrl_counter(self, sysctl_freebsd):
        output = dedent("0")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_flow_ctrl_counter(FlowCtrlCounter.XON_RX, "mac_stats", "igb0") == int(output)

    def test_adapter_get_eetrack_id(self, sysctl_freebsd):
        output = dedent("EEPROM V1.52-0 Option ROM V1-b924-p0 eTrack 0x800007ae")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_eetrack_id("igb0") == output

    def test_adapter_get_stats(self, sysctl_freebsd):
        output = {"advertise_speed": "4"}
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="dev.igb.0.advertise_speed: 4", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_stats("igb0", "advertise_speed") == output

    def test_adapter_test_adapter_get_stats_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr="Error while getting sysctl value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd.get_stats("igb0", "advertise_speed")

    def test_adapter_get_current_module_version_unix(self, sysctl_freebsd):
        output = dedent("5.4.0_k")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_current_module_version_unix("igb") == output

    def test_adapter_get_current_module_version_unix_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr="Error while executing sysctl value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd.get_current_module_version_unix("igb")

    def test_adapter_get_tunable_value(self, sysctl_freebsd):
        output = dedent("31250")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_tunable_value("ix0", "max_interrupt_rate") == output

    def test_adapter_get_tunable_value_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr="Error while getting tunable value"
        )
        with pytest.raises(SysctlException):
            sysctl_freebsd.get_tunable_value("ix0", "max_interrupt_rate")

    def test_adapter_set_advertise_speed(self, sysctl_freebsd):
        output = dedent("dev.ix.0.advertise_speed: 2 -> 2")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.set_advertise_speed("ix0", ["1G"]) == output

    def test_adapter_set_advertise_speed_caseinsensitive_input(self, sysctl_freebsd):
        output = dedent("dev.ix.0.advertise_speed: 2 -> 2")
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.set_advertise_speed("ix0", ["1g"]) == output

    def test_adapter_set_advertise_speed_error_in_output(self, sysctl_freebsd):
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="", return_code=0, stderr="Error while setting sysctl value"
        )
        with pytest.raises(SysctlExecutionError):
            sysctl_freebsd.set_advertise_speed("ix0", ["1G"])

    def test_adapter_convert_advertise_speed_to_table(self, sysctl_freebsd):
        output = ["10G"]
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0, stderr=""
        )
        assert sysctl_freebsd.convert_advertise_speed_to_table(4, "ix") == output

    def test_adapter_get_advertise_speed(self, sysctl_freebsd):
        output = ["1G"]
        sysctl_freebsd._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout="2", return_code=0, stderr=""
        )
        assert sysctl_freebsd.get_advertise_speed("ix0") == output
