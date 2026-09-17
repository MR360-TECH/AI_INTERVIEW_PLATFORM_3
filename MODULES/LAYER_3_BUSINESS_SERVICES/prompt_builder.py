def build_initial_question_prompt(practice_mode, practice_topic="General", lang_target="English", lang_focus="conversation", lang_level="intermediate"):
    if practice_mode == "viva":
        return (
            f"You are an academic external examiner starting a Viva Voce exam on the subject: {practice_topic}. "
            "Briefly introduce the exam and ask the candidate your very first conceptual question about this subject. "
            "Output ONLY the question text followed by [TYPE: TEXT] at the end. No preamble, no intro."
        )
    elif practice_mode == "lang":
        target_lang = lang_target or "English"
        focus_cat = lang_focus or "conversation"
        level = lang_level or "intermediate"
        is_english_target = target_lang.strip().lower() == "english"
        translation_rule_q1 = (
            ""
            if is_english_target
            else f"Format the question STRICTLY as follows: first write the question in {target_lang}, then on the very next line write the English translation in brackets like this: [English: <translation here>]. Do NOT skip the English translation. "
        )
        return (
            f"You are a language validator and native tutor. First, analyze the string: '{target_lang}'. "
            "Is this a legitimate language name (e.g. English, French, Spanish, Hindi, Telugu, Sindhi, Japanese, Arabic, Russian, etc.)? "
            "If it is NOT a legitimate or real language, respond with exactly: "
            "'ERROR: Language not found. Please start a new session and specify a valid language. [TYPE: TEXT]' "
            "If it IS a legitimate language, start a language speaking practice session. "
            f"The target language is: {target_lang}. The candidate's level is: {level.capitalize()}. "
            f"The focus category is: {focus_cat.capitalize()}. "
            "Briefly introduce the session with a warm and slightly friendly tone, then ask the first practice question or prompt. "
            f"{translation_rule_q1}"
            "The user can answer in any language they prefer. "
            "Output ONLY the formatted question followed by [TYPE: TEXT] at the end. No preamble, no extra commentary."
        )
    elif practice_mode == "drill":
        return (
            f"You are a friendly mentor starting a concept drill session on the topic: {practice_topic}. "
            "State the topic and ask the candidate their first open conceptual question. "
            "Output ONLY the question text followed by [TYPE: TEXT] at the end. No preamble, no intro."
        )
    return ""


def build_subsequent_question_prompt(practice_mode, practice_topic, lang_target, lang_focus, lang_level, difficulty, q_count, min_questions, conversation_text):
    if practice_mode == "viva":
        difficulty_instruction = (
            f"The candidate is undergoing an Academic Viva Voce exam on: {practice_topic}. "
            "Keep questions clear, technical, and strictly focused on academic course concepts. "
            "Evaluate their understanding of theory, equations, algorithms, or definitions."
        )
    elif practice_mode == "lang":
        target_lang = lang_target or "English"
        focus_cat = lang_focus or "conversation"
        level = lang_level or "intermediate"
        is_english_target = target_lang.strip().lower() == "english"
        translation_rule = (
            ""
            if is_english_target
            else f"IMPORTANT FORMAT RULE: Always write each question first in {target_lang}, then on the very next line write the English translation in brackets like this: [English: <translation here>]. Never skip the English translation. "
        )
        difficulty_instruction = (
            f"This is a FluentFlow language practice session in {target_lang}. The candidate's level is {level.capitalize()}. "
            f"Focus Category: {focus_cat.capitalize()}. "
            "Maintain a warm, polite, and professional but encouraging tone. Keep any conversational remarks extremely short (under 2 sentences). "
            "If the candidate's last response contained any clear grammatical, vocabulary, or structural mistakes, "
            "provide a single, polite, direct correction sentence (e.g., 'Correction: Instead of ..., it is better to say ...'), then immediately ask the next question. "
            f"{translation_rule}"
            "The candidate can answer in any language they prefer — do not restrict or comment on the language of their answer."
        )
    elif practice_mode == "drill":
        difficulty_instruction = (
            f"The candidate is doing a Concept Drill on: {practice_topic}. "
            "Ask helpful conceptual questions that challenge their logic and reasoning on this topic."
        )
    else:
        if difficulty == "student":
            difficulty_instruction = (
                "The candidate is a Student/Beginner. Keep questions friendly and focus on fundamental concepts. "
                "Ask practical, interview-style questions suitable for a junior role, rather than overly simplistic dictionary definitions (e.g. do not ask 'What is a computer?') and explore all categories of questions within the domain. "
                "Do NOT ask highly complex technical questions. If they answer incorrectly or struggle, change the topic and ask different question within the same domain. "
                "Do not end early unless you have asked at least 5 questions. "
                "Keep conversational feedback minimal and professional."
            )
        elif difficulty == "senior":
            difficulty_instruction = (
                "The candidate is a Senior/Expert. Ask challenging, deep architectural or practical scenarios. "
                "Challenge their decisions, drill down into technical specifics, and maintain a high bar. Explore different categories of questions within the domain and output only question and not anything else. Do not offer any conversational filler or praise."
            )
        else:
            difficulty_instruction = (
                "The candidate is Mid-Level. Ask standard industry questions with moderate scenarios and fundamentals. "
                "Adjust difficulty adaptively based on their performance. Explore different categories of questions within the domain and output only the question. Keep feedback professional and minimal."
            )

    completion_option = ""
    if q_count >= min_questions:
        completion_option = f"If you have gathered enough evaluation data after {min_questions} questions, you may conclude by outputting ONLY: [END_INTERVIEW]\n"

    prompt = (
        "You are an expert interviewer conducting a real-time assessment.\n\n"
        f"CANDIDATE TARGET LEVEL:\n{difficulty_instruction}\n\n"
        "CRITICAL DOMAIN RULE:\n"
        "Determine the candidate's core domain/role from their first answer. You MUST stay strictly 100% within this domain. Never switch to unrelated fields.\n\n"
        "RULES FOR OUTPUT:\n"
        "1. Output ONLY the raw next question. Keep it concise (under 2 sentences). ZERO preamble, conversational filler, praise, or acknowledgment.\n"
        "2. If they struggle or answer 'I don't know', DO NOT give them the answer. Change the topic/concept within the domain and output the next question immediately.\n"
        "3. Explore diverse categories of questions within the domain without repeating topics.\n"
        "4. HUMAN INTERVIEWER CLARIFICATION RULE: If the candidate indicates they do not understand a term or question, briefly clarify (in 1 short sentence), then state the question.\n"
        "5. BEHAVIORAL RULE: You may seamlessly integrate 1-2 behavioral or situational questions (e.g., 'Tell me about yourself', 'Why should we hire you?', or domain conflict scenarios).\n"
        "6. INPUT TAG RULE: You MUST append a tag at the very end of your output:\n"
        "   - `[TYPE: CODE]` if they need to write or fix code.\n"
        "   - `[TYPE: FILE]` if they need to upload a diagram or image.\n"
        "   - `[TYPE: TEXT]` for all standard conceptual questions.\n"
        f"{completion_option}\n"
        f"Conversation so far:\n{conversation_text}\n"
        "Output ONLY the raw question text with its tag below:"
    )
    return prompt


def build_ajax_system_prompt(domain, difficulty, resume_summary, is_practice, submit_q_count, min_questions, max_questions):
    if difficulty == "student":
        diff_note = "Candidate level: Student/Beginner. Ask practical beginner-friendly questions. No advanced or architecture-level questions."
    elif difficulty == "senior":
        diff_note = "Candidate level: Senior/Expert. Ask deep technical, architectural, and scenario-based questions. Maintain a high bar."
    else:
        diff_note = "Candidate level: Mid-Level. Ask standard industry questions with moderate depth."

    prompt_parts = [
        f"You are a strict {domain} interviewer. Domain: {domain}. {diff_note}",
        f"Resume summary: {resume_summary}" if resume_summary else "",
        f"CRITICAL RULE: ALL questions MUST be strictly within the '{domain}' domain only. NEVER ask questions from unrelated fields.",
        "Output ONLY the raw next question. Explore diverse categories within the domain. Change topic if the previous answer was wrong. Keep it concise (1-2 sentences). ZERO preamble, filler, or acknowledgment.",
        "If they answer 'I don't know', DO NOT give them the answer. Just output the next question immediately.",
    ]
    if not is_practice:
        prompt_parts.append(
            "BEHAVIORAL/SITUATIONAL RULE: Ensure to ask 2 behavioral or situational questions "
            "(e.g., 'Tell me about yourself', 'Why should we hire you?', or domain scenario questions) randomly or near the end before concluding."
        )

    if not is_practice and submit_q_count >= min_questions:
        prompt_parts.append("If the candidate has demonstrated sufficient knowledge and you are ready to finish the interview, output ONLY the exact phrase: [END_INTERVIEW]")

    prompt_parts.append(f"Question {submit_q_count + 1} (Max: {max_questions}). You MUST append [TYPE: TEXT], [TYPE: CODE], or [TYPE: FILE] at the end.")

    return " ".join(p for p in prompt_parts if p)


def build_evaluation_prompt(practice_mode, practice_topic, lang_target, difficulty, domain_val, conversation_text):
    if practice_mode == "viva":
        grading_instruction = f"Academic Viva Voce exam on {practice_topic}. Grade strictly on theoretical accuracy and academic definitions."
    elif practice_mode == "lang":
        grading_instruction = f"Language practice in {lang_target or 'English'}. Grade on grammar, vocabulary, and conversational fluency."
    elif practice_mode == "drill":
        grading_instruction = f"Concept Drill on {practice_topic}. Grade on conceptual understanding and logical reasoning."
    else:
        if difficulty == "student":
            grading_instruction = "Candidate level: Student/Beginner. Grade encouragingly on fundamentals and potential."
        elif difficulty == "senior":
            grading_instruction = "Candidate level: Senior/Expert. Grade strictly on deep technical proficiency, design, and architecture."
        else:
            grading_instruction = "Candidate level: Mid-Level. Grade balanced on standard industry expectations."

    prompt = (
        f"Evaluate this {domain_val} interview assessment.\n"
        f"{grading_instruction}\n"
        "Format EXACTLY as follows:\n"
        "SCORE: [number 1-10]\n"
        "SUMMARY:\n"
        "[2 concise professional sentences evaluating candidate performance, technical strengths, and placement recommendation.]\n\n"
        f"Transcript:\n{conversation_text}"
    )
    return prompt
