# Scanner Mainboard time-source and sensor-time mapping status.
std_msgs/Header header

uint8 TIME_SOURCE_GNSS_LOCKED=0
uint8 TIME_SOURCE_HOLDOVER=1
uint8 TIME_SOURCE_LOCAL_SYNC=2
uint8 TIME_SOURCE_FAULT=3

uint8 UTC_STATUS_VALID=0
uint8 UTC_STATUS_ESTIMATED=1
uint8 UTC_STATUS_INVALID=2

uint8 time_source
uint8 utc_status
bool pps_locked
bool gnss_rmc_valid
bool lidar_sync_reported

uint32 holdover_seconds
int64 estimated_clock_error_ns
float64 frequency_correction_ppm

uint64 pps_count
uint64 trigger_count
uint64 exposure_feedback_count

bool camera_clock_mapping_valid
int64 camera_clock_offset_ns
float64 camera_clock_drift_ppm

string detail
