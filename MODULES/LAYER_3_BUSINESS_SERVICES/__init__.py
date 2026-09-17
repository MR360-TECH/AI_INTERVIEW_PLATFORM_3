# LAYER 3: BUSINESS SERVICES
from MODULES.LAYER_3_BUSINESS_SERVICES.ai_client import get_ai_client, analyze_attachment
from MODULES.LAYER_3_BUSINESS_SERVICES.prompt_builder import (
    build_initial_question_prompt,
    build_subsequent_question_prompt,
    build_ajax_system_prompt,
    build_evaluation_prompt
)
from MODULES.LAYER_3_BUSINESS_SERVICES.mailer import send_otp_email, send_slot_unlocked_email
