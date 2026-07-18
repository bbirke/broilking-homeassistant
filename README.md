# Broil King Smoker - Home Assistant integration

A **fully local** Home Assistant integration for a Broil King iQue pellet smoker
(Mongoose OS firmware, ESP32). It talks to the grill directly over your LAN via
its JSON-RPC-over-WebSocket API - no cloud, no app, no AWS tokens. Reverse
engineered from the firmware's own `init.js` and the official app.

## Tested hardware / disclaimer

This integration was developed and tested against **one** grill only: a
**Broil King Regal Pellet 500 Pro Smoker (2024 model)** running the `Broil_King`
iQue firmware. It will most likely work on other iQue-based Broil King pellet
grills that expose the same local RPC API, but that is **untested** - temperature
ranges, command codes, or reported fields may differ on other models.

Use at your own risk: this integration can change your grill's setpoint and mode.
Not affiliated with or endorsed by Broil King / Onward Manufacturing.

## Install (HACS)

1. HACS -> Integrations -> three-dot menu -> **Custom repositories** -> add this
   repo, category **Integration**.
2. Install **Broil King Smoker**, restart Home Assistant.
3. Settings -> Devices & Services -> **Add Integration** -> "Broil King Smoker".
4. Enter the smoker's **IP address** (a device password is only needed if you set
   one in the iQue app).

Or copy `custom_components/broilking/` into your HA `config/custom_components/`
manually and restart.

## Entities

One "Broil King Smoker" device with:

- **climate.broil_king_smoker** - current grill temp, settable target temperature,
  on/off, and preset modes Smoke / Cook / High.
- **sensor** - Meat Probe 1 & 2 (and their targets, disabled by default), Cook
  Time, Preset Mode, Cook Timer Remaining.
- **binary_sensor** - Running, Low Fuel (pellet warning).
- **number.broil_king_smoker_cook_timer** - cook timer in minutes. Setting it
  arms the grill's own timer; 0 clears it.

### Cook timer

Two-way. Writing the Cook Timer number sends the timer to the control board
(action 6), and the grill echoes the configured duration back in
`alarm_Hour_Set` / `alarm_Minute_Set`, so a timer set on the grill's own panel
or in the iQue app shows up in Home Assistant too. The board runs the countdown
itself and reports what is left in `alarm_Hour` / `alarm_Minute`, which is the
Cook Timer Remaining sensor - HA does not keep its own clock.

Temperatures are shown in your HA unit; internally the grill always uses
Fahrenheit and the integration converts.

## Dashboards & alarms

Optional, copy-paste recipes built on these entities live in
[`examples/`](examples/README.md): a settable meat-probe alarm and a low-pellet
alarm (Home Assistant package), plus a ready-made Lovelace dashboard.

## The protocol (decoded)

- Transport: WebSocket `ws://<grill-ip>/rpc`, JSON-RPC, **no authentication** on
  the LAN.
- Custom methods reply asynchronously: the result is inside `response.error.message`
  as a **double-encoded JSON string**, and `error.code == 0` means **success**.
- `GetCurrentTemperatures` **requires** `{"reply":"full"}`.
- **Units:** raw values are always Fahrenheit; convert with `(raw-32)*5/9`. A probe
  reading of `0` = unplugged.
- Control frames go via `SendGenericCommand` `{"command":"...","pass":"..."}`, each
  byte as `"DDD "` (zero-padded 3 decimal digits + space), **without** the checksum
  (firmware appends it). commType byte `00`. UART frame:
  `E1 E1 | len(2) | 00 | func(2) | body | checksum`.

  | action | frame (pre-checksum) | meaning |
  |--------|----------------------|---------|
  | 0 | `E1 E1 00 09 00 30 02 vv`    | power off |
  | 1 | `E1 E1 00 0A 00 30 05 hi lo` | grill setpoint, degrees F (16-bit) |
  | 2 | `E1 E1 00 0A 00 30 06 hi lo` | probe 1 target F |
  | 3 | `E1 E1 00 0A 00 30 09 hi lo` | probe 2 target F |
  | 4 | `E1 E1 00 09 00 30 03 vv`    | display unit |
  | 5 | `E1 E1 00 09 00 30 07 vv`    | mode 0=Off 1=Smoke 2=Cook 3=High |
  | 6 | `E1 E1 00 0A 00 30 0A hh mm` | timer |
  | 7 | `E1 E1 00 09 00 30 0B vv`    | backlight |

## Security note

The grill's local RPC is **unauthenticated**: anyone on the LAN can read its config
(incl. the WiFi password) and download its AWS IoT private key via `FS.Get`. Keep
it on a trusted / IoT VLAN.
