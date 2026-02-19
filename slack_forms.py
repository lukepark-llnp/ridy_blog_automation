"""Slack modal forms for structured input"""
from models_db import MODEL_DROPDOWN_OPTIONS


def get_publish_form():
    """
    Build Slack modal form for blog publish
    
    Returns:
        dict: Slack modal view payload
    """
    return {
        "type": "modal",
        "callback_id": "publish_form",
        "title": {
            "type": "plain_text",
            "text": "📝 출고 발행"
        },
        "submit": {
            "type": "plain_text",
            "text": "제출"
        },
        "close": {
            "type": "plain_text",
            "text": "취소"
        },
        "blocks": [
            {
                "type": "input",
                "block_id": "model",
                "label": {
                    "type": "plain_text",
                    "text": "모델 선택 *"
                },
                "element": {
                    "type": "static_select",
                    "action_id": "model_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "모델 선택"
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": opt["display"]},
                            "value": opt["key"]
                        }
                        for opt in MODEL_DROPDOWN_OPTIONS
                    ] + [
                        {
                            "text": {"type": "plain_text", "text": "🔧 기타 (직접 입력)"},
                            "value": "OTHER"
                        }
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "model_custom",
                "label": {
                    "type": "plain_text",
                    "text": "기타 모델명 (위에서 '기타' 선택 시)"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "model_custom_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "예: X-ADV750, GSX-R1000"
                    }
                },
                "optional": True
            },
            {
                "type": "input",
                "block_id": "acquisition",
                "label": {
                    "type": "plain_text",
                    "text": "상품 유형 *"
                },
                "element": {
                    "type": "static_select",
                    "action_id": "acquisition_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "유형 선택"
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "인수형"},
                            "value": "인수형"
                        },
                        {
                            "text": {"type": "plain_text", "text": "반납형"},
                            "value": "반납형"
                        }
                    ],
                    "initial_option": {
                        "text": {"type": "plain_text", "text": "인수형"},
                        "value": "인수형"
                    }
                }
            },
            {
                "type": "input",
                "block_id": "year",
                "label": {
                    "type": "plain_text",
                    "text": "년식 *"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "year_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "예: 2025"
                    }
                }
            },
            {
                "type": "input",
                "block_id": "color",
                "label": {
                    "type": "plain_text",
                    "text": "색상 *"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "color_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "예: 펄 화이트, 매트 블랙"
                    }
                }
            },
            {
                "type": "input",
                "block_id": "region",
                "label": {
                    "type": "plain_text",
                    "text": "출고 지역 *"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "region_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "예: 서울 강남구"
                    }
                }
            },
            {
                "type": "input",
                "block_id": "options",
                "label": {
                    "type": "plain_text",
                    "text": "기본 장착 옵션"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "options_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "예:\n- 스크린(폭 스크린, 미들 스크린)\n- 사이드 스탠드(발판형)\n- 그로스 비"
                    }
                },
                "optional": True
            },
            {
                "type": "input",
                "block_id": "extra_options",
                "label": {
                    "type": "plain_text",
                    "text": "추가 장착 옵션"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "extra_options_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "예: 등등 추가로 원하시는 옵션이 있으면 문의!"
                    }
                },
                "optional": True
            },
            {
                "type": "input",
                "block_id": "special_message",
                "label": {
                    "type": "plain_text",
                    "text": "특별 메시지 (키워드 입력 시 LLM 자동 작문)"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "special_message_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "예: 발렌타인 데이, 설날, 장마철 안전운전"
                    }
                },
                "optional": True
            }
        ]
    }


def parse_form_submission(values: dict) -> dict:
    """
    Parse modal form submission
    
    Args:
        values: Slack view['state']['values']
        
    Returns:
        dict: Parsed data
    """
    # Get model selection
    model_key = values['model']['model_select']['selected_option']['value']
    
    # If "OTHER", use custom input
    if model_key == "OTHER":
        model_key = values['model_custom']['model_custom_input'].get('value', 'UNKNOWN')
    
    return {
        'model_key': model_key,
        'acquisition_type': values['acquisition']['acquisition_select']['selected_option']['value'],
        'year': values['year']['year_input']['value'],
        'color': values['color']['color_input']['value'],
        'region': values['region']['region_input']['value'],
        'options': values['options']['options_input'].get('value', ''),
        'extra_options': values['extra_options']['extra_options_input'].get('value', ''),
        'special_message': values['special_message']['special_message_input'].get('value', '')
    }
