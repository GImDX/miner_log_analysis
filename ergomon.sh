#!/bin/bash

# === 获取当前脚本所在目录 ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# === 可配置参数 ===
ADDRESS="9i9m9AxmqgBUBD6GfYJQHZiHQ5d6AP7Ak3QVFfKiNtopQnMZkmG"
PROXY="127.0.0.1:7890"
LOG_FILE="${SCRIPT_DIR}/ergo_${ADDRESS}.log"
URL="https://ergo.herominers.com/api/stats_address?address=${ADDRESS}"

# === 如果日志文件不存在则创建 ===
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# === 获取 JSON 并解析 unlocked 部分 ===
response=$(curl -s --proxy "$PROXY" "$URL")
entries=$(echo "$response" | jq -r '.unlocked[]' 2>/dev/null)

# === 遍历 unlocked 条目 ===
while IFS= read -r entry; do
    if [[ "$entry" == *:* ]]; then
        fields=($(echo "$entry" | tr ':' '\n'))
        if [[ ${#fields[@]} -eq 14 ]]; then
            if ! grep -qF "$entry" "$LOG_FILE"; then
                numerator=${fields[6]}
                denominator=${fields[2]}
                if [[ "$denominator" -ne 0 ]]; then
                    raw_luck=$(echo "scale=10; $numerator / $denominator * 100" | bc)
                    luck=$(printf "%.2f" "$raw_luck")
                    echo "\"$entry\", luck = $luck" >> "$LOG_FILE"
                fi
            fi
        fi
    fi
done <<< "$entries"
