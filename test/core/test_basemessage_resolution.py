"""Test basemessage resolution in message definitions."""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from xregistry.generator.xregistry_loader import XRegistryLoader


class TestBasemessageResolution(unittest.TestCase):
    """Test basemessage resolution for message definitions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_simple_basemessage_resolution(self):
        """Test simple basemessage reference resolution."""
        # Create a document with a base message and a derived message
        doc = {
            "specversion": "1.0-rc2",
            "messagegroups": {
                "testgroup": {
                    "messagegroupid": "testgroup",
                    "messages": {
                        "BaseMessage": {
                            "messageid": "BaseMessage",
                            "description": "Base message definition",
                            "envelope": "CloudEvents/1.0",
                            "envelopemetadata": {
                                "type": {
                                    "value": "com.example.base"
                                },
                                "source": {
                                    "value": "/base/source"
                                }
                            },
                            "datacontenttype": "application/json"
                        },
                        "DerivedMessage": {
                            "messageid": "DerivedMessage",
                            "description": "Derived message definition",
                            "basemessageurl": "/messagegroups/testgroup/messages/BaseMessage",
                            "envelopemetadata": {
                                "type": {
                                    "value": "com.example.derived"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Write to temp file
        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump(doc, f)
        
        # Load with mocked Model
        with patch('xregistry.generator.xregistry_loader.Model') as MockModel:
            mock_model = Mock()
            mock_model.groups = {
                "messagegroups": {
                    "resources": {
                        "messages": {"singular": "message"}
                    }
                }
            }
            MockModel.return_value = mock_model
            
            loader = XRegistryLoader()
            _, result = loader.load(test_file)
        
        # Verify the derived message inherited from base
        self.assertIsNotNone(result)
        derived = result["messagegroups"]["testgroup"]["messages"]["DerivedMessage"]
        
        # Should have overridden type
        self.assertEqual(derived["envelopemetadata"]["type"]["value"], "com.example.derived")
        
        # Should have inherited source from base
        self.assertEqual(derived["envelopemetadata"]["source"]["value"], "/base/source")
        
        # Should have inherited datacontenttype from base
        self.assertEqual(derived["datacontenttype"], "application/json")
        
        # Should have inherited envelope from base
        self.assertEqual(derived["envelope"], "CloudEvents/1.0")
        
        # basemessageurl should be removed after resolution
        self.assertNotIn("basemessageurl", derived)
    
    def test_transitive_basemessage_resolution(self):
        """Test transitive basemessage chain resolution."""
        doc = {
            "specversion": "1.0-rc2",
            "messagegroups": {
                "testgroup": {
                    "messagegroupid": "testgroup",
                    "messages": {
                        "Level1": {
                            "messageid": "Level1",
                            "description": "Level 1 base",
                            "envelope": "CloudEvents/1.0",
                            "envelopemetadata": {
                                "type": {
                                    "value": "level1.type"
                                },
                                "source": {
                                    "value": "level1.source"
                                }
                            }
                        },
                        "Level2": {
                            "messageid": "Level2",
                            "description": "Level 2 extends Level1",
                            "basemessageurl": "/messagegroups/testgroup/messages/Level1",
                            "envelopemetadata": {
                                "type": {
                                    "value": "level2.type"
                                },
                                "subject": {
                                    "value": "level2.subject"
                                }
                            }
                        },
                        "Level3": {
                            "messageid": "Level3",
                            "description": "Level 3 extends Level2",
                            "basemessageurl": "/messagegroups/testgroup/messages/Level2",
                            "envelopemetadata": {
                                "type": {
                                    "value": "level3.type"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump(doc, f)
        
        with patch('xregistry.generator.xregistry_loader.Model') as MockModel:
            mock_model = Mock()
            mock_model.groups = {
                "messagegroups": {
                    "resources": {
                        "messages": {"singular": "message"}
                    }
                }
            }
            MockModel.return_value = mock_model
            
            loader = XRegistryLoader()
            _, result = loader.load(test_file)
        
        # Verify Level3 inherited from Level2 and Level1
        level3 = result["messagegroups"]["testgroup"]["messages"]["Level3"]
        
        # Should have its own type
        self.assertEqual(level3["envelopemetadata"]["type"]["value"], "level3.type")
        
        # Should have inherited subject from Level2
        self.assertEqual(level3["envelopemetadata"]["subject"]["value"], "level2.subject")
        
        # Should have inherited source from Level1
        self.assertEqual(level3["envelopemetadata"]["source"]["value"], "level1.source")
        
        # Should have inherited envelope from Level1
        self.assertEqual(level3["envelope"], "CloudEvents/1.0")
    
    def test_circular_basemessage_detection(self):
        """Test that circular basemessage references are detected."""
        doc = {
            "specversion": "1.0-rc2",
            "messagegroups": {
                "testgroup": {
                    "messagegroupid": "testgroup",
                    "messages": {
                        "MessageA": {
                            "messageid": "MessageA",
                            "description": "Message A",
                            "basemessageurl": "/messagegroups/testgroup/messages/MessageB"
                        },
                        "MessageB": {
                            "messageid": "MessageB",
                            "description": "Message B",
                            "basemessageurl": "/messagegroups/testgroup/messages/MessageA"
                        }
                    }
                }
            }
        }
        
        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump(doc, f)
        
        with patch('xregistry.generator.xregistry_loader.Model') as MockModel:
            mock_model = Mock()
            mock_model.groups = {
                "messagegroups": {
                    "resources": {
                        "messages": {"singular": "message"}
                    }
                }
            }
            MockModel.return_value = mock_model
            
            loader = XRegistryLoader()
            _, result = loader.load(test_file)
        
        # Messages should still exist (not be removed due to error)
        self.assertIn("MessageA", result["messagegroups"]["testgroup"]["messages"])
        self.assertIn("MessageB", result["messagegroups"]["testgroup"]["messages"])
    
    def test_missing_basemessage_reference(self):
        """Test handling of missing basemessage reference (per spec: no error)."""
        doc = {
            "specversion": "1.0-rc2",
            "messagegroups": {
                "testgroup": {
                    "messagegroupid": "testgroup",
                    "messages": {
                        "DerivedMessage": {
                            "messageid": "DerivedMessage",
                            "description": "Derived message with missing base",
                            "basemessageurl": "/messagegroups/testgroup/messages/NonExistentBase",
                            "envelope": "CloudEvents/1.0",
                            "envelopemetadata": {
                                "type": {
                                    "value": "com.example.derived"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump(doc, f)
        
        with patch('xregistry.generator.xregistry_loader.Model') as MockModel:
            mock_model = Mock()
            mock_model.groups = {
                "messagegroups": {
                    "resources": {
                        "messages": {"singular": "message"}
                    }
                }
            }
            MockModel.return_value = mock_model
            
            loader = XRegistryLoader()
            _, result = loader.load(test_file)
        
        # Message should exist without base attributes
        derived = result["messagegroups"]["testgroup"]["messages"]["DerivedMessage"]
        self.assertEqual(derived["envelopemetadata"]["type"]["value"], "com.example.derived")
        
        # basemessageurl should be removed
        self.assertNotIn("basemessageurl", derived)
    
    def test_basemessage_in_endpoints(self):
        """Test basemessage resolution in endpoint-embedded messages."""
        doc = {
            "specversion": "1.0-rc2",
            "messagegroups": {
                "sharedgroup": {
                    "messagegroupid": "sharedgroup",
                    "messages": {
                        "SharedBase": {
                            "messageid": "SharedBase",
                            "description": "Shared base message",
                            "envelope": "CloudEvents/1.0",
                            "envelopemetadata": {
                                "type": {
                                    "value": "com.example.shared"
                                },
                                "source": {
                                    "value": "/shared/source"
                                }
                            }
                        }
                    }
                }
            },
            "endpoints": {
                "myendpoint": {
                    "endpointid": "myendpoint",
                    "usage": ["producer"],
                    "protocol": "HTTP",
                    "messages": {
                        "EndpointMessage": {
                            "messageid": "EndpointMessage",
                            "description": "Message in endpoint",
                            "basemessageurl": "/messagegroups/sharedgroup/messages/SharedBase",
                            "envelopemetadata": {
                                "type": {
                                    "value": "com.example.endpoint"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump(doc, f)
        
        with patch('xregistry.generator.xregistry_loader.Model') as MockModel:
            mock_model = Mock()
            mock_model.groups = {
                "messagegroups": {
                    "resources": {
                        "messages": {"singular": "message"}
                    }
                },
                "endpoints": {
                    "resources": {
                        "messages": {"singular": "message"}
                    }
                }
            }
            MockModel.return_value = mock_model
            
            loader = XRegistryLoader()
            _, result = loader.load(test_file)
        
        # Verify endpoint message inherited from shared base
        endpoint_msg = result["endpoints"]["myendpoint"]["messages"]["EndpointMessage"]
        
        # Should have overridden type
        self.assertEqual(endpoint_msg["envelopemetadata"]["type"]["value"], "com.example.endpoint")
        
        # Should have inherited source from shared base
        self.assertEqual(endpoint_msg["envelopemetadata"]["source"]["value"], "/shared/source")
        
        # Should have inherited envelope from shared base
        self.assertEqual(endpoint_msg["envelope"], "CloudEvents/1.0")
    
    def test_deep_merge_with_nested_objects(self):
        """Test deep merge of nested objects in basemessage resolution."""
        doc = {
            "specversion": "1.0-rc2",
            "messagegroups": {
                "testgroup": {
                    "messagegroupid": "testgroup",
                    "messages": {
                        "BaseMessage": {
                            "messageid": "BaseMessage",
                            "description": "Base with nested structure",
                            "envelope": "CloudEvents/1.0",
                            "envelopemetadata": {
                                "type": {
                                    "value": "base.type",
                                    "required": True
                                },
                                "source": {
                                    "value": "base.source",
                                    "required": True
                                },
                                "subject": {
                                    "value": "base.subject"
                                }
                            }
                        },
                        "DerivedMessage": {
                            "messageid": "DerivedMessage",
                            "description": "Derived with partial override",
                            "basemessageurl": "/messagegroups/testgroup/messages/BaseMessage",
                            "envelopemetadata": {
                                "type": {
                                    "value": "derived.type"
                                    # required should be inherited
                                },
                                "source": {
                                    "value": "derived.source",
                                    "required": False  # override required flag
                                }
                                # subject should be inherited completely
                            }
                        }
                    }
                }
            }
        }
        
        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump(doc, f)
        
        with patch('xregistry.generator.xregistry_loader.Model') as MockModel:
            mock_model = Mock()
            mock_model.groups = {
                "messagegroups": {
                    "resources": {
                        "messages": {"singular": "message"}
                    }
                }
            }
            MockModel.return_value = mock_model
            
            loader = XRegistryLoader()
            _, result = loader.load(test_file)
        
        derived = result["messagegroups"]["testgroup"]["messages"]["DerivedMessage"]
        
        # Type should be overridden but required should be inherited
        self.assertEqual(derived["envelopemetadata"]["type"]["value"], "derived.type")
        self.assertTrue(derived["envelopemetadata"]["type"]["required"])
        
        # Source should be overridden including required flag
        self.assertEqual(derived["envelopemetadata"]["source"]["value"], "derived.source")
        self.assertFalse(derived["envelopemetadata"]["source"]["required"])
        
        # Subject should be completely inherited
        self.assertEqual(derived["envelopemetadata"]["subject"]["value"], "base.subject")
    
    def test_cross_messagegroup_basemessage_reference(self):
        """Test basemessage reference across messagegroup boundaries."""
        doc = {
            "specversion": "1.0-rc2",
            "messagegroups": {
                "sharedgroup": {
                    "messagegroupid": "sharedgroup",
                    "messages": {
                        "CommonBase": {
                            "messageid": "CommonBase",
                            "description": "Common base message in shared group",
                            "envelope": "CloudEvents/1.0",
                            "envelopemetadata": {
                                "type": {
                                    "value": "com.shared.base"
                                },
                                "source": {
                                    "value": "/shared/base/source"
                                },
                                "datacontenttype": {
                                    "value": "application/json"
                                }
                            }
                        }
                    }
                },
                "derivedgroup": {
                    "messagegroupid": "derivedgroup",
                    "messages": {
                        "DerivedMessage": {
                            "messageid": "DerivedMessage",
                            "description": "Message in different group extending shared base",
                            "basemessageurl": "/messagegroups/sharedgroup/messages/CommonBase",
                            "envelopemetadata": {
                                "type": {
                                    "value": "com.derived.specific"
                                },
                                "subject": {
                                    "value": "/derived/subject"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump(doc, f)
        
        with patch('xregistry.generator.xregistry_loader.Model') as MockModel:
            mock_model = Mock()
            mock_model.groups = {
                "messagegroups": {
                    "resources": {
                        "messages": {"singular": "message"}
                    }
                }
            }
            MockModel.return_value = mock_model
            
            loader = XRegistryLoader()
            _, result = loader.load(test_file)
        
        # Verify cross-group inheritance worked
        derived = result["messagegroups"]["derivedgroup"]["messages"]["DerivedMessage"]
        
        # Should have overridden type
        self.assertEqual(derived["envelopemetadata"]["type"]["value"], "com.derived.specific")
        
        # Should have its own subject
        self.assertEqual(derived["envelopemetadata"]["subject"]["value"], "/derived/subject")
        
        # Should have inherited source from shared base in different group
        self.assertEqual(derived["envelopemetadata"]["source"]["value"], "/shared/base/source")
        
        # Should have inherited datacontenttype from shared base
        self.assertEqual(derived["envelopemetadata"]["datacontenttype"]["value"], "application/json")
        
        # Should have inherited envelope from shared base
        self.assertEqual(derived["envelope"], "CloudEvents/1.0")
    
    def test_cloudevents_to_mqtt_basemessage(self):
        """Test CloudEvents base message extended by MQTT+CloudEvents message with protocol bindings."""
        doc = {
            "specversion": "1.0-rc2",
            "messagegroups": {
                "eventgroup": {
                    "messagegroupid": "eventgroup",
                    "messages": {
                        "BaseCloudEvent": {
                            "messageid": "BaseCloudEvent",
                            "description": "Base CloudEvents message",
                            "envelope": "CloudEvents/1.0",
                            "envelopemetadata": {
                                "type": {
                                    "value": "com.example.sensor.reading"
                                },
                                "source": {
                                    "value": "/sensors/{sensorid}"
                                },
                                "datacontenttype": {
                                    "value": "application/json"
                                }
                            },
                            "dataschemaurl": "#/schemagroups/eventgroup/schemas/SensorReading"
                        },
                        "MqttSensorEvent": {
                            "messageid": "MqttSensorEvent",
                            "description": "MQTT-specific sensor event with topic and QoS",
                            "basemessageurl": "/messagegroups/eventgroup/messages/BaseCloudEvent",
                            "protocol": "MQTT/5.0",
                            "protocolmetadata": {
                                "topic": {
                                    "value": "sensors/{sensorid}/readings"
                                },
                                "qos": {
                                    "value": 1
                                },
                                "retain": {
                                    "value": False
                                }
                            },
                            "envelopemetadata": {
                                "type": {
                                    "value": "com.example.sensor.mqtt.reading"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump(doc, f)
        
        with patch('xregistry.generator.xregistry_loader.Model') as MockModel:
            mock_model = Mock()
            mock_model.groups = {
                "messagegroups": {
                    "resources": {
                        "messages": {"singular": "message"}
                    }
                }
            }
            MockModel.return_value = mock_model
            
            loader = XRegistryLoader()
            _, result = loader.load(test_file)
        
        # Verify MQTT message inherited from CloudEvents base
        mqtt_msg = result["messagegroups"]["eventgroup"]["messages"]["MqttSensorEvent"]
        
        # Should have protocol set to MQTT
        self.assertEqual(mqtt_msg["protocol"], "MQTT/5.0")
        
        # Should have inherited envelope from CloudEvents base
        self.assertEqual(mqtt_msg["envelope"], "CloudEvents/1.0")
        
        # Should have overridden type in envelope metadata
        self.assertEqual(mqtt_msg["envelopemetadata"]["type"]["value"], "com.example.sensor.mqtt.reading")
        
        # Should have MQTT-specific protocol metadata (topic, qos, retain)
        self.assertEqual(mqtt_msg["protocolmetadata"]["topic"]["value"], "sensors/{sensorid}/readings")
        self.assertEqual(mqtt_msg["protocolmetadata"]["qos"]["value"], 1)
        self.assertFalse(mqtt_msg["protocolmetadata"]["retain"]["value"])
        
        # Should have inherited source from CloudEvents base
        self.assertEqual(mqtt_msg["envelopemetadata"]["source"]["value"], "/sensors/{sensorid}")
        
        # Should have inherited datacontenttype from CloudEvents base
        self.assertEqual(mqtt_msg["envelopemetadata"]["datacontenttype"]["value"], "application/json")
        
        # Should have inherited dataschemaurl from CloudEvents base
        self.assertEqual(mqtt_msg["dataschemaurl"], "#/schemagroups/eventgroup/schemas/SensorReading")


if __name__ == '__main__':
    unittest.main()
