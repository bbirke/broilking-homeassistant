# Dashboard and alarms

Recipes that build on top of the integration's entities. All are optional and
self-contained; nothing here changes the integration itself.

Files:

- [`broilking_alarms.yaml`](broilking_alarms.yaml) - a Home Assistant **package**:
  settable meat-probe alarms + a low-pellet alarm + a cook-timer countdown, plus
  helper template entities.
- [`lovelace-smoker-dashboard.yaml`](lovelace-smoker-dashboard.yaml) - a dashboard
  with the alarm controls, live status, grill control, and history.

## 1. Settable probe alarm + low-pellet alarm

Copy `broilking_alarms.yaml` into `config/packages/` and make sure packages are
loaded (once) in `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages/
```

Then **restart** Home Assistant (a package that adds `template:`/`input_*` needs a
restart, not just a reload). It creates:

- `input_number.broilking_probe1_alarm_temp`, `..._probe2_alarm_temp` - the settable
  target temperatures (deg C).
- `input_boolean.broilking_probe1_alarm_enabled`, `..._probe2_...`,
  `..._lowfuel_alarm_enabled` - arm/disarm toggles.
- `sensor.broil_king_grill_temperature` - the grill chamber temp as a clean numeric
  sensor (lifted from the climate entity's `current_temperature` attribute) so it
  graphs and exports easily.
- `binary_sensor.broil_king_probe_1_alarm`, `..._probe_2_alarm`,
  `..._low_pellet_alarm` - "alarm active" signals (armed **and** condition met).
- Automations that raise / auto-dismiss a persistent notification when each alarm
  turns on / off. A 10 s debounce avoids flapping.
- An automation that notifies when the grill's cook timer runs out (it watches
  `sensor.broil_king_smoker_cook_timer_remaining` fall to zero).

> Entity IDs are slugified from the friendly names. If your device is not named
> "Broil King Smoker", check the actual IDs under Settings -> Devices & Services ->
> Entities and adjust the dashboard / queries below.

**Want phone push instead of (or as well as) the dashboard notification?** In the
`*_reached` / `low_fuel` automations, add a `notify.mobile_app_*` service call
alongside `persistent_notification.create`.

## 2. Dashboard

Add a new dashboard (Settings -> Dashboards -> **+ Add dashboard** -> open the
three-dot menu -> **Edit in YAML**) and paste
[`lovelace-smoker-dashboard.yaml`](lovelace-smoker-dashboard.yaml). It shows red
alarm banners only while an alarm is active, the settable targets + arm toggles,
grill control, the cook timer, live status, and a 24 h history graph.

## 3. Cook timer

The **Cook timer** card sets `number.broil_king_smoker_cook_timer` in minutes,
which arms the grill's own timer. Set it to **0** to cancel.

The countdown is the grill's, not Home Assistant's:
`sensor.broil_king_smoker_cook_timer_remaining` is what the control board
reports as left. So a timer set on the grill's panel or in the iQue app shows up
here too, and the two can never drift apart. The package includes an automation
that raises a persistent notification when the remaining minutes reach zero.