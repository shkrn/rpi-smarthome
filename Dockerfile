# 公式のHome Assistantをベースにする
FROM ghcr.io/home-assistant/home-assistant:stable

# 赤外線ツールを永続的にインストールする
RUN apk add --no-cache v4l-utils