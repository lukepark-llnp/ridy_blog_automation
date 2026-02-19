#!/bin/bash

# 작업 디렉토리로 이동
cd ~/agents/naverblog_automation

# 가상환경 활성화
source venv/bin/activate

echo "🚀 Bot monitoring started at $(date)"

while true; do
    echo "----------------------------------------"
    echo "🔄 Starting bot at $(date)"
    
    # 봇 실행 (로그는 bot_output.log에 누적)
    python bot.py >> bot_output.log 2>&1
    
    EXIT_CODE=$?
    echo "⚠️ Bot exited with code $EXIT_CODE at $(date)"
    
    # 잠시 대기 후 재시작 (너무 빠른 재시작 방지)
    echo "⏳ Restarting in 5 seconds..."
    sleep 5
done
