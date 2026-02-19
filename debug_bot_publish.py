"""Debug script to verify bot's structure generation and publishing"""
import logging
import sys
from pathlib import Path
from structure_generator import structure_gen
from naver_publisher_selenium import NaverBlogPublisherSelenium as NaverBlogPublisher

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample data (simulating Slack form input)
SAMPLE_DATA = {
    'model_key': 'X-ADV750',
    'year': '2025',
    'color': '펄 화이트',
    'region': '서울 강남구',
    'acquisition_type': '인수형',
    'options': '85L 알루미늄 탑박스\n탑박스 받침(리다이)\n핸드폰 거치대',
    'extra_options': '스크린(롱 스크린, 미들 스크린)\n사이드 스탠드(말발굽)\n크로스 바(봉지 걸이 및 멀티바)',
    'special_message': '발렌타인 데이'
}

# Sample images (using existing test images)
TEST_IMAGES_DIR = Path("output/test_complete_1770213639/watermarked")
IMAGES = sorted(list(TEST_IMAGES_DIR.glob("*.jpg")))[:8] # 8 images needed
FOOTER_IMAGES = [
    Path("assets/footer/benefits.png"),
    Path("assets/footer/insurance_comparison.png")
]

def debug_publish():
    print("🧪 Debugging Bot Publish Flow")
    print("============================================================")
    
    # 1. Generate Structure
    print("📋 Generating structure...")
    elements = structure_gen.generate_elements(SAMPLE_DATA)
    
    print(f"  ✅ Generated {len(elements)} elements")
    for i, elem in enumerate(elements):
        print(f"    [{i+1}] {elem['type']}: {str(elem.get('content', ''))[:30]}...")
        
    # 2. Publish
    print("\n🚀 Starting Publisher...")
    publisher = NaverBlogPublisher()
    
    # Login check removed - publish() handles it
    # publisher.login_with_clipboard() 
    
    url = publisher.publish(
        title="[DEBUG] 서울 강남구 X-ADV750 2025년식 출고 (발렌타인 에디션)",
        html_content="",
        images=IMAGES,
        footer_images=FOOTER_IMAGES,
        data=elements,
        tags=["#RIDY", "#XADV750", "#배달대행", "#오토바이리스", "#강남배달"]
    )
    
    print(f"\n✅ Publish Result: {url}")

if __name__ == "__main__":
    try:
        debug_publish()
    except Exception as e:
        logger.exception("❌ Debug failed")
