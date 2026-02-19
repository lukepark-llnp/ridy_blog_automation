"""Real-time progress tracking for Slack"""
import logging
from typing import Optional
from slack_sdk import WebClient

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track and update progress in Slack thread"""
    
    STEPS = {
        'download': '📥 이미지 다운로드 중...',
        'optimize': '🖼️ 이미지 최적화 중...',
        'watermark': '💧 워터마크 추가 중...',
        'content': '✍️ 블로그 글 생성 중...',
        'publish': '🌐 네이버 블로그 발행 중...',
    }
    
    def __init__(self, client: WebClient, channel: str, thread_ts: str, user_id: str):
        """
        Args:
            client: Slack WebClient
            channel: Channel ID
            thread_ts: Thread timestamp (for replies)
            user_id: User who triggered the action (for mention)
        """
        self.client = client
        self.channel = channel
        self.thread_ts = thread_ts
        self.user_id = user_id
        self.message_ts = None  # Track the progress message
        self.current_step = None
        self.stats = {}
    
    def start(self):
        """Send initial message"""
        response = self.client.chat_postMessage(
            channel=self.channel,
            thread_ts=self.thread_ts,
            text=f"<@{self.user_id}> 출고 발행을 시작합니다! 📝"
        )
        self.message_ts = response['ts']
    
    def update(self, step: str, details: str = ""):
        """Update progress"""
        if step not in self.STEPS:
            logger.warning(f"Unknown step: {step}")
            return
        
        self.current_step = step
        status_text = self.STEPS[step]
        
        if details:
            status_text += f"\n  └─ {details}"
        
        # Build full status message
        message_lines = [f"<@{self.user_id}> 출고 발행 진행중..."]
        
        for s, label in self.STEPS.items():
            if s in self.stats:
                # Completed step
                message_lines.append(f"✅ {label.replace('중...', '완료!')}")
                if self.stats[s]:
                    message_lines.append(f"   └─ {self.stats[s]}")
            elif s == step:
                # Current step
                message_lines.append(f"⏳ {label}")
                if details:
                    message_lines.append(f"   └─ {details}")
            else:
                # Future step
                message_lines.append(f"⚪ {label.replace('중...', '')}")
        
        # Update message
        try:
            self.client.chat_update(
                channel=self.channel,
                ts=self.message_ts,
                text="\n".join(message_lines)
            )
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
    
    def complete_step(self, step: str, details: str = ""):
        """Mark step as completed"""
        self.stats[step] = details
        self.update(step, details)
    
    def finish(self, url: str, duration: float, log_path: str):
        """Send completion message"""
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        time_str = f"{minutes}분 {seconds}초" if minutes > 0 else f"{seconds}초"
        
        message = f"""
🎉 <@{self.user_id}> 출고 발행이 완료되었습니다!

📝 **제목:** {self.stats.get('title', 'N/A')}
🔗 **URL:** {url}
⏱️ **소요시간:** {time_str}
📊 **로그:** `{log_path}`
"""
        
        self.client.chat_postMessage(
            channel=self.channel,
            thread_ts=self.thread_ts,
            text=message.strip()
        )
    
    def error(self, error_msg: str, log_path: str, notify_admin: bool = True):
        """Send error message"""
        admin_mention = "\n\n⚠️ <@Luke> 확인이 필요합니다." if notify_admin else ""
        
        message = f"""
❌ <@{self.user_id}> 발행 중 오류가 발생했습니다.

🔍 **오류 내용:**
{error_msg}

📊 **로그:** `{log_path}`{admin_mention}
"""
        
        self.client.chat_postMessage(
            channel=self.channel,
            thread_ts=self.thread_ts,
            text=message.strip()
        )
