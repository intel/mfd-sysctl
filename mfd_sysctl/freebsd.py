# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for FREEBSD OS."""

import logging
import re

from typing import Union, List, Dict
from mfd_typing import OSName
from mfd_common_libs import add_logging_level, log_levels, os_supported
from .mfd_sysctl import Sysctl
from .exceptions import SysctlException, SysctlExecutionError
from mfd_sysctl.enums import PowerStates, InterruptMode, FlowCtrlCounter
from mfd_const import FREEBSD_ADVERTISE_SPEED as adv_speed

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class FreebsdSysctl(Sysctl):
    """Class to handle Sysctl in Freebsd."""

    __init__ = os_supported(OSName.FREEBSD)(Sysctl.__init__)

    NUMERIC_FC_COMPONENTS = dict(rx=1, tx=2)

    def _transform_power_state(self, state: str) -> PowerStates:
        """
        Transform the power state.

        :param state: Name of the state, whose powerstate to be transformed
        :raises SysctlException: if state is unknown
        :return: transformed state
        """
        for powerstate in PowerStates:
            if state == powerstate.name or state == powerstate.value:
                return powerstate
        raise SysctlException(f"{state} state is unknown")

    def get_available_power_states(self) -> List[PowerStates]:
        """Get available power states.

        :raises SysctlExecutionError: if the sysctl command execution failed
        :return: List of available power states
        """
        command = f"{self._tool_exec} -n hw.acpi.supported_sleep_state"
        output = self._connection.execute_command(command)
        if output.stderr:
            raise SysctlExecutionError(f"Error while getting available power states: {output.stderr}")
        return_states = []
        for state in output.stdout.strip().split():
            return_states.append(self._transform_power_state(state))
        return return_states

    def get_log_cpu_no(self) -> int:
        """Get the number of logical cpus.

        :raises SysctlExecutionError if the sysctl command execution failed or SysctlException when output not found
        :return: logical cpu count
        """
        command = f"{self._tool_exec} -n hw.ncpu"
        output = self._connection.execute_command(command)
        if output.stderr:
            raise SysctlExecutionError(f"Error while getting number of available cpu: {output.stderr}")
        try:
            out = int(output.stdout.strip())
        except ValueError:
            raise SysctlException(f"Invalid number of logical CPU found: {output.stdout}")
        return out

    def set_icmp_echo(self, ignore_broadcasts: bool = True) -> None:
        """Set icmp broadcast.

        :param ignore_broadcasts: parameter to set enable/disable icmp broadcast
        :raises SysctlExecutionError: if the sysctl command execution failed
        """
        broadcasts_tmp = 0 if ignore_broadcasts else 1
        command = f"{self._tool_exec} -w net.inet.icmp.bmcastecho={broadcasts_tmp}"
        output = self._connection.execute_command(command)
        if output.stderr:
            raise SysctlExecutionError(f"Unable to execute command {command}")

    def get_interrupt_mode(self) -> InterruptMode:
        """Get system-wide interrupt mode.

        :raises SysctlException: if interrupt mode not found
        :return: interrupt mode
        """
        msix_enabled = not bool(int(self.get_sysctl_value("hw.pci.enable_msix")) == 0)
        msi_enabled = not bool(int(self.get_sysctl_value("hw.pci.enable_msi")) == 0)

        if msix_enabled and msi_enabled:
            return InterruptMode.MSIX
        elif not msix_enabled and msi_enabled:
            return InterruptMode.MSI
        elif not msix_enabled and not msi_enabled:
            return InterruptMode.LEGACY
        else:
            raise SysctlException("System interrupt mode is inconsistent")

    def set_interrupt_mode(self, mode: InterruptMode) -> None:
        """Set system-wide interrupt mode.

        :param mode - name of interface mode to be specified
        :raises Exception: if mode value is not in expected list
        """
        if mode == InterruptMode.MSIX:
            self.set_sysctl_value("hw.pci.enable_msix", 1)
            self.set_sysctl_value("hw.pci.enable_msi", 1)
        elif mode == InterruptMode.MSI:
            self.set_sysctl_value("hw.pci.enable_msix", 0)
            self.set_sysctl_value("hw.pci.enable_msi", 1)
        elif mode == InterruptMode.LEGACY:
            self.set_sysctl_value("hw.pci.enable_msix", 0)
            self.set_sysctl_value("hw.pci.enable_msi", 0)
        else:
            raise SysctlException(f"Interrupt mode {mode} is not supported")

    def get_sysctl_value(self, sysctl_name: str, options: str = "-n") -> Union[str, int]:
        """
        Get a sysctl value.

        :param sysctl_name: name of a sysctl variable to get its value
        :param options: options to add to command line
        :raises SysctlExecutionError: if the sysctl command execution failed
        :return: sysctl output
        """
        command = f"{self._tool_exec} {options} {sysctl_name}"
        output = self._connection.execute_command(command, expected_return_codes=[0, 1])
        if output.return_code != 0 or output.stderr:
            raise SysctlExecutionError("Error while getting sysctl value")
        if re.search("\n", output.stdout):
            out = output.stdout.replace("\n", "")
        else:
            out = output.stdout
        if re.search("^[0-9]+$", out):
            return int(out)
        else:
            return out

    def set_sysctl_value(self, sysctl_name: str, value: int) -> str:
        """
        Set a sysctl value.

        :param sysctl_name: name of a sysctl variable to set its value
        :param value: value to set for specified sysctl variable
        :raises SysctlExecutionError: if the sysctl command execution failed
        :return: sysctl output
        """
        command = f"{self._tool_exec} {sysctl_name}={value}"
        output = self._connection.execute_command(command, expected_return_codes=[0, 1])
        if output.return_code != 0 or output.stderr:
            raise SysctlExecutionError(f"Error while setting sysctl value: {output.stderr}")
        return output.stdout

    def get_driver_name(self, interface: str) -> Union[str, None]:
        """Get driver name from user provided interface.

        :param interface: name of an interface
        :return: driver name
        """
        split_driver = re.search(r"(?P<int_name>[a-z]*)(?P<int_number>\d+)", interface)
        if split_driver is None:
            raise SysctlException("Unable to match expected pattern")
        else:
            return split_driver.group("int_name")

    def get_driver_interface_number(self, interface: str) -> Union[str, None]:
        """Get driver interface number from user provided interface.

        :param interface: name of an interface
        :return: driver interface number
        """
        split_driver = re.search(r"(?P<int_name>[a-z]*)(?P<int_number>\d+)", interface)
        if split_driver is None:
            raise SysctlException("Unable to match expected pattern")
        else:
            return split_driver.group("int_number")

    def _get_sysctl_value(self, sysctl_name: str, interface: str, options: str = "-n") -> str:
        """
        Get an adapter-specific sysctl value.

        :param sysctl_name: sysctl name relative to dev.<drv>.<num>
        :param interface: name of an interface
        :param options: options to add to command line
        :return: sysctl output
        """
        sysctl_full = (
            f"dev.{self.get_driver_name(interface)}.{self.get_driver_interface_number(interface)}.{sysctl_name}"
        )
        return self.get_sysctl_value(sysctl_full, options=options)

    def _set_sysctl_value(self, sysctl_name: str, value: int, interface: str) -> str:
        """
        Set and adapter-specific sysctl value.

        :param sysctl_name: sysctl name relative to dev.<drv>.<num>
        :param value: value to set for specified sysctl variable
        :param interface: name of an interface
        :return: sysctl output
        """
        sysctl_full = (
            f"dev.{self.get_driver_name(interface)}.{self.get_driver_interface_number(interface)}.{sysctl_name}"
        )
        return self.set_sysctl_value(sysctl_full, value)

    def get_driver_version(self, interface: str) -> str:
        """Get current driver version for the adapter.

        :param interface: name of an interface
        :return: sysctl output
        """
        try:
            version = self._get_sysctl_value("iflib.driver_version", interface)
        except SysctlExecutionError:
            version = "Unknown"
        return version

    def get_vlan_filter(self, interface: str) -> str:
        """
        Get list of configured filters with debug sysctl.

        :param interface: name of an interface
        :raises SysctlExecutionError: when sysctl command execution failed
        :raises SysctlException: when there is an exception during execution
        :return: sysctl output
        """
        command = f"{self._tool_exec} dev.ixl.{self.get_driver_interface_number(interface)}.debug.filter_list"
        output = self._connection.execute_command(command, expected_return_codes={0})
        if output.stderr:
            raise SysctlExecutionError(f"Error while executing sysctl command, {output.stderr}")
        return output.stdout

    def set_fwlldp(self, interface: str, *, is_100g_adapter: bool, enabled: bool = True) -> str:
        """Set FW-LLDP (Firmware Link Local Discovery Protocol) feature on/off.

        :param interface: Name of an interface
        :param is_100g_adapter: param to mention whether the adapter is 100G or not
        :param enabled: feature on or off
        :raises SysctlException: when there is an exception during sysctl execution
        :return: sysctl output
        """
        fw_lldp_oid = "fw_lldp_agent" if is_100g_adapter else "fw_lldp"
        try:
            output = self._set_sysctl_value(fw_lldp_oid, 1 if enabled else 0, interface)
        except Exception as e:
            raise SysctlException("Error during sysctl command execution") from e
        return output

    def get_fwlldp(self, interface: str, *, is_100g_adapter: bool) -> bool:
        """Get FW-LLDP (Firmware Link Local Discovery Protocol) feature on/off.

        :param interface: Name of an interface
        :param is_100g_adapter: param to mention whether the adapter is 100G or not
        :raises SysctlException: when there is an exception during sysctl execution or incorrect setting found
        return: True/False
        """
        try:
            fwlldp_value = self._get_sysctl_value("fw_lldp_agent" if is_100g_adapter else "fw_lldp", interface)
        except Exception as e:
            raise SysctlException("Error during sysctl command execution") from e
        fwlldp_numeric_mode = re.match(r"(\d)", str(fwlldp_value))
        if fwlldp_numeric_mode is None:
            raise SysctlException("Unable to match expected pattern")
        else:
            fwlldp_numeric_mode_value = int(fwlldp_numeric_mode.group())
            if not 0 <= fwlldp_numeric_mode_value <= 1:
                raise SysctlException(f"Incorrect Link Local Discovery protocol setting: {fwlldp_numeric_mode_value}")
            return bool(fwlldp_numeric_mode_value)

    def set_flow_ctrl(self, interface: str, direction: str, value: bool) -> Union[str, None]:
        """Disable/Enable flow control option.

        :param interface: Name of an interface
        :param direction: Valid directions are:
        'tx' - enable/disable TX Flow Control
        'rx' - enable/disable RX Flow Control
        'autoneg' - set current 'autonegotiate' feature settings (always off on FreeBSD)
        :param value: enabling switch
        :raises SysctlException: when there is an exception during execution or autoneg enable request
        :return: output on success, None on failure
        """
        assert direction in {
            "tx",
            "rx",
            "autoneg",
        }, f"Valid 'direction' values are {{'tx', 'rx', 'autoneg'}}, got {direction} instead"

        if direction == "autoneg":
            # If asked to turn autoneg on - raise exception
            if value:
                raise SysctlException("FreeBSD doesn't support flow control autoneg")
            else:
                # Otherwise return success as autoneg is always off on FreeBSD
                return "FreeBSD doesn't support flow control autonegotiation"

        fc_setting = {direction: value}
        other_mode = "rx" if direction == "tx" else "tx"
        fc_setting[other_mode] = self.get_flow_ctrl_status(interface, other_mode)

        fc_numeric_value = 0
        for mode in "rx", "tx":
            if fc_setting[mode]:
                fc_numeric_value += self.NUMERIC_FC_COMPONENTS[mode]

        try:
            output = self._set_sysctl_value("fc", fc_numeric_value, interface)
            return output
        except Exception as e:
            raise SysctlException("Error during sysctl command execution") from e

    def _get_sysctl_flow_ctrl(self, interface: str) -> set:
        """Get flow control mode reported by sysctl.

        :param interface: Name of an interface
        :raises SysctlException: when flow settings are incorrect
        :return: Set of enabled fc modes out of 'rx' and 'tx'
        """
        fc_value = str(self._get_sysctl_value("fc", interface))
        fc_numeric_mode = re.match(r"(\d)", fc_value)
        if fc_numeric_mode is None:
            raise SysctlException("Unable to match expected pattern")
        else:
            fc_numeric_mode_value = int(fc_numeric_mode.group())
            if not 0 <= fc_numeric_mode_value <= 3:
                raise SysctlException(f"Incorrect flow control setting: {fc_numeric_mode_value}")

        fc_mode = set()
        for direction in "rx", "tx":
            if fc_numeric_mode_value & self.NUMERIC_FC_COMPONENTS[direction]:
                fc_mode.add(direction)
        return fc_mode

    def get_flow_ctrl_status(self, interface: str, direction: str) -> bool:
        """Get flow control status for given(rx or tx) direction.

        :param interface: Name of an interface
        :param direction: Valid directions are:
        'tx' - get current TX Flow Control settings
        'rx' - get current RX Flow Control settings
        'autoneg' - get current 'autonegotiate' feature settings (no way to do that on FreeBSD, always returns False)
        :raises SysctlException: when sysctl get value failed
        :return: True for enabled and False for disabled
        """
        assert direction in {
            "tx",
            "rx",
            "autoneg",
        }, f"Valid 'direction' values are {{'tx', 'rx', 'autoneg'}}, got {direction} instead"

        if direction == "autoneg":
            return False  # FreeBSD isn't able to report FC autoneg state, so we always return False

        try:
            sysctl_fc_mode = self._get_sysctl_flow_ctrl(interface)
        except Exception:
            raise SysctlException("Error while getting sysctl value")

        if direction in sysctl_fc_mode:
            return True
        return False

    def get_flow_ctrl_counter(
        self, flow_control_counter: FlowCtrlCounter, mac_stats_sysctl_path: str, interface: str
    ) -> int:
        """Get flow control counter value for the adapter.

        :param flow_control_counter: one of FlowCtrlCounter
        :param mac_stats_sysctl_path: Sysctl path to mac statistics
        :param interface: Name of an interface
        :return: flow control counter value
        """
        return int(self._get_sysctl_value(mac_stats_sysctl_path + "." + flow_control_counter.value, interface))

    def get_tunable_value(self, interface: str, tunable_name: str) -> str:
        """
        Get an adapter-specific tunable value using sysctl.

        :param interface: Name of an interface
        :param tunable_name: tunable name relative to hw.<drv>
        :raises SysctlException: when sysctl get value failed
        :return: tunable value
        """
        sysctl_full = f"hw.{self.get_driver_name(interface)}.{tunable_name}"
        try:
            return str(self.get_sysctl_value(sysctl_full)).strip()
        except Exception as e:
            raise SysctlException("Error while getting tunable value") from e

    def get_eetrack_id(self, interface: str) -> str:
        """Get EETRACK-ID (firmware version of NVM image) for adapter.

        :param interface: Name of an interface
        :return: firmware version
        """
        try:
            fw_version = self._get_sysctl_value("fw_version", interface)
        except Exception:
            fw_version = "0"
        return fw_version

    def get_stats(self, interface: str, name: str = "") -> Dict[str, str]:
        """Get statistics from specific adapter.

        :param interface: Name of an interface
        :param name: name of statistics to fetch. If not specified, all will be fetched.
        :raises SysctlException: when statistics not found for the given name
        :return: dictionary containing statistics and their values.
        """
        stats = {}
        output = self._get_sysctl_value("", interface, options="")

        regex = re.compile(r"dev\.\w+\.\d+\.(?P<name>\S+):\s*(?P<value>\d+)")
        for match in regex.finditer(output):
            stats[match.group("name")] = match.group("value")

        if name:
            if name in stats:
                return {name: stats[name]}
            raise SysctlException(f"Statistics {name} not found on {interface} adapter")
        return stats

    def set_advertise_speed(self, interface: str, advertise_speed: list) -> str:
        """
        Set advertise speed to the specified speeds used for Auto-negotiation process.

        :param interface: Name of an interface
        :param advertise_speed: advertise link speeds table eg. [1g, 5g].
        :raises SysctlException: if speed is invalid
        :return: sysctl output
        """
        speed_sysctl_value = 0
        for speed in advertise_speed:
            match = re.search("[0-9]+([a-zA-Z]+)", speed)
            if match:
                if match.group(1) in ["g", "G"]:
                    speed = re.sub(match.group(1), "G", speed)
                if match.group(1) in ["mb", "Mb", "mB", "MB"]:
                    speed = re.sub(match.group(1), "Mb", speed)

            if speed not in adv_speed.keys():
                raise SysctlException(f"Value {speed} is not a valid speed")
            else:
                speed_sysctl_value += adv_speed[speed][self.get_driver_name(interface)]
        return self._set_sysctl_value("advertise_speed", speed_sysctl_value, interface)

    def convert_advertise_speed_to_table(self, speed: Union[int, str], drv_name: str) -> List[str]:
        """Convert int advertise speed into table of speeds.

        :param speed: Advrtise speed.
        :param drv_name: Driver name.
        :return: Advertised speed list
        """
        advertise_speed = []
        for speed_name, speed_value in adv_speed.items():
            try:
                if int(speed) & speed_value[drv_name]:
                    advertise_speed.append(speed_name)
            except KeyError:
                pass
        return advertise_speed

    def get_advertise_speed(self, interface: str) -> List[str]:
        """
        Get advertise speed. Those speeds are used for Auto-negotiation process.

        :param interface: Name of an interface
        :return: Advertised speed list
        """
        return self.convert_advertise_speed_to_table(
            speed=self._get_sysctl_value("advertise_speed", interface), drv_name=self.get_driver_name(interface)
        )
