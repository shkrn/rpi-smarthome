import json
import time
import smbus2
import bme280
import paho.mqtt.publish as publish

I2C_BUS = 1
I2C_ADDR = 0x76

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "home/bme280"

MQTT_USER = "ha"
MQTT_PASS = "polaris"

bus = smbus2.SMBus(I2C_BUS)
cal = bme280.load_calibration_params(bus, I2C_ADDR)

while True:
    data = bme280.sample(bus, I2C_ADDR, cal)
    payload = {
        "temperature": round(data.temperature, 2),
        "humidity": round(data.humidity, 2),
        "pressure": round(data.pressure, 2),
    }
    publish.single(
        MQTT_TOPIC,
        payload=json.dumps(payload),
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        auth={"username": MQTT_USER, "password": MQTT_PASS},
    )
    time.sleep(30)
