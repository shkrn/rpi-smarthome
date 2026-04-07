import time
import json
import smbus2
import paho.mqtt.client as mqtt

BH1750_ADDR = 0x23
MEASURE_CMD = 0x10

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "home/bh1750"
MQTT_USER = "ha"
MQTT_PASS = "polaris"

bus = smbus2.SMBus(1)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_start()

while True:
    try:
        bus.write_byte(BH1750_ADDR, MEASURE_CMD)
        time.sleep(0.2)
        data = bus.read_i2c_block_data(BH1750_ADDR, MEASURE_CMD, 2)
        lux = (data[0] << 8 | data[1]) / 1.2
        payload = json.dumps({"illuminance": round(lux, 1)})
        client.publish(MQTT_TOPIC, payload, retain=True)
        print(payload, flush=True)
    except Exception as e:
        print(f"error: {e}", flush=True)

    time.sleep(30)
