# Basemessage Resolution Feature

This document describes the basemessage resolution feature implemented in the xRegistry Code Generation CLI, which follows the [xRegistry Message Specification](https://github.com/xregistry/spec/blob/main/message/spec.md#reusing-message-definitions).

## Overview

The `basemessageurl` attribute allows message definitions to inherit from other message definitions, enabling reuse and reducing repetition in message catalogs. This is particularly useful for:

- Defining common message attributes across multiple related messages
- Creating protocol-specific variants of envelope-only messages
- Building message hierarchies for related event types

## How It Works

### Basic Inheritance

When a message definition includes a `basemessageurl` attribute, the xRegistry loader:

1. Resolves the reference to the base message
2. Deep-merges the base message attributes with the current message
3. Attributes in the current message shadow/override those from the base
4. Removes the `basemessageurl` attribute after resolution

### Transitive Resolution

The resolution process is transitive - if the base message itself has a `basemessageurl`, the chain is followed until a message with no base is found. The attributes are then merged from the root of the chain down to the final message.

### Circular Reference Detection

The loader detects circular references (e.g., MessageA → MessageB → MessageA) and prevents infinite loops. When a circular reference is detected, an error is logged but the message is not removed from the document.

### Missing References

Per the xRegistry spec, if a referenced base message cannot be found, no error is generated. The message is processed as if it had no base, with the `basemessageurl` attribute removed.

## Usage Example

```json
{
  "messagegroups": {
    "devices": {
      "messagegroupid": "devices",
      "envelope": "CloudEvents/1.0",
      "messages": {
        "BaseDeviceEvent": {
          "messageid": "BaseDeviceEvent",
          "description": "Base event for all device events",
          "envelope": "CloudEvents/1.0",
          "envelopemetadata": {
            "source": {
              "value": "/devices/{deviceid}",
              "type": "uritemplate"
            },
            "datacontenttype": {
              "value": "application/json"
            }
          },
          "dataschemaformat": "JSONSchema/draft-07"
        },
        "SensorEvent": {
          "messageid": "SensorEvent",
          "description": "Event from sensor devices",
          "basemessageurl": "/messagegroups/devices/messages/BaseDeviceEvent",
          "envelope": "CloudEvents/1.0",
          "envelopemetadata": {
            "type": {
              "value": "com.example.device.sensor"
            },
            "subject": {
              "value": "/sensors/{sensorid}",
              "type": "uritemplate"
            }
          }
        },
        "TemperatureSensorEvent": {
          "messageid": "TemperatureSensorEvent",
          "description": "Temperature sensor reading",
          "basemessageurl": "/messagegroups/devices/messages/SensorEvent",
          "envelope": "CloudEvents/1.0",
          "envelopemetadata": {
            "type": {
              "value": "com.example.device.sensor.temperature"
            }
          }
        }
      }
    }
  }
}
```

After resolution, `TemperatureSensorEvent` will have:
- Its own `type`: `com.example.device.sensor.temperature`
- `subject` inherited from `SensorEvent`: `/sensors/{sensorid}`
- `source` inherited from `BaseDeviceEvent`: `/devices/{deviceid}`
- `datacontenttype` inherited from `BaseDeviceEvent`: `application/json`
- `dataschemaformat` inherited from `BaseDeviceEvent`: `JSONSchema/draft-07`

## Endpoint Message Inheritance

The basemessage mechanism also applies to messages embedded in endpoint definitions:

```json
{
  "endpoints": {
    "device-telemetry": {
      "endpointid": "device-telemetry",
      "usage": ["producer"],
      "protocol": "HTTP",
      "messages": {
        "ActuatorEvent": {
          "messageid": "ActuatorEvent",
          "description": "Event from actuator devices",
          "basemessageurl": "/messagegroups/devices/messages/BaseDeviceEvent",
          "envelope": "CloudEvents/1.0",
          "envelopemetadata": {
            "type": {
              "value": "com.example.device.actuator"
            }
          }
        }
      }
    }
  }
}
```

## Deep Merge Behavior

When merging attributes, the process is "deep" for nested objects:

**Base Message:**
```json
{
  "envelopemetadata": {
    "type": {
      "value": "base.type",
      "required": true
    },
    "source": {
      "value": "base.source"
    }
  }
}
```

**Derived Message:**
```json
{
  "basemessageurl": "/messagegroups/group/messages/Base",
  "envelopemetadata": {
    "type": {
      "value": "derived.type"
    }
  }
}
```

**Result after resolution:**
```json
{
  "envelopemetadata": {
    "type": {
      "value": "derived.type",      // overridden
      "required": true              // inherited
    },
    "source": {
      "value": "base.source"        // completely inherited
    }
  }
}
```

## Testing

Comprehensive unit tests are provided in `test/core/test_basemessage_resolution.py` covering:

- Simple basemessage resolution
- Transitive chain resolution
- Circular reference detection
- Missing reference handling
- Endpoint message inheritance
- Deep merge with nested objects

Run tests with:
```bash
python -m pytest test/core/test_basemessage_resolution.py -v
```

## Implementation Details

The basemessage resolution is implemented in the `MessageResolver` class in `xregistry/generator/xregistry_loader.py`. The resolution happens after resource resolution (schemas, etc.) but before any filtering is applied.

The resolution process is called automatically by:
- `XRegistryLoader.load()` - basic document loading
- `XRegistryLoader.load_stacked()` - stacked document loading
- `XRegistryLoader.load_with_dependencies()` - dependency-resolved loading

This ensures that basemessage references are always resolved regardless of how the document is loaded.
