import json
import time
import serial
import paho.mqtt.client as mqtt

SERIAL_DEV = "/dev/serial0"
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "home/mhz19"
MQTT_USER = "ha"
MQTT_PASS = "polaris"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_start()

while True:
    try:
        ser = serial.Serial(SERIAL_DEV, baudrate=9600, timeout=2)
        ser.write(b'\xff\x01\x86\x00\x00\x00\x00\x00\x79')
        resp = ser.read(9)
        ser.close()

        if len(resp) == 9 and resp[0] == 0xff and resp[1] == 0x86:
            co2 = resp[2] * 256 + resp[3]
            payload = json.dumps({"co2": co2})
            client.publish(MQTT_TOPIC, payload, retain=True)
            print(payload)

    except Exception as e:
        print(f"error: {e}")

    time.sleep(30)
