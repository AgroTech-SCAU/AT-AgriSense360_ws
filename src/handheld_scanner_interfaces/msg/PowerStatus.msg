# Electrical-team interface consumed by the upper-computer software.
std_msgs/Header header

uint8 STATE_OFF=0
uint8 STATE_CONTROL_BOOT=1
uint8 STATE_TIME_ACQUIRE=2
uint8 STATE_NUC_ON=3
uint8 STATE_SENSORS_ON=4
uint8 STATE_SYNC_ARMED=5
uint8 STATE_RUNNING=6
uint8 STATE_SHUTTING_DOWN=7
uint8 STATE_FAULT=255

uint8 state
bool shutdown_requested
bool shutdown_ready

string[] rail_name
bool[] rail_enabled
bool[] rail_power_good
float32[] rail_voltage_v
float32[] rail_current_a

uint32 fault_mask
string detail
