#!/usr/bin/env python3
"""수동 로그인 전용 스크립트"""
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def manual_login():
    """네이버 수동 로그인 및 쿠키 저장"""
    
    logger.info("🔐 네이버 수동 로그인 시작...")
    logger.info("=" * 60)
    
    # 크롬 옵션
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # 영구 프로필 사용
    profile_dir = Path.home() / "agents/naverblog_automation/chrome_data"
    profile_dir.mkdir(parents=True, exist_ok=True)
    options.add_argument(f"user-data-dir={profile_dir}")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 네이버 접속
        logger.info("📍 네이버 접속 중...")
        driver.get("https://naver.com")
        time.sleep(2)
        
        # 로그인 확인
        if "nid.naver.com" in driver.current_url:
            logger.info("=" * 60)
            logger.info("👉 로그인이 필요합니다.")
            logger.info("👉 열린 크롬 창에서 네이버 로그인을 완료해주세요.")
            logger.info("=" * 60)
            
            # 로그인 대기 (최대 5분)
            max_wait = 300
            waited = 0
            
            while waited < max_wait:
                if "nid.naver.com" not in driver.current_url:
                    logger.info("✅ 로그인 성공!")
                    break
                
                if waited % 10 == 0:
                    logger.info(f"⏳ 로그인 대기 중... ({waited}/{max_wait}초)")
                
                time.sleep(1)
                waited += 1
            
            if waited >= max_wait:
                logger.error("❌ 타임아웃: 5분 내에 로그인을 완료해주세요.")
                sys.exit(1)
        else:
            logger.info("✅ 이미 로그인되어 있습니다.")
        
        # 쿠키 저장
        logger.info("💾 쿠키 저장 중...")
        cookies = driver.get_cookies()
        
        cookie_path = Path.home() / "agents/naverblog_automation/naver_cookies.json"
        import json
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2)
        
        logger.info(f"✅ {len(cookies)}개 쿠키 저장 완료: {cookie_path}")
        
        # 테스트: 블로그 접속
        logger.info("🧪 블로그 접속 테스트 중...")
        driver.get("https://blog.naver.com/ridyservice")
        time.sleep(2)
        
        if "nid.naver.com" not in driver.current_url:
            logger.info("✅ 블로그 접속 성공! 로그인 상태 확인됨.")
        else:
            logger.warning("⚠️ 블로그 접속 시 로그인 필요. 쿠키를 확인하세요.")
        
        logger.info("=" * 60)
        logger.info("🎉 설정 완료!")
        logger.info("이제 `/출고발행` 명령어를 사용할 수 있습니다.")
        logger.info("=" * 60)
        
        input("\n👉 Enter 키를 눌러 종료하세요...")
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        sys.exit(1)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    manual_login()
