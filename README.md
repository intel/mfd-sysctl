> [!IMPORTANT] 
> This project is under development. All source code and features on the main branch are for the purpose of testing or evaluation and not production ready.

# MFD Sysctl
Module for SYSCTL, module implements [mfd-base-tool](https://github.com/intel/mfd-tool)


## Usage
```python
from mfd_sysctl import Sysctl
from mfd_connect import SSHConnection

conn = SSHConnection(ip='x.x.x.x', username='your_username', password='your_password')
conn.execute_command('sysctl -V')
sysctl_obj = Sysctl(connection=conn)
print(sysctl_obj.get_version())
print(sysctl_obj.check_if_available())
print(sysctl_obj.get_sysctl_value('dev.igb.0.fc'))
print(sysctl_obj.set_sysctl_value('dev.igb.0.fc',3))
print(sysctl_obj.set_busy_poll())
print(sysctl_obj.get_busy_poll())
print(sysctl_obj.change_network_buffers_size())
print(sysctl_obj.get_available_power_states())
print(sysctl_obj.get_log_cpu_no())
print(sysctl_obj.set_icmp_echo())
print(sysctl_obj.get_interrupt_mode())
print(sysctl_obj.set_interrupt_mode(InterruptMode.MSIX))
print(sysctl_obj.get_driver_version('igb0'))
print(sysctl_obj.get_vlan_filter('igb0'))
print(sysctl_obj.set_ipv6_autoconf('lo'))
print(sysctl_obj.is_ipv6_autoconf_enabled('lo'))
print(sysctl_obj.get_current_module_version_unix('igb'))
print(sysctl_obj.set_fwlldp('igb0', is_100g_adapter=True, enabled=True))
print(sysctl_obj.get_fwlldp('igb0', is_100g_adapter=True))
print(sysctl_obj.set_flow_ctrl('igb0', 'tx', True))
print(sysctl_obj.get_flow_ctrl_status('igb0', 'tx'))
print(sysctl_obj.get_flow_ctrl_counter(FlowCtrlCounter.XON_TX, 'mac_stats', 'igb0'))
print(sysctl_obj.get_tunable_value('ix0', 'tx_process_limit'))
print(sysctl_obj.get_eetrack_id('igb0'))
print(sysctl_obj.get_stats('igb0'))
print(sysctl_obj.set_advertise_speed('ix0', ['1g', '10g']))
print(sysctl_obj.get_advertise_speed('ix0'))
```

## Implemented methods
```python
'get_version(self) -> str' - Returns sysctl version
'check_if_available(self) -> None' - Check if sysctl is available in system, raises ToolNotAvailable if not
'get_current_module_version_unix(self, module: str) -> Union[str, None]' - Get current module version

# Below APIs supported in LINUX
'set_busy_poll(self, value: int = 0) -> str' - Set sysctl busy poll value
'get_busy_poll(self) -> str' - Get value of sysctl busy poll
'change_network_buffers_size(self, buffer_size: int = 26214400) -> None' - Change linux network buffer size for core and ipv4 buffers
'set_ipv6_autoconf(self, interface: str, enable: bool = True) -> bool' - Enabling ipv6 autoconfiguration
'is_ipv6_autoconf_enabled(self, interface: str) -> bool' - Get ipv6 autoconfiguration status enabled or disabled

# Below APIs supported in FREEBSD
'get_available_power_states(self) -> List[PowerStates]' - Gets list of available power states
'get_log_cpu_no(self) -> int' - Get number of logical CPU
'set_icmp_echo(self, ignore_broadcasts: bool = True) -> None' - Set icmp echo broadcast
'get_interrupt_mode(self) -> InterruptMode' - Get available interrupt mode
'set_interrupt_mode(self, mode: InterruptMode) -> None' - Set interrupt mode as per input
'get_sysctl_value(self, sysctl_name: str, options: str = "-n") -> Union[str, int]' - Get sysctl value of any user provided sysctl_name
'set_sysctl_value(self, sysctl_name: str, value: int) -> str' - Set sysctl value from user provided value for any user provided sysctl_name
'get_driver_name(self, interface: str) -> Union[str, None]' - Get driver interface name from user provided interface
'get_driver_interface_number(self, interface: str) -> Union[str, None]' - Get driver interface number from user provided interface
'get_driver_version(self, interface: str) -> str' - Get the driver version of adapter
'get_vlan_filter(self, interface: str) -> str' - Get configured filter list
'set_fwlldp(self, interface: str, *, is_100g_adapter: bool, enabled: bool = True) -> str' - Set Firmware LLDP feature on/off
'get_fwlldp(self, interface: str, *, is_100g_adapter: bool) -> bool' - Get Firmware LLDP feature status
'set_flow_ctrl(self, interface: str, direction: str, value: bool) -> Union[str, None]' - Enable/Disable Flow control option on specific direction
'get_flow_ctrl_status(self, interface: str,  direction: str) -> bool' - Get Flow control option on specific direction
'get_flow_ctrl_counter(self, flow_control_counter: FlowCtrlCounter, mac_stats_sysctl_path: str, interface: str) -> int' - Get flow control counter value of an adapter
'get_tunable_value(self, interface: str, tunable_name: str) -> str' - Get an adapter-specific tunable value
'get_eetrack_id(self, interface: str) -> str' - Get eetrack id for an adapter
'get_stats(self, interface: str, name: str = "") -> Dict[str, str]' - Get statistics from specific adapter
'set_advertise_speed(self, interface: str, advertise_speed: list) -> str' - Set specied advertised speed
'convert_advertise_speed_to_table(self, speed: Union[int, str], driver_name: str) -> List[str]' - Convert int advertise speed into table of speeds
'get_advertise_speed(self, interface: str) -> List[str]' - Get list of advertised list
```

## Enums available for user
```python
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
```

## Constants used in some methods 
```python
'NUMERIC_FC_COMPONENTS = dict(rx=1, tx=2)'
```

## OS supported:
* LINUX
* FREEBSD

## Issue reporting

If you encounter any bugs or have suggestions for improvements, you're welcome to contribute directly or open an issue [here](https://github.com/intel/mfd-sysctl/issues).