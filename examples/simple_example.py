# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT

# Put here only the dependencies required to run the module.
# Development and test requirements should go to the corresponding files.
"""Simple example of usage."""
from mfd_sysctl import Sysctl
from mfd_connect import SSHConnection
from mfd_sysctl.enums import InterruptMode, FlowCtrlCounter

conn = SSHConnection(ip="x.x.x.x", username="your_username", password="your_password")
conn.execute_command("sysctl -V")
sysctl_obj = Sysctl(connection=conn)
print(sysctl_obj.get_version())
print(sysctl_obj.check_if_available())
print(sysctl_obj.get_sysctl_value("dev.igb.0.fc"))
print(sysctl_obj.set_sysctl_value("dev.igb.0.fc", 3))
print(sysctl_obj.set_busy_poll())
print(sysctl_obj.get_busy_poll())
print(sysctl_obj.change_network_buffers_size())
print(sysctl_obj.get_available_power_states())
print(sysctl_obj.get_log_cpu_no())
print(sysctl_obj.set_icmp_echo())
print(sysctl_obj.get_interrupt_mode())
print(sysctl_obj.set_interrupt_mode(InterruptMode.MSIX))
print(sysctl_obj.get_driver_version("igb0"))
print(sysctl_obj.get_vlan_filter("igb0"))
print(sysctl_obj.set_ipv6_autoconf("lo"))
print(sysctl_obj.is_ipv6_autoconf_enabled("lo"))
print(sysctl_obj.get_current_module_version_unix("igb"))
print(sysctl_obj.set_fwlldp("igb0", is_100g_adapter=True, enabled=True))
print(sysctl_obj.get_fwlldp("igb0", is_100g_adapter=True))
print(sysctl_obj.set_flow_ctrl("igb0", "tx", True))
print(sysctl_obj.get_flow_ctrl_status("igb0", "tx"))
print(sysctl_obj.get_flow_ctrl_counter(FlowCtrlCounter.XON_TX, "mac_stats", "igb0"))
print(sysctl_obj.get_tunable_value("ix0", "tx_process_limit"))
print(sysctl_obj.get_eetrack_id("igb0"))
print(sysctl_obj.get_stats("igb0"))
print(sysctl_obj.set_advertise_speed("ix0", ["1G", "10G"]))
print(sysctl_obj.get_advertise_speed("ix0"))
