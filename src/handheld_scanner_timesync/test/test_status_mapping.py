from handheld_scanner_timesync.protocol import (
    BoardSnapshot,
    build_status_fields,
    parse_reply,
    TIME_SOURCE_FAULT,
    TIME_SOURCE_GNSS_LOCKED,
    TIME_SOURCE_HOLDOVER,
    TIME_SOURCE_LOCAL_SYNC,
    UTC_STATUS_ESTIMATED,
    UTC_STATUS_INVALID,
    UTC_STATUS_VALID,
)


TIME_LOCAL = (
    "TIME state=FREE_RUN seen=0 accepted=0 rejected=0 duplicate=0 missing=0 "
    "good=0 period=0 residual=0 freq_ppb=0 pps64=0x0000000000000000 rmc=- "
    "rmc_valid=0 rmc_consistent=0 utc_valid=0 holdover=1 utc=unknown unix=0 "
    "utc_now=0 baud=38400 baud_auto=1 baud_locked=0 baud_switches=201 "
    "uart_dma=1 uart_rx_bytes=0 nmea_valid=0 checksum_err=0 parse_err=0 "
    "output_disciplined=0 mode=LOCAL time_valid=1 time_now=1767226039 "
    "generation=2 firmware=20261020_CFG1 config=SAVED config_seq=8 "
    "config_error=0"
)

TIME_LOCKED = (
    "TIME state=LOCKED seen=120 accepted=120 rejected=0 duplicate=0 missing=0 "
    "good=120 period=1000000000 residual=12 freq_ppb=250 "
    "pps64=0x000000000000001f rmc=- rmc_valid=1 rmc_consistent=1 utc_valid=1 "
    "holdover=0 utc=2026-11-12T07:00:00Z unix=1762930800 utc_now=1762930800 "
    "baud=38400 baud_auto=0 baud_locked=1 baud_switches=1 uart_dma=1 "
    "uart_rx_bytes=100 nmea_valid=120 checksum_err=0 parse_err=0 "
    "output_disciplined=1 mode=GNSS time_valid=1 time_now=1762930800 "
    "generation=3 firmware=20261020_CFG1 config=SAVED config_seq=8 "
    "config_error=0"
)

TIME_HOLDOVER = (
    "TIME state=HOLDOVER seen=0 accepted=0 rejected=0 duplicate=0 missing=0 "
    "good=0 period=1000000000 residual=0 freq_ppb=-120 "
    "pps64=0x0000000000000020 rmc=- rmc_valid=0 rmc_consistent=0 utc_valid=0 "
    "holdover=42 utc=2026-11-12T07:00:01Z unix=0 utc_now=0 baud=38400 "
    "baud_auto=0 baud_locked=1 baud_switches=1 uart_dma=1 uart_rx_bytes=0 "
    "nmea_valid=0 checksum_err=0 parse_err=0 output_disciplined=0 mode=GNSS "
    "time_valid=1 time_now=1762930801 generation=4 "
    "firmware=20261020_CFG1 config=SAVED config_seq=8 config_error=0"
)

TIME_FAULT = (
    "TIME state=FAULT seen=0 accepted=0 rejected=1 duplicate=0 missing=0 "
    "good=0 period=0 residual=0 freq_ppb=0 pps64=0x0 rmc=- rmc_valid=0 "
    "rmc_consistent=0 utc_valid=0 holdover=0 utc=unknown unix=0 utc_now=0 "
    "baud=38400 baud_auto=1 baud_locked=0 baud_switches=0 uart_dma=1 "
    "uart_rx_bytes=0 nmea_valid=0 checksum_err=1 parse_err=0 "
    "output_disciplined=0 mode=GNSS time_valid=1 time_now=0 generation=1 "
    "firmware=20261020_CFG1 config=SAVED config_seq=8 config_error=0"
)

CAMERA = (
    "CAMERA ch1=10000,0,100000 ch2=30000,0,100000 ch3=60000,0,100000 "
    "ch4=90000,0,100000 requested_enabled=0x0 enabled=0x0 "
    "requested_voltage3v3=0x0 voltage3v3=0x0 level_override=0 engine=ACTIVE "
    "slot=650 irq=318170 sched_err=0x0 epoch_sync=LOCKED epoch_count=442 "
    "sync_irq=442 rephase=1 epoch_set_mask=0xF epoch_tim2=2884549509 "
    "mcr=0x281F060F mdier=0x21 mper=56250 mcmp1=54250 mcnt=50212 "
    "period_ticks=4050000,1350000,675000,450000 "
    "pulses=4419,13257,26514,39771"
)

RADAR_OFF = (
    "RADAR profile=OFF requested_arm=0 active=0 pps_width_us=10000 "
    "rmc_delay_ms=80 baud=9600 inverted=0 epoch=CURRENT_PPS "
    "holdover=COMPAT pps_count=0 rmc_count=0 tx_bytes=0 rx_bytes=0 "
    "tx_errors=0 tx_busy=0 err=0x0 engine=ACTIVE epoch_running=1 "
    "epoch_count=444 next_epoch_tick=3370549509 output_arm_pending=0 "
    "output_enabled=0 lidar_capture_repurposed=1"
)

RADAR_ACTIVE = (
    "RADAR profile=MID360 requested_arm=1 active=1 pps_width_us=10000 "
    "rmc_delay_ms=80 baud=9600 inverted=0 epoch=CURRENT_PPS "
    "holdover=COMPAT pps_count=120 rmc_count=120 tx_bytes=9600 rx_bytes=0 "
    "tx_errors=0 tx_busy=0 err=0x0 engine=ACTIVE epoch_running=1 "
    "epoch_count=444 next_epoch_tick=3370549509 output_arm_pending=0 "
    "output_enabled=1 lidar_capture_repurposed=0"
)

IO_REPLY = (
    "IO force1v8=0 force3v3=0 level_override=0 requested_voltage3v3=0x0 "
    "effective_voltage3v3=0x0 requested_enabled=0x0 enabled=0x0 led=LOCAL "
    "led_rgb=0,8,24 led_dma=1"
)


def _snapshot(*lines):
    snapshot = BoardSnapshot()
    for line in lines:
        reply = parse_reply(line)
        assert reply is not None
        assert snapshot.store(reply)
    return snapshot


def test_local_free_run_maps_to_local_sync():
    fields = build_status_fields(_snapshot(TIME_LOCAL, IO_REPLY, CAMERA))
    assert fields.time_source == TIME_SOURCE_LOCAL_SYNC
    assert fields.utc_status == UTC_STATUS_INVALID
    assert fields.pps_locked is False
    assert fields.gnss_rmc_valid is False
    assert fields.pps_count == 0


def test_camera_pulses_become_trigger_count():
    fields = build_status_fields(_snapshot(TIME_LOCAL, CAMERA))
    assert fields.trigger_count == 4419
    assert "pulses=4419,13257,26514,39771" in fields.detail


def test_gnss_locked_mapping():
    fields = build_status_fields(_snapshot(TIME_LOCKED, CAMERA, RADAR_ACTIVE))
    assert fields.time_source == TIME_SOURCE_GNSS_LOCKED
    assert fields.utc_status == UTC_STATUS_VALID
    assert fields.pps_locked is True
    assert fields.gnss_rmc_valid is True
    assert fields.pps_count == 0x1F
    assert fields.frequency_correction_ppm == 0.25
    assert fields.lidar_sync_reported is True


def test_holdover_mapping():
    fields = build_status_fields(_snapshot(TIME_HOLDOVER))
    assert fields.time_source == TIME_SOURCE_HOLDOVER
    assert fields.utc_status == UTC_STATUS_ESTIMATED
    assert fields.pps_locked is False


def test_fault_mapping():
    fields = build_status_fields(_snapshot(TIME_FAULT))
    assert fields.time_source == TIME_SOURCE_FAULT
    assert fields.utc_status == UTC_STATUS_INVALID


def test_missing_time_is_reported_as_fault():
    fields = build_status_fields(_snapshot(CAMERA))
    assert fields.time_source == TIME_SOURCE_FAULT
    assert fields.utc_status == UTC_STATUS_INVALID
    assert "time=missing" in fields.detail


def test_radar_off_is_not_reported_as_lidar_sync():
    fields = build_status_fields(_snapshot(TIME_LOCAL, RADAR_OFF))
    assert fields.lidar_sync_reported is False


def test_unknown_reply_is_rejected_by_snapshot():
    snapshot = BoardSnapshot()
    reply = parse_reply("SERIAL gnss_rx_bytes=0")
    assert reply is not None
    assert snapshot.store(reply) is False
