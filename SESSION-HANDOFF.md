# SESSION-HANDOFF

> このファイルは「次のAIセッションに渡す短い引継ぎメモ」です。  
> 作業が進むたびに内容を書き換えてください。詳細は `docs/system-spec.md` を参照してください。

## 最終更新

2026-04-07

## 現在の状態（10行サマリー）

1. Raspberry Pi 3 Model B / Raspberry Pi OS でシステム稼働中
2. Home Assistant と Mosquitto が Docker Compose で動いている
3. BME280 は I2C bus1 / 0x76 でホスト Python が読み、MQTT `home/bme280` に publish 済み
4. HA の照明制御は `light.template` + `input_select.light_mode` + `input_number.light_brightness` で構成済み
5. IR 送信は `ir-ctl -d /dev/lirc0 --send=/config/light_*.txt` で動作、ただし実機での動作確認が未完了
6. `/dev/lirc0` と `/dev/lirc1` の送受信役割が未確定（要 `--features` で確認）
7. IRコードは `light_step.txt`、`light_up.txt`、`light_down.txt` が `config/` 配下に存在確認済み
8. `aircon_off.txt` と `panasonic_test_on_27c.txt` はホームディレクトリ直下にあり、まだリポジトリ未整理
9. BH1750・MH-Z19E・IR LED 強化（OSI5LA5A33A-B x2 + 2SK2232）は計画中・未着手
10. MH-Z19E 追加前に `cmdline.txt` の serial console 設定を変更する必要がある

## 次にやること（優先順）

- [ ] `ir-ctl --features -d /dev/lirc0` と `lirc1` で送受信の役割を確認する
- [ ] 実際に IR 送信が照明に届くか実機テストする
- [ ] `aircon_off.txt` と `panasonic_test_on_27c.txt` を `config/` 配下に移しコミットする
- [ ] BH1750 を I2C に接続し `i2cdetect -y 1` で認識確認する
- [ ] BH1750 の Python+MQTT パブリッシャーを作成する
- [ ] `cmdline.txt` の `console=serial0,115200` を削除し MH-Z19E 用に serial0 を解放する
- [ ] IR 送信回路を OSI5LA5A33A-B x2 + 2SK2232 構成に組み替える

## 既知の問題・リスク

| 問題 | 状況 |
|---|---|
| IR が届かない可能性 | LED 出力が弱い可能性あり、回路要見直し |
| lirc デバイスの役割不明 | `lirc0`=TX か RX か未確認 |
| 照明状態がずれる可能性 | helper 推定のため、実機操作で状態ずれが発生しうる |
| serial console 競合 | MH-Z19E 追加前に `cmdline.txt` 変更が必要 |
| MQTT 認証の直書き | `bme280_to_mqtt.py` 内に認証情報あり |

## AIに渡すときのコンテキスト手順

1. このファイルを最初に読ませる
2. `docs/system-spec.md` を読ませる
3. 関係するファイル（`config/configuration.yaml` など）を必要に応じて見せる
4. 「現在やろうとしていること」を一言添える
