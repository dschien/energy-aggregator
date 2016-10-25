__author__ = 'mitchell'

device_id = "123@rayleigh"

devices_data_resp = [
  {
    "bts": [
      -2.6026,
      51.4546,
      1106
    ],
    "tzo": 2,
    "vsn": "CHANGE_ME",
    "payment_to": 123,
    "model": "GSM Control Expert",
    "last_call": 123,
    "name": "CHANGE_ME",
    "id": device_id,
    "privilege": "owner",
    "created": 123,
    "sensors_access": "all",
    "owner": "CHANGE_ME",
    "ccid": "123",
    "phone": "123",
    "provider": None,
    "provider_txt": None,
    "location": "123"
  },
]

sensor_data_resp = {
  device_id: {
    "1": {
      "last_value": 1,
      "last_call_delta": 25656,
      "last_call": 1467799704984,
      "direction": "input",
      "negated": 1,
      "name": "DIN1",
      "type": "bool"
    },
    "129": {
      "last_value": 0.9500,
      "last_call_delta": 25690,
      "last_call": 1467799704950,
      "direction": "input",
      "name": "AIN1",
      "type": "float",
      "unit": "V",
      "fixed": 2
    },
    "130": {
      "last_value": 0.9400,
      "last_call_delta": 25692,
      "last_call": 1467799704948,
      "direction": "input",
      "name": "AIN2",
      "type": "float",
      "unit": "V",
      "fixed": 2
    },
    "158": {
      "last_value": -65.0000,
      "last_call_delta": 25638,
      "last_call": 1467799705002,
      "direction": "input",
      "name": "GSM",
      "type": "float",
      "unit": "dbm",
      "fixed": 0
    },
    "159": {
      "last_value": 22.7000,
      "last_call_delta": 25674,
      "last_call": 1467799704966,
      "direction": "input",
      "name": "Temperatura",
      "type": "float",
      "unit": "&deg;C",
      "fixed": 1
    },
    "160": {
      "last_value": 17.0400,
      "last_call_delta": 25660,
      "last_call": 1467799704980,
      "direction": "input",
      "name": "Zasilanie",
      "type": "float",
      "unit": "V",
      "fixed": 2
    },
    "17": {
      "last_value": 0,
      "last_call_delta": 25646,
      "last_call": 1467799704994,
      "direction": "output",
      "name": "OUT1",
      "type": "bool",
      "lock": 1413288722000
    },
    "18": {
      "last_value": 0,
      "last_call_delta": 25642,
      "last_call": 1467799704998,
      "direction": "output",
      "name": "OUT2",
      "type": "bool"
    },
    "2": {
      "last_value": 1,
      "last_call_delta": 25651,
      "last_call": 1467799704989,
      "direction": "input",
      "negated": 1,
      "name": "DIN2",
      "type": "bool"
    },
    "70": {
      "last_value": None,
      "direction": "input",
      "name": "Temperatura EXT1",
      "type": "float",
      "unit": "&deg;C",
      "fixed": 1
    },
    "71": {
      "last_value": None,
      "direction": "input",
      "name": "Temperatura EXT2",
      "type": "float",
      "unit": "&deg;C",
      "fixed": 1
    },
    "72": {
      "last_value": None,
      "direction": "input",
      "name": "Temperatura EXT3",
      "type": "float",
      "unit": "&deg;C",
      "fixed": 1
    },
    "bts": {
      "last_value": [
        1467799689000,
        "234",
        "50",
        "77A6",
        "559D"
      ],
      "last_call_delta": 25636,
      "last_call": 1467799705004,
      "enabled": 0,
      "direction": "input",
      "type": "bts"
    },
    "call": {
      "last_value": None,
      "type": "string"
    },
    "e1": {
      "last_value": [
        1413288726967,
        0.0000,
        0.0000,
        0.0000,
        0.0000,
        0.0000,
        0.0000,
        0.0000,
        0.0000
      ],
      "last_call_delta": 25686,
      "last_call": 1467799704954,
      "mbid": "C0",
      "name": "Chiller 1",
      "type": "e3p2",
      "interval": 55
    },
    "e1.i3p": {
      "last_value": [
        1.5600,
        1.2000,
        0.9600
      ],
      "last_call_delta": 25678,
      "last_call": 1467799704962,
      "direction": "input",
      "type": "float3"
    },
    "e1.kwh": {
      "last_value": 69525.0000,
      "last_call_delta": 25686,
      "last_call": 1467799704954,
      "direction": "input",
      "type": "float"
    },
    "e1.v3p": {
      "last_value": [
        225.5000,
        226.6000,
        227.7000
      ],
      "last_call_delta": 25681,
      "last_call": 1467799704959,
      "direction": "input",
      "type": "float3"
    },
    "virt1": {
      "last_value": None,
      "formula": "fixed((val('e1.v3p',0)+val('e1.v3p',1)+val('e1.v3p',2))\/3,1)",
      "name": "Chiller 1",
      "type": "virtual",
      "display": {
        "max": 250,
        "low": 222,
        "alarm": 245,
        "high": 240,
        "min": 220,
        "type": "cgauge3"
      },
      "dunit": "V"
    }
  }
}