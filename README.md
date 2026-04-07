# rpi-smarthome

Raspberry Pi 3 Model B 上で動作するスマートホームノード。  
Home Assistant (Docker) を中心に、赤外線リモコン送受信・環境センサー取得・MQTT連携を統合する。

## システム概要

| 項目 | 内容 |
|---|---|
| ホスト | Raspberry Pi 3 Model B / Raspberry Pi OS |
| Home Assistant | Docker コンテナ（ローカルビルド） |
| MQTT ブローカー | Mosquitto（Docker コンテナ） |
| センサー | BME280（I2C）、BH1750（追加予定）、MH-Z19E（追加予定） |
| IR 送受信 | GPIO17=受信、GPIO18=送信、`ir-ctl` 使用 |

## ディレクトリ構成

```
rpi-smarthome/
├── README.md                  # このファイル
├── SESSION-HANDOFF.md         # 次回AIセッション向け引継ぎメモ（頻繁に更新）
├── Dockerfile                 # HA コンテナのローカルビルド定義
├── docker-compose.yml         # HA + Mosquitto の構成
├── config/                    # Home Assistant 設定（コンテナ内 /config にマウント）
│   ├── configuration.yaml
│   ├── automations.yaml
│   ├── scenes.yaml
│   ├── scripts.yaml
│   ├── light_step.txt         # 照明切替 IR コード
│   ├── light_up.txt           # 照明アップ IR コード
│   ├── light_down.txt         # 照明ダウン IR コード
│   └── blueprints/
├── bme280-publisher/          # BME280 → MQTT publish スクリプト
│   └── bme280_to_mqtt.py
├── mosquitto/                 # Mosquitto 設定
└── docs/
    ├── system-spec.md         # システム詳細仕様書（正式版）
    └── decisions/             # 設計判断の記録
```

## 起動方法

```bash
cd ~/rpi-smarthome   # またはリポジトリのルート
docker compose up -d
```

BME280 パブリッシャーは systemd サービスで自動起動する:

```bash
sudo systemctl status bme280-mqtt.service
```

## IR 送信テスト

```bash
# どちらが TX か確認
ir-ctl --features -d /dev/lirc0
ir-ctl --features -d /dev/lirc1

# 照明の IR 送信テスト
ir-ctl -d /dev/lirc0 --send=config/light_step.txt
```

## 追加予定の対応状況

| 部品 | 状態 | 備考 |
|---|---|---|
| BH1750 | 計画中 | I2C バス1、Python+MQTT 方式 |
| MH-Z19E | 計画中 | UART、serial console 整理が先 |
| OSI5LA5A33A-B x2 | 計画中 | IR 送信出力強化 |
| 2SK2232 | 計画中 | IR LED 駆動 MOSFET |

## 関連ドキュメント

- [システム仕様書](docs/system-spec.md) — 現在の確定事項・設計方針・リスク一覧
- [引継ぎメモ](SESSION-HANDOFF.md) — 今このシステムがどういう状態かの短いまとめ

## 注意事項

- `config/.storage/` は `.gitignore` 対象。HA の実行時状態ファイルは管理しない。
- MQTT 認証情報はスクリプト内に直書きされているため、将来的に secrets 化を検討する。
- `/dev/lirc0` と `/dev/lirc1` の送受信の役割は実機で要確認。
