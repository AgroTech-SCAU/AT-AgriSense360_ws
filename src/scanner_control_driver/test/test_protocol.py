from scanner_control_driver.protocol import parse_reply


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


def test_parse_key_values():
    reply = parse_reply(TIME_LOCAL)
    assert reply is not None
    assert reply.command == "TIME"
    assert reply.values["state"] == "FREE_RUN"
    assert reply.values["mode"] == "LOCAL"
    assert reply.values["time_now"] == "1767226039"


def test_parse_help_line_is_tolerated():
    reply = parse_reply(
        "HELP: CONFIG | SAVE | STATUS | TIME | CAMERA | RADAR")
    assert reply is not None
    assert reply.command == "HELP"
    assert reply.values == {}


def test_parse_empty_and_malformed():
    assert parse_reply("") is None
    assert parse_reply("   \r") is None
    assert parse_reply("   ") is None


def test_parse_ok_reply():
    reply = parse_reply("OK")
    assert reply is not None
    assert reply.command == "OK"
    assert reply.values == {}
