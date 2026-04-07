# IR コードファイル

このディレクトリには `ir-ctl` 形式の赤外線送信コードが入っています。

## ファイル一覧

| ファイル | 対象機器 | 動作 | 状態 |
|---|---|---|---|
| `light_step.txt` | 寝室照明 | 1段階切替（OFF→ON→NIGHT→OFF） | 使用中 |
| `light_up.txt` | 寝室照明 | 明るさアップ | 使用中 |
| `light_down.txt` | 寝室照明 | 明るさダウン | 使用中 |
| `aircon_off.txt` | エアコン | 停止 | 要追加（`~/aircon_off.txt` から移動） |
| `panasonic_test_on_27c.txt` | Panasonic AC | 27℃冷房ON テスト | 要追加（`~/panasonic_test_on_27c.txt` から移動） |

## IR コードの追加方法

```bash
# 1. ir-ctl でコードを録音
ir-ctl -d /dev/lirc1 --receive > config/ir/new_command.txt

# 2. 動作確認
ir-ctl -d /dev/lirc0 --send=config/ir/new_command.txt

# 3. コミット
git add config/ir/new_command.txt
git commit -m "ir: new_command を追加"
```

## 注意

- `/dev/lirc0` と `/dev/lirc1` の送受信割り当ては要実機確認。
- Home Assistant コンテナ内では `/config/ir/` として参照される。
