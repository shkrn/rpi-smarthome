# Raspberry Pi スマートリモコン・センサーハブ 仕様書 v0.7

> **このドキュメントの位置づけ:**  
> システムの「正式な現状定義」です。実際の構成が変わったら必ずここも更新してください。  
> 短期の作業メモは `SESSION-HANDOFF.md` を使い、このファイルは肥大化させないようにします。

## 1. 目的

Raspberry Pi 3 Model B 上の Raspberry Pi OS を基盤として、Home Assistant を中心に赤外線リモコン機能と環境センサー機能を統合したスマートホーム用ノードを構成する。  
現時点では BME280 と赤外線送受信が主な稼働対象で、BH1750・MH-Z19E・高出力 IR LED を追加することを前提に設計を進める。

## 2. ハードウェア構成

### 確認済み

| デバイス | 種別 | インターフェース | 備考 |
|---|---|---|---|
| Raspberry Pi 3 Model B | ホスト | — | OS: Raspberry Pi OS |
| BME280 | 温湿度・気圧センサー | I2C bus1 / 0x76 | 稼働中 |
| IR受信モジュール | IR受信 | GPIO17 / `/dev/lirc?` | overlay 設定済み |
| IR送信 LED | IR送信 | GPIO18 / `/dev/lirc?` | overlay 設定済み、出力要強化 |

### 追加予定

| デバイス | 種別 | インターフェース | 状態 |
|---|---|---|---|
| BH1750 | 照度センサー | I2C bus1 / 0x23 or 0x5C | 計画中 |
| MH-Z19E | CO2センサー | UART (GPIO14/15) | 計画中 |
| OSI5LA5A33A-B x2 | IR送信 LED | MOSFET 経由 | 計画中 |
| 2SK2232 | Nch MOSFET | GPIO18 ゲート | 計画中 |

## 3. ソフトウェア構成

### コンテナ

| コンテナ名 | 役割 | 備考 |
|---|---|---|
| `homeassistant` | HA 本体 | ローカルビルド、host network |
| `mosquitto` | MQTT ブローカー | ポート 1883 |

Compose ファイル: `docker-compose.yml`  
HA 設定: `config/configuration.yaml`（コンテナ内 `/config` にマウント）

### ホスト側サービス

| サービス | スクリプト | 役割 |
|---|---|---|
| `bme280-mqtt.service` | `bme280-publisher/bme280_to_mqtt.py` | BME280 → MQTT publish |

## 4. センサー取得方式

HA コンテナがセンサーを直接読むのではなく、**ホスト側 Python → MQTT → HA** の流れで統一する。

```
Raspberry Pi ホスト
  └─ bme280_to_mqtt.py (systemd)
        └─ I2C bus1 / BME280
        └─ MQTT publish → home/bme280 (JSON)
              └─ Mosquitto コンテナ
                    └─ Home Assistant コンテナ
                          └─ MQTT sensor (temperature / humidity / pressure)
```

BH1750・MH-Z19E も同じ方式でホスト Python → MQTT に統一する予定。

## 5. MQTT トピック定義

| トピック | 発行者 | 内容 | 状態 |
|---|---|---|---|
| `home/bme280` | bme280_to_mqtt.py | `{temperature, humidity, pressure}` JSON | 稼働中 |
| `home/bh1750` | bh1750_to_mqtt.py（予定） | `{illuminance}` JSON | 計画中 |
| `home/mhz19e` | mhz19e_to_mqtt.py（予定） | `{co2, temperature}` JSON | 計画中 |

## 6. Home Assistant エンティティ

### センサー

| エンティティ | ソース | 状態 |
|---|---|---|
| `sensor.bme280_temperature` | MQTT `home/bme280` | 稼働中 |
| `sensor.bme280_humidity` | MQTT `home/bme280` | 稼働中 |
| `sensor.bme280_pressure` | MQTT `home/bme280` | 稼働中 |

### 照明制御

| エンティティ | 種別 | 役割 |
|---|---|---|
| `light.my_bedroom_light` | template light | 仮想ライト（推定状態） |
| `input_select.light_mode` | helper | `OFF` / `ON` / `NIGHT` |
| `input_number.light_brightness` | helper | 輝度レベル保持 |

> ⚠️ 照明の状態は IR 送信成功を前提とした「推定」であり、実機フィードバックはない。  
> 手動リモコン操作や IR 失敗で状態がずれる可能性がある。

### IR 送信（shell_command）

| コマンド名 | 送信ファイル | 動作 |
|---|---|---|
| `send_light_step` | `/config/light_step.txt` | 照明切替 |
| `send_light_up` | `/config/light_up.txt` | 照明を明るく |
| `send_light_down` | `/config/light_down.txt` | 照明を暗く |

## 7. GPIO・ピン割り当て

| 機能 | GPIO | 物理ピン | 状態 |
|---|---|---|---|
| I2C SDA | GPIO2 | 3番 | 稼働中 |
| I2C SCL | GPIO3 | 5番 | 稼働中 |
| UART TX | GPIO14 | 8番 | 計画中（MH-Z19E用） |
| UART RX | GPIO15 | 10番 | 計画中（MH-Z19E用） |
| IR 受信 | GPIO17 | 11番 | overlay 設定済み |
| IR 送信 | GPIO18 | 12番 | overlay 設定済み |

## 8. ブート設定 (`/boot/firmware/config.txt`)

```ini
dtparam=i2c_arm=on
enable_uart=1
dtoverlay=gpio-ir,gpio_pin=17
dtoverlay=gpio-ir-tx,gpio_pin=18
```

> ⚠️ `/boot/firmware/cmdline.txt` に `console=serial0,115200` が残っている。  
> MH-Z19E 追加前にこの行から `console=serial0,115200` を削除する必要がある。

## 9. IR コード資産

| ファイル | 場所 | 用途 | 状態 |
|---|---|---|---|
| `light_step.txt` | `config/` | 照明切替 | 管理済み |
| `light_up.txt` | `config/` | 照明アップ | 管理済み |
| `light_down.txt` | `config/` | 照明ダウン | 管理済み |
| `aircon_off.txt` | `~/`（要移動） | エアコン停止 | 未整理 |
| `panasonic_test_on_27c.txt` | `~/`（要移動） | Panasonic AC テスト | 未整理 |

## 10. IR 送信回路の方針

現行は GPIO18 から直接 IR LED を駆動している可能性があり、出力が不十分な場合がある。  
今後は 2SK2232（Nch MOSFET）を低側スイッチとして使い、OSI5LA5A33A-B を 2 個同時点灯する回路に移行する。  
各 LED には個別の電流制限抵抗を入れる。

```
GPIO18 ──[抵抗]──→ 2SK2232 Gate
                     Drain ──[抵抗]──→ LED1 (OSI5LA5A33A-B)
                           ──[抵抗]──→ LED2 (OSI5LA5A33A-B)
                     Source → GND
```

## 11. 設計原則

1. **HA の責務を絞る** — 自動化・UI・MQTT 受信・IR トリガーに集中させる
2. **センサーはホスト Python + MQTT で統一** — コンテナ側にハード依存を増やさない
3. **IR 送信は `ir-ctl` を継続** — 即時性の都合上、shell_command 方式を維持する
4. **状態は推定と明示する** — helper ベースの照明状態は「推定」であることを設計上認める
5. **1 方式に統一する** — センサー取得や設定管理で複数の流儀を混在させない

## 12. 既知のリスク

| 項目 | リスク | 対策方針 |
|---|---|---|
| IR デバイス役割 | `/dev/lirc0` と `lirc1` の送受信が未確認 | `--features` で確認後に設定を固定 |
| IR 出力不足 | 現行 LED が弱い可能性 | MOSFET + 2LED 回路に更新 |
| 照明状態ずれ | 実機フィードバックなし | 現状許容、将来検討 |
| UART 競合 | `serial0` がコンソール使用中 | MH-Z19E 追加前に `cmdline.txt` 修正 |
| MQTT 認証 | `bme280_to_mqtt.py` 内に直書き | 将来 secrets ファイル化 |
| 設定集中 | `configuration.yaml` に集中 | 将来ファイル分割を検討 |

## 13. 更新ルール

以下が変わったら必ずこのファイルを更新する:

- 物理配線・ピン割り当て
- センサーの追加・削除
- MQTT トピック名
- HA エンティティ・helper 名
- Docker Compose 構成
- ブート設定

各項目のステータス表記:

| 表記 | 意味 |
|---|---|
| **確認済み** | 実機で動作確認済み |
| **計画中** | 合意済みだが未実装 |
| **廃止** | 過去の構成（参考のため残存） |
| **未確認** | 推定だが未検証 |
