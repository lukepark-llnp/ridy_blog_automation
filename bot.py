"""Slack bot for Naver blog automation"""
import os
import re
from typing import Optional
import logging
import time
from pathlib import Path
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import settings
from watermark import batch_watermark
from content_generator import content_gen
from templates.blog_template import build_blog_html
from naver_publisher_selenium import NaverBlogPublisherSelenium as NaverBlogPublisher
from progress_tracker import ProgressTracker
from logger import PublishLogger
from image_optimizer import ImageOptimizer
from slack_forms import get_publish_form, parse_form_submission
from seo_generator import generate_seo_tags, generate_meta_description
from models_db import get_model_info, get_model_display_name
from footer_manager import get_footer_images
from structure_generator import structure_gen

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Slack app
app = App(token=settings.slack_bot_token)


def parse_message(text: str) -> Optional[dict]:
    """
    Parse Slack message for blog post data (legacy text-based input)
    """
    try:
        data = {}
        
        # Extract fields with regex
        manufacturer_match = re.search(r'제조사[:\s]+(.+)', text)
        model_match = re.search(r'모델[:\s]+(.+)', text)
        year_match = re.search(r'년식[:\s]+(.+)', text)
        color_match = re.search(r'색상[:\s]+(.+)', text)
        region_match = re.search(r'지역[:\s]+(.+)', text)
        installer_match = re.search(r'출고장착[:\s]+(.+)', text)
        
        if not all([model_match, color_match, region_match, installer_match]):
            return None
        
        # Try to match model_key from text
        model_text = model_match.group(1).strip()
        
        # Simple matching: remove spaces and check against known models
        model_key = model_text.replace(' ', '').replace('-', '')
        
        # If no match, use raw text
        if not get_model_info(model_key):
            model_key = model_text
        
        data['model_key'] = model_key
        data['manufacturer'] = manufacturer_match.group(1).strip() if manufacturer_match else ""
        data['year'] = year_match.group(1).strip() if year_match else ""
        data['color'] = color_match.group(1).strip()
        data['region'] = region_match.group(1).strip()
        data['installer'] = installer_match.group(1).strip()
        
        # Extract options
        options_match = re.search(
            r'\[?기본\s*장착\s*옵션\]?[:\s]*(.+?)(?=\[?추가|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        data['options'] = options_match.group(1).strip() if options_match else ""
        
        # Extract extra options
        extra_match = re.search(
            r'\[?추가\s*옵션\]?[:\s]*(.+?)(?=\[?특별|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        data['extra_options'] = extra_match.group(1).strip() if extra_match else ""
        
        # Extract special message
        special_match = re.search(
            r'\[?특별\s*메시지\]?[:\s]*(.+)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        data['special_message'] = special_match.group(1).strip() if special_match else ""
        
        return data
        
    except Exception as e:
        logger.error(f"Message parsing failed: {e}")
        return None


def download_images(files: list, output_dir: Path) -> list[Path]:
    """Download images from Slack"""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    
    for i, file_info in enumerate(files):
        try:
            # Get file URL
            url = file_info.get('url_private')
            if not url:
                continue
            
            # Download with Slack token auth
            import requests
            response = requests.get(
                url,
                headers={'Authorization': f'Bearer {settings.slack_bot_token}'}
            )
            response.raise_for_status()
            
            # Save file
            file_path = output_dir / f"original_{i+1:02d}.jpg"
            file_path.write_bytes(response.content)
            downloaded.append(file_path)
            logger.info(f"Downloaded: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to download image {i}: {e}")
    
    return downloaded


@app.event("message")
def handle_message(event, say, client):
    """Handle incoming messages"""
    
    logger.info(f"📩 Message event received: channel={event.get('channel')}, thread_ts={event.get('thread_ts')}, files={len(event.get('files', []))}")
    
    # Only respond to messages in configured channel
    if event.get('channel') != settings.slack_channel_id:
        logger.info(f"Ignoring message from different channel: {event.get('channel')}")
        return
    
    # Ignore bot messages
    if event.get('bot_id'):
        logger.info("Ignoring bot message")
        return
    
    # Check if this is a reply to a pending publish
    thread_ts = str(event.get('thread_ts')) if event.get('thread_ts') else None
    if thread_ts and thread_ts in pending_publishes:
        logger.info(f"Found pending publish for thread {thread_ts}")
        # Check for images
        files = event.get('files', [])
        if files:
            logger.info(f"Images found in thread: {len(files)} files")
            # Image attached! Start publishing
            pending = pending_publishes.pop(thread_ts)
            data = pending['data']
            user_id = pending['user_id']
            
            # Process publish with the form data
            process_publish(client, event, data, user_id, files)
        else:
            logger.info("No files in this message, waiting for images...")
        return
    elif thread_ts:
        # Thread exists but no pending publish found
        logger.warning(f"Thread {thread_ts} has no pending publish (bot restarted?)")
        files = event.get('files', [])
        if files:
            # User attached images to a thread with no form data
            user_id = event.get('user')
            client.chat_postMessage(
                channel=event.get('channel'),
                thread_ts=thread_ts,
                text=f"<@{user_id}> ⚠️ 봇이 재시작되어 폼 정보가 초기화되었습니다.\n\n"
                     "다시 `/출고발행` 명령어를 입력하고 폼을 제출해주세요!"
            )
        return
    
    text = event.get('text', '')
    
    # Legacy: Check for trigger command (old text-based input)
    if not text.strip().startswith('/출고발행'):
        logger.debug(f"Message ignored (no trigger command): {text[:50]}")
        return
    
    # Parse message (legacy text-based input)
    data = parse_message(text)
    if not data:
        say("❌ 메시지 형식이 올바르지 않습니다.\n\n"
            "💡 **팁:** `/출고발행` 명령어를 사용하면 편리한 폼으로 입력할 수 있습니다!")
        return
    
    # Check for attached images
    files = event.get('files', [])
    user_id = event.get('user')
    
    process_publish(client, event, data, user_id, files)


def process_publish(client, event, data: dict, user_id: str, files: list):
    """Process blog publish request"""
    channel = event.get('channel')
    thread_ts = event.get('thread_ts') or event.get('ts')
    
    # Initialize progress tracker
    progress = ProgressTracker(client, channel, thread_ts, user_id)
    progress.start()
    
    # Initialize logger
    pub_logger = PublishLogger()
    
    start_time = time.time()
    
    try:
        # Validate images
        if len(files) < 4:
            error_msg = f"이미지가 부족합니다. (현재: {len(files)}장, 최소: 4장)"
            pub_logger.start(user_id, data)
            pub_logger.log_error("validation", Exception(error_msg))
            pub_logger.finish(False)
            progress.error(error_msg, str(pub_logger.get_log_path()), notify_admin=False)
            return
        
        # Start logging
        pub_logger.start(user_id, data)
        
        # Create output directory
        output_dir = Path(settings.output_dir) / f"post_{event['ts'].replace('.', '_')}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Download images
        progress.update('download', f"{len(files)}장 다운로드 시작")
        original_images = download_images(files, output_dir / "originals")
        
        if len(original_images) < 4:
            error_msg = "이미지 다운로드 실패"
            pub_logger.log_error("download", Exception(error_msg))
            pub_logger.finish(False)
            progress.error(error_msg, str(pub_logger.get_log_path()))
            return
        
        progress.complete_step('download', f"{len(original_images)}장 완료")
        pub_logger.log_step('download', 'success', {'count': len(original_images)})
        
        # Optimize images
        progress.update('optimize', f"{len(original_images)}장 최적화 시작")
        optimizer = ImageOptimizer(max_width=1200, quality=85)
        opt_result = optimizer.batch_optimize(
            original_images,
            output_dir / "optimized"
        )
        
        progress.complete_step(
            'optimize',
            f"{opt_result['count']}장 완료 (평균 {opt_result['avg_size']}, {opt_result['total_reduction']}% 감소)"
        )
        pub_logger.log_step('optimize', 'success', opt_result)
        
        # Add watermarks
        progress.update('watermark', f"{len(opt_result['optimized_paths'])}장 워터마크 추가")
        watermarked_images = batch_watermark(
            opt_result['optimized_paths'],
            output_dir / "watermarked"
        )
        
        progress.complete_step('watermark', f"{len(watermarked_images)}장 완료")
        pub_logger.log_step('watermark', 'success', {'count': len(watermarked_images)})
        
        # --- 구조 생성 및 발행 ---
        
        # Generate content
        progress.update('content', 'LLM으로 블로그 글 생성 중')
        
        # Get model info
        model_key = data.get('model_key', data.get('model', 'UNKNOWN'))
        # model_info = get_model_info(model_key) # Used inside generators
        
        # Generate title
        title = content_gen.generate_title(data)
        
        # Generate SEO tags
        seo_tags = generate_seo_tags(data)
        
        # Get footer images
        footer_images = get_footer_images()
        
        # Prepare final images list (watermarked + emojis)
        emoji_dir = Path("assets")
        emoji_images = [
            emoji_dir / "emoji_45.png",
            emoji_dir / "emoji_46.png"
        ]
        
        # Combine: watermarked images + emojis
        # footer images are appended by publisher if passed as footer_images
        final_images = list(watermarked_images) + emoji_images
        
        # Generate Structured Elements (Directly!)
        # Pass image_count to calculate correct indices for emojis and footer
        structured_elements = structure_gen.generate_elements(data, image_count=len(watermarked_images))
        
        progress.complete_step('content', f'제목: {title}')
        progress.stats['title'] = title
        pub_logger.log_step('content', 'success', {'title': title})
        
        # Publish to Naver (자가 복구 + 재시도 로직)
        max_publish_retries = 2
        retry_delay_seconds = 300  # 5분

        # 에러 코드별 사용자 친화적 메시지 매핑
        ERROR_MESSAGES = {
            'POPUP_DURING_PUBLISH': {
                'emoji': '🔴',
                'cause': '네이버 파일 전송 오류 팝업이 발행 도중 나타남',
                'detail': '네이버 서버에서 이미지 처리 중 일시적 오류가 발생했습니다.',
                'action': '에러 팝업을 자동으로 닫고 발행을 재시도합니다.',
            },
            'PUBLISH_TIMEOUT_POPUP': {
                'emoji': '🟠',
                'cause': '에러 팝업이 발행 완료를 차단',
                'detail': '파일 전송 오류 팝업이 발행 프로세스를 막아 타임아웃이 발생했습니다.',
                'action': '팝업을 닫고 새 세션으로 발행을 재시도합니다.',
            },
            'MODAL_BLOCKED': {
                'emoji': '🟡',
                'cause': '발행 모달이 열리지 않음',
                'detail': '에러 팝업 또는 네이버 에디터 오류로 발행 창이 열리지 않았습니다.',
                'action': '에러 팝업 제거 후 발행 버튼을 다시 클릭합니다.',
            },
            'PUBLISH_TIMEOUT': {
                'emoji': '🟤',
                'cause': '발행 타임아웃 (60초 초과)',
                'detail': '발행 버튼을 클릭했으나 네이버 서버가 응답하지 않았습니다.',
                'action': '새 세션을 열어 처음부터 다시 시도합니다.',
            },
            'PUBLISH_BTN_NOT_FOUND': {
                'emoji': '⚫',
                'cause': '발행 버튼을 찾을 수 없음',
                'detail': '네이버 에디터 화면에서 발행 버튼이 사라졌습니다. 페이지 로딩 오류 가능성.',
                'action': '새 세션으로 재시도합니다.',
            },
            'MODAL_BTN_NOT_FOUND': {
                'emoji': '⚫',
                'cause': '모달 내 발행 버튼 없음',
                'detail': '발행 모달은 열렸으나 내부 버튼을 찾지 못했습니다.',
                'action': '새 세션으로 재시도합니다.',
            },
        }

        def _parse_error_code(error: Exception) -> str:
            """에러 메시지에서 에러 코드 추출"""
            msg = str(error)
            if ':' in msg:
                code = msg.split(':')[0].strip()
                if code in ERROR_MESSAGES:
                    return code
            return 'UNKNOWN'

        def _build_error_slack_msg(error: Exception, error_code: str) -> str:
            """에러 코드 기반 상세 Slack 메시지 생성"""
            info = ERROR_MESSAGES.get(error_code)
            if info:
                return (
                    f"{info['emoji']} **원인:** {info['cause']}\n"
                    f"**상세:** {info['detail']}\n"
                    f"**자동 조치:** {info['action']}"
                )
            return f"**원인:** 알 수 없는 오류\n**상세:** {str(error)[:200]}"

        for publish_attempt in range(max_publish_retries + 1):
            progress.update('publish',
                f'네이버 블로그 발행 중{f" (재시도 {publish_attempt}/{max_publish_retries})" if publish_attempt > 0 else ""}')

            try:
                publisher = NaverBlogPublisher()
                published_url = publisher.publish(
                    title=title,
                    html_content="",
                    images=final_images,
                    footer_images=footer_images,
                    data=structured_elements,
                    tags=seo_tags
                )

                # Check if draft saved (semi-auto mode)
                if published_url == "DRAFT_SAVED":
                    progress.complete_step('publish', '임시저장 완료')
                    pub_logger.log_step('publish', 'success', {'status': 'draft_saved'})

                    duration = time.time() - start_time
                    log_path = pub_logger.finish(True, {
                        'status': 'draft_saved',
                        'title': title,
                        'image_count': len(watermarked_images)
                    })

                    client.chat_postMessage(
                        channel=channel,
                        thread_ts=thread_ts,
                        text=f"<@{user_id}> **임시저장 완료!**\n\n"
                             f"**제목:** {title}\n"
                             f"**이미지:** {len(watermarked_images) + len(footer_images)}장\n\n"
                             f"네이버 블로그에서 발행해주세요:\n"
                             f"https://blog.naver.com/ridyservice\n\n"
                             f"소요시간: {duration:.1f}초"
                    )
                else:
                    # 발행 성공
                    progress.complete_step('publish', f'URL: {published_url}')
                    pub_logger.log_step('publish', 'success', {'url': published_url, 'retries': publish_attempt})

                    duration = time.time() - start_time
                    log_path = pub_logger.finish(True, {
                        'url': published_url,
                        'title': title,
                        'image_count': len(watermarked_images)
                    })

                    if publish_attempt > 0:
                        # 재시도 후 성공 알림
                        client.chat_postMessage(
                            channel=channel,
                            thread_ts=thread_ts,
                            text=f"<@{user_id}> **재시도 발행 성공!** (재시도 {publish_attempt}회 후 성공)\n\n"
                                 f"**제목:** {title}\n"
                                 f"**URL:** {published_url}\n"
                                 f"소요시간: {duration:.1f}초\n\n"
                                 f"자가 복구가 정상 작동했습니다."
                        )

                    progress.finish(published_url, duration, str(log_path))

                break  # 성공 시 루프 탈출

            except Exception as pub_error:
                logger.error(f"Publishing failed (attempt {publish_attempt+1}): {pub_error}", exc_info=True)

                error_code = _parse_error_code(pub_error)
                error_detail = _build_error_slack_msg(pub_error, error_code)

                # 로그인 에러는 재시도 불가
                error_str = str(pub_error).lower()
                is_login_error = any(keyword in error_str for keyword in [
                    'login', 'nid.naver.com', 'authentication', '로그인'
                ])

                if is_login_error:
                    pub_logger.log_error('publish', pub_error)
                    log_path = pub_logger.finish(False)
                    error_msg = (
                        f"<@{user_id}> **네이버 로그인 필요**\n\n"
                        f"**문제:** 자동 로그인 실패 (세션 만료)\n"
                        f"**에러 코드:** LOGIN_EXPIRED\n\n"
                        f"**수동 조치 필요:**\n"
                        f"1. 터미널에서 실행:\n"
                        f"```\n"
                        f"cd ~/Ridy/naver_blog_automation\n"
                        f"source venv/bin/activate\n"
                        f"python manual_login.py\n"
                        f"```\n"
                        f"2. 크롬 창에서 네이버 로그인\n"
                        f"3. 완료 후 다시 `/출고발행` 시도\n\n"
                        f"이 오류는 자동 재시도가 불가합니다."
                    )
                    progress.error(error_msg, str(log_path))
                    break

                # 재시도 가능한 에러 (파일 전송, 타임아웃 등)
                if publish_attempt < max_publish_retries:
                    retry_min = retry_delay_seconds // 60
                    remaining = max_publish_retries - publish_attempt

                    # 상세 Slack 경고 알림
                    client.chat_postMessage(
                        channel=channel,
                        thread_ts=thread_ts,
                        text=(
                            f"<@{user_id}> **발행 실패 - 자동 재시도 예정**\n\n"
                            f"**에러 코드:** `{error_code}`\n"
                            f"{error_detail}\n\n"
                            f"**현재 상태:**\n"
                            f"- 시도: {publish_attempt + 1}회 / 최대 {max_publish_retries + 1}회\n"
                            f"- 남은 재시도: {remaining}회\n"
                            f"- 대기 시간: {retry_min}분\n\n"
                            f"**{retry_min}분 후 새 세션으로 자동 재시도합니다.**\n"
                            f"글 작성은 완료된 상태이며, 발행 단계만 다시 시도합니다."
                        )
                    )
                    logger.info(f"Waiting {retry_delay_seconds}s before retry {publish_attempt+1}...")
                    time.sleep(retry_delay_seconds)
                else:
                    # 모든 재시도 실패
                    pub_logger.log_error('publish', pub_error)
                    log_path = pub_logger.finish(False)
                    error_msg = (
                        f"<@{user_id}> **발행 최종 실패**\n\n"
                        f"**에러 코드:** `{error_code}`\n"
                        f"{error_detail}\n\n"
                        f"**시도 내역:**\n"
                        f"- 발행 단계 내부 자동 복구: 2회 시도\n"
                        f"- 새 세션 재시도: {max_publish_retries}회 시도 (각 {retry_delay_seconds // 60}분 간격)\n"
                        f"- 결과: 모두 실패\n\n"
                        f"**수동 조치 필요:**\n"
                        f"1. 네이버 블로그 에디터에서 임시저장 글 확인\n"
                        f"2. 수동으로 발행하거나 `/출고발행`으로 재시도\n\n"
                        f"네이버 서버 장애가 지속되고 있을 수 있습니다."
                    )
                    progress.error(error_msg, str(log_path))
        
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        
        # Log error
        if 'pub_logger' in locals():
            pub_logger.log_error('unknown', e)
            log_path = pub_logger.finish(False)
        else:
            log_path = "N/A"
        
        # Send error message
        if 'progress' in locals():
            progress.error(f"처리 중 오류 발생\n\n{str(e)}", log_path)


@app.command("/출고발행")
def handle_command(ack, command, client):
    """Handle slash command - show modal form"""
    ack()
    
    try:
        # Open modal form
        client.views_open(
            trigger_id=command['trigger_id'],
            view=get_publish_form()
        )
    except Exception as e:
        logger.error(f"Failed to open modal: {e}")
        client.chat_postMessage(
            channel=command['channel_id'],
            text=f"❌ 폼을 열 수 없습니다: {str(e)}"
        )


@app.view("publish_form")
def handle_form_submission(ack, body, client, view):
    """Handle modal form submission"""
    ack()
    
    try:
        # Parse form data
        values = view['state']['values']
        data = parse_form_submission(values)
        
        # Get user and channel info
        user_id = body['user']['id']
        channel_id = settings.slack_channel_id
        
        # Get model display name
        model_display = get_model_display_name(data['model_key'])
        
        # Send confirmation and ask for images
        response = client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}> 정보가 저장되었습니다! ✅\n\n"
                 f"**모델:** {model_display}\n"
                 f"**년식:** {data['year']}\n"
                 f"**색상:** {data['color']}\n"
                 f"**지역:** {data['region']}\n\n"
                 f"📷 **이제 출고 사진을 이 쓰레드에 첨부해주세요** (최소 4장, 권장 14장)\n"
                 f"이미지 첨부가 완료되면 자동으로 발행이 시작됩니다."
        )
        
        # Store data temporarily (use thread_ts as key)
        # In production, use Redis or database
        # For now, we'll use a simple in-memory dict
        thread_ts = str(response['ts'])  # Ensure string type
        pending_publishes[thread_ts] = {
            'data': data,
            'user_id': user_id,
            'channel_id': channel_id,
            'waiting_for_images': True
        }
        
        logger.info(f"Form submitted by {user_id}, waiting for images in thread {thread_ts}")
        logger.info(f"DEBUG: Stored in pending_publishes with key type={type(thread_ts)}, value={thread_ts}")
        
    except Exception as e:
        logger.error(f"Form submission failed: {e}", exc_info=True)
        client.chat_postMessage(
            channel=settings.slack_channel_id,
            text=f"❌ 폼 제출 실패: {str(e)}"
        )


# In-memory storage for pending publishes
# TODO: Replace with Redis/DB in production
pending_publishes = {}


def main():
    """Start bot"""
    logger.info("🤖 Naver Blog Automation Bot starting...")
    logger.info(f"Listening on channel: {settings.slack_channel_id}")
    
    # Start socket mode handler
    handler = SocketModeHandler(app, settings.slack_app_token)
    handler.start()


if __name__ == "__main__":
    main()
