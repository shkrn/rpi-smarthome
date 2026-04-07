# Raspberry Pi スマートリモコン・センサーハブ 仕様書 v0.8

> **このドキュメントの位置づけ:**  
> システムの「正式な現状定義」です。実際の構成が変わったら必ずここも更新してください。  
> 短期の作業メモは `SESSION-HANDOFF.md` を使い、このファイルは肥大化させないようにします。  
> 配線の詳細・図解は [`docs/wiring-diagram.md`](./wiring-diagram.md) を参照してください。

## 1. 目的

Raspberry Pi 3 Model B 上の Raspberry Pi OS を基盤として、Home Assistant を中心に赤外線リモコン機能と環境センサー機能を統合したスマートホーム用ノードを構成する。  
現時点では BME280 と赤外線送受信が主な稼働対象で、BH1750・MH-Z19E・高出力 IR LED を追加することを前提に設計を進める。

## 2. ハードウェア構成

### 確認済み

| デバイス | 種別 | インターフェース | 備考 |
|---|---|---|---|
| Raspberry Pi 3 Model B | ホスト | — | OS: Raspberry Pi OS |
| BME280（6ピン） | 温湿度・気圧センサー | I2C bus1 / 0x76 | CSB=3.3V / SDO=GND で固定 |
| IR受信モジュール | IR受信 | GPIO17 / `/dev/lirc?` | overlay 設定済み |
| IR送信（2SK2232 + LED×2） | IR送信 | GPIO18 / `/dev/lirc?` | MOSFET 強化回路に移行済み |

### 追加予定

| デバイス | 種別 | インターフェース | 状態 |
|---|---|---|---|
| BH1750 | 照度センサー | I2C bus1 / 0x23 | 計画中 |
| MH-Z19E | CO2センサー | UART (GPIO14/15) | 計画中（cmdline.txt 修正が先） |
| OSI5LA5A33A-B × 2 | IR送信 LED | MOSFET 経由 | 組み込み済み |
| 2SK2232 | NchMOSFET | GPIO18 ゲート | 組み込み済み |

> 配線詳細・図解 → [`docs/wiring-diagram.md`](./wiring-diagram.md)

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
| `send_light_step` | `/config/ir/light_step.txt` | 照明切替 |
| `send_light_up` | `/config/ir/light_up.txt` | 照明を明るく |
| `send_light_down` | `/config/ir/light_down.txt` | 照明を暗く |

## 7. GPIO・ピン割り当て（概要）

> 詳細図解 → [`docs/wiring-diagram.md`](./wiring-diagram.md)

| 機能 | GPIO | 物理ピン | 状態 |
|---|---|---|---|
| I2C SDA | GPIO2 | 3番 | 稼働中（BME280 / BH1750 共用） |
| I2C SCL | GPIO3 | 5番 | 稼働中（BME280 / BH1750 共用） |
| UART TX | GPIO14 | 8番 | 計画中（MH-Z19E 用） |
| UART RX | GPIO15 | 10番 | 計画中（MH-Z19E 用） |
| IR 受信 | GPIO17 | 11番 | overlay 設定済み |
| IR 送信 | GPIO18 | 12番 | MOSFET ゲート |

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

> IRコードファイルの詳細 → [`config/ir/README.md`](../config/ir/README.md)

| ファイル | 場所 | 用途 | 状態 |
|---|---|---|---|
| `light_step.txt` | `config/ir/` | 照明切替 | 管理済み |
| `light_up.txt` | `config/ir/` | 照明アップ | 管理済み |
| `light_down.txt` | `config/ir/` | 照明ダウン | 管理済み |
| `aircon_off.txt` | 要追加 | エアコン停止 | 未整理 |
| `panasonic_test_on_27c.txt` | 要追加 | Panasonic AC テスト | 未整理 |

## 10. IR 送信回路

> 詳細図解・抵抗値計算 → [`docs/wiring-diagram.md`](./wiring-diagram.md)

2SK2232（NchMOSFET）を低側スイッチとして使い、OSI5LA5A33A-B を2個同時点灯する回路。  
LED 1本あたり 27Ω 1W を直列挿入。ゲートに 100Ω 直列＋220Ω プルダウン。

```
GPIO18 ──[100Ω]──→ 2SK2232 Gate ──[220Ω]── GND
                       Drain ──[27Ω]──→ LED1
                             ──[27Ω]──→ LED2
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
| IR 出力不足 | 現行 LED が弱い可能性 | MOSFET + 2LED 回路に更新済み |
| 照明状態ずれ | 実機フィードバックなし | 現状許容、将来検討 |
| UART 競合 | `serial0` がコンソール使用中 | MH-Z19E 追加前に `cmdline.txt` 修正 |
| MQTT 認証 | `bme280_to_mqtt.py` 内に直書き | 将来 secrets ファイル化 |
| 設定集中 | `configuration.yaml` に集中 | 将来ファイル分割を検討 |

## 13. 更新ルール

以下が変わったら必ずこのファイルを更新する:

- 物理配線・ピン割り当て（詳細は `wiring-diagram.md` も）
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

## 14. 関連ドキュメント

| ファイル | 内容 |
|---|---|
| [`docs/wiring-diagram.md`](./wiring-diagram.md) | 配線詳細・図解・ピン配置 |
| [`config/ir/README.md`](../config/ir/README.md) | IR コードファイル一覧・追加方法 |
| [`SESSION-HANDOFF.md`](../SESSION-HANDOFF.md) | 直近の作業状況・引継ぎメモ |
