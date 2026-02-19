"""
Retry Last Failed Publish
"""
import logging
import sys
import glob
from pathlib import Path
from naver_publisher_selenium import NaverBlogPublisherSelenium as NaverBlogPublisher
from structure_generator import structure_gen
from content_generator import content_gen
from seo_generator import generate_seo_tags
from footer_manager import get_footer_images
from config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def retry_publish():
    # 1. 데이터 (2026-02-11 17:30 로그에서 추출)
    data = {
        "model_key": "NMAX125",
        "acquisition_type": "인수형",
        "year": "2025",
        "color": "아이콘 블랙",
        "region": "서울 중구",
        "options": "85L 탑박스\n리다이\n1구 핸드폰 거치대",
        "extra_options": "사이드 브레이크\n열선\n크로스바",
        "special_message": "눈 비 조심"
    }
    
    logger.info(f"🔄 Retrying publish for: {data['model_key']} {data['region']}")
    
    # 2. 이미지 경로 (로그 기반)
    base_dir = Path("output/post_1770798611_119229")
    
    # 워터마크 이미지 사용
    watermark_dir = base_dir / "watermarked"
    
    if not watermark_dir.exists():
        watermark_dir = base_dir / "optimized"
        logger.warning(f"Watermark dir not found, using optimized: {watermark_dir}")
        
    if not watermark_dir.exists():
        logger.error(f"❌ Image directory not found: {base_dir}")
        return

    # 이미지 리스트 가져오기
    image_paths = sorted(list(watermark_dir.glob("*.jpg")))
    logger.info(f"Found {len(image_paths)} images")
    
    if not image_paths:
        logger.error("❌ No images found!")
        return

    # 3. 이모지 및 푸터 준비
    emoji_dir = Path("assets")
    emoji_images = [
        emoji_dir / "emoji_45.png",
        emoji_dir / "emoji_46.png"
    ]
    
    footer_images = get_footer_images()
    
    # Final images list
    final_images = list(image_paths) + emoji_images
    
    # 4. 구조 생성
    logger.info("Generating structure...")
    try:
        # image_count 전달!
        structured_elements = structure_gen.generate_elements(data, image_count=len(image_paths))
        logger.info("✅ Structure generated with dynamic indices")
    except TypeError:
        logger.error("❌ structure_generator.py error!")
        return
        
    # 5. 제목 및 태그 생성
    title = content_gen.generate_title(data)
    seo_tags = generate_seo_tags(data)
    
    logger.info(f"Title: {title}")
    logger.info(f"Tags: {seo_tags[:5]}...")
    
    # 6. 발행 시작
    logger.info("🚀 Starting publisher...")
    publisher = NaverBlogPublisher()
    
    try:
        url = publisher.publish(
            title=title,
            html_content="",
            images=final_images,
            footer_images=footer_images,
            data=structured_elements,
            tags=seo_tags
        )
        logger.info(f"✅ Published successfully: {url}")
    except Exception as e:
        logger.error(f"❌ Publish failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    retry_publish()
