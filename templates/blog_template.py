"""HTML blog template builder"""


def build_blog_html(data: dict, images: list[str]) -> str:
    """
    Build Naver blog HTML from data and watermarked images
    
    Args:
        data: {
            'title': str,
            'greeting_intro': str,
            'model': str (display name),
            'manufacturer': str,
            'year': str,
            'color': str,
            'region': str,
            'installer': str,
            'thank_you': str,
            'options': str,
            'extra_options': str,
            'special_message': str,
            'tags': list[str],
            'meta_description': str
        }
        images: List of watermarked image file paths (14장 예상)
    
    Returns:
        HTML string
    """
    
    # Split images into groups (based on reference layout)
    # Group 1: 4 images (2x2)
    # Group 2: 6 images (2x3) 
    # Group 3: 4 images (2x2)
    
    img_group1 = images[:4] if len(images) >= 4 else images
    img_group2 = images[4:10] if len(images) >= 10 else []
    img_group3 = images[10:14] if len(images) >= 14 else []
    
    # Helper to create image grid HTML
    def image_grid(imgs: list[str], cols: int = 2) -> str:
        html = '<div style="display: grid; grid-template-columns: repeat({}, 1fr); gap: 10px; margin: 20px 0;">'.format(cols)
        for img in imgs:
            html += f'<img src="{img}" style="width: 100%; height: auto;" />'
        html += '</div>'
        return html
    
    # Build HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: "Apple SD Gothic Neo", "맑은 고딕", sans-serif;
            max-width: 680px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.8;
        }}
        .section {{
            margin: 30px 0;
        }}
        .char-emoji {{
            text-align: center;
            font-size: 80px;
            margin: 20px 0;
        }}
        .divider {{
            border-bottom: 1px solid #ddd;
            margin: 30px 0;
        }}
        .info-list {{
            list-style: none;
            padding: 0;
            margin: 20px 0;
        }}
        .info-list li {{
            margin: 8px 0;
            padding-left: 20px;
        }}
        .info-list li:before {{
            content: "·";
            margin-right: 10px;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
        }}
        .footer-links {{
            margin: 20px 0;
        }}
        .footer-links a {{
            display: block;
            margin: 10px 0;
            color: #4a90e2;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <!-- Greeting -->
    <div class="section">
        <div class="char-emoji">🐶</div>
        <p>{data['greeting_intro']}</p>
    </div>

    <!-- Image Group 1 (4 images) -->
    {image_grid(img_group1)}

    <div class="divider"></div>

    <!-- Vehicle Info -->
    <div class="section">
        <ul class="info-list">
            <li>제조사 : {data.get('manufacturer', 'UNKNOWN')}</li>
            <li>모델명 : {data['model']}</li>
            <li>년식 : {data.get('year', 'N/A')}</li>
            <li>색상 : {data['color']}</li>
            <li>출고 장착 : {data['installer']}</li>
            <li>출고 지역 : {data['region']}</li>
        </ul>
    </div>

    <div class="divider"></div>

    <!-- Thank You -->
    <div class="section" style="text-align: center;">
        <p>{data['thank_you']}</p>
        <div class="char-emoji" style="font-size: 60px;">🐶❤️</div>
    </div>

    <!-- Image Group 2 (6 images) -->
    {image_grid(img_group2)}

    <div class="divider"></div>

    <!-- Options -->
    <div class="section">
        <ul class="info-list">
            {_format_options(data['options'])}
        </ul>
    </div>

    <div class="divider"></div>

    <!-- Extra Options Message -->
    <div class="section" style="text-align: center;">
        <p>{data.get('extra_options', '')}</p>
    </div>

    <div class="divider"></div>

    <!-- Special Message (if exists) -->
    {"<div class='section' style='text-align: center; background: #f0f8ff; padding: 20px; border-radius: 10px;'><p style='font-size: 18px; font-weight: bold;'>" + data.get('special_message', '') + "</p></div><div class='divider'></div>" if data.get('special_message') else ""}

    <!-- Image Group 3 (4 images) -->
    {image_grid(img_group3)}

    <!-- Footer: Fixed Images (고객혜택 정리) -->
    <div class="section">
        <!-- 고객 혜택 정리 이미지 -->
        <img src="{{FOOTER_IMAGE_1}}" style="width: 100%; margin: 10px 0;" alt="RIDY 고객 혜택 정리" />
        
        <!-- 책임보험/종합보험 비교표 -->
        <img src="{{FOOTER_IMAGE_2}}" style="width: 100%; margin: 10px 0;" alt="보험 비교표" />
    </div>

    <!-- RIDY Logo -->
    <div class="footer">
        <img src="https://via.placeholder.com/400x100?text=RIDY+RENTAL+LOGO" style="width: 400px; max-width: 100%;" />
    </div>

    <!-- Contact Info -->
    <div class="footer">
        <p><strong>문의</strong></p>
        <p>번호: {data.get('phone', '1555-6595')}</p>
        <div class="footer-links">
            <a href="https://pf.kakao.com/_xgxoxexen/chat">카카오톡 채널</a>
            <a href="https://www.ridy.co.kr/">RIDY 바로 가기</a>
            <a href="https://www.ridy.co.kr/service/payout">PAYOUT 바로 가기</a>
            <a href="https://tally.so/r/mYLXOd">서비스센터 가입 문의</a>
        </div>
    </div>

    <!-- Tags -->
    <div class="footer" style="color: #666; font-size: 14px; margin-top: 30px;">
        <p>{' '.join(data.get('tags', []))}</p>
    </div>
</body>
</html>
"""
    
    return html


def _format_options(options_text: str) -> str:
    """Convert options text to HTML list items"""
    lines = [line.strip() for line in options_text.split('\n') if line.strip()]
    items = []
    
    for line in lines:
        # Remove leading dashes/bullets
        line = line.lstrip('- •·')
        if line:
            items.append(f"<li>{line}</li>")
    
    return '\n'.join(items)
