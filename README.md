# ha-lossnay

Home Assistant custom integration for Mitsubishi Lossnay ERV (Energy Recovery Ventilator) units, via the MelView cloud API (NZ/AU).

## Features

- **Fan entity** — power on/off, 4 speed presets (low / medium_low / medium_high / boost), percentage speed control
- **Climate entity** — heat exchange mode: Heat Recovery (`heat`), Auto (`auto`), Bypass / Fresh Air (`fan_only`), Off
- **Sensors** — room temp, outdoor temp, supply temp, exhaust temp, core efficiency (%), filter status (ok/replace)
- Polls every 60 seconds; automatically re-authenticates when the MelView session expires

## Requirements

- MelView account (New Zealand or Australia)
- At least one Lossnay ERV unit registered in MelView
- Home Assistant 2024.1 or newer

## Installation

### HACS (recommended)

1. In HACS, go to **Integrations** → **Custom repositories**
2. Add `https://github.com/bronitskiy/ha-lossnay` as an **Integration**
3. Install **Mitsubishi Lossnay ERV**
4. Restart Home Assistant

### Manual

1. Copy `custom_components/lossnay/` into your HA `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Mitsubishi Lossnay ERV**
3. Enter your MelView email and password
4. If you have multiple ERV units, select the one to add
5. Done — entities will appear under the discovered device

## Entities

| Entity | Type | Description |
|---|---|---|
| `fan.<name>` | Fan | Power, fan speed (presets + percentage) |
| `climate.<name>_mode` | Climate | Heat exchange mode (heat / auto / fan_only / off) |
| `sensor.<name>_room_temperature` | Sensor | Room temperature (°C) |
| `sensor.<name>_outdoor_temperature` | Sensor | Outdoor temperature (°C) |
| `sensor.<name>_supply_temperature` | Sensor | Supply air temperature (°C) |
| `sensor.<name>_exhaust_temperature` | Sensor | Exhaust air temperature (°C) |
| `sensor.<name>_core_efficiency` | Sensor | Heat exchanger efficiency (%) |
| `sensor.<name>_filter_status` | Sensor | Filter status: `ok` or `replace` |

## Fan Speed Presets

| Preset | Command | Approx. % |
|---|---|---|
| `low` | FS2 | 25% |
| `medium_low` | FS3 | 50% |
| `medium_high` | FS5 | 75% |
| `boost` | FS6 | 100% |

## Climate / Heat Exchange Modes

| HA Mode | MelView | Description |
|---|---|---|
| `heat` | MD1 | Lossnay heat recovery — extracts heat from exhaust air |
| `auto` | MD3 | Unit automatically selects bypass or heat recovery |
| `fan_only` | MD7 | Bypass — fresh air only, no heat exchange |
| `off` | PW0 | Unit off |

## Extra State Attributes

Both the fan and climate entity expose additional attributes:

- `auto_mode` — `true` when the wall panel Auto mode is active (unit is managing bypass internally)
- `change_filter` — `true` when the filter needs cleaning (also exposed via the Filter Status sensor)
- `fault` — fault string from the unit (empty when no fault)

## Known Limitations

- The MelView API rate-limits aggressive polling. The integration polls every 60 seconds, which is safe. Do not set the interval below 30 seconds.
- Temperature setpoints are not supported — the ERV does not have a temperature target.

## License

MIT
