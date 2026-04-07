import time
import json
import smbus2
import threading
import paho.mqtt.client as mqtt

BH1750_ADDR = 0x23
MEASURE_CMD = 0x10

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "home/bh1750"
MQTT_CONTROL_TOPIC = "home/bh1750/control"  # "fast" / "normal" を受け付ける
MQTT_USER = "ha"
MQTT_PASS = "polaris"

INTERVAL_NORMAL = 10   # 通常間隔（秒）
INTERVAL_FAST   = 1    # 高速間隔（秒）

interval = INTERVAL_NORMAL
interval_lock = threading.Lock()

bus = smbus2.SMBus(1)


def on_message(client, userdata, msg):
    global interval
    payload = msg.payload.decode().strip()
    with interval_lock:
        if payload == "fast":
            interval = INTERVAL_FAST
            print(f"[bh1750] interval -> {INTERVAL_FAST}s (fast mode)", flush=True)
        elif payload == "normal":
            interval = INTERVAL_NORMAL
            print(f"[bh1750] interval -> {INTERVAL_NORMAL}s (normal mode)", flush=True)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_message = on_message
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.subscribe(MQTT_CONTROL_TOPIC)
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

    with interval_lock:
        sleep_sec = interval
    time.sleep(sleep_sec)
