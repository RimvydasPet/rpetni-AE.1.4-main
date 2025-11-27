import json
import os
import time

import streamlit as st
import streamlit.components.v1 as components

from llm_utils import (
    generate_question, 
    validate_google_api_key, 
    HarmCategory, 
    HarmBlockThreshold, 
    DEFAULT_SAFETY_SETTINGS,
    DEFAULT_GENERATION_CONFIG
)
from audio_input import render_audio_input_panel
from ui_components import (
    display_question,
    display_response_area,
    display_navigation_buttons,
    display_interview_summary,
    get_response_aria_label,
)

def practice_session(standalone: bool = True):
    if standalone:
        st.set_page_config(
            page_title="Practice Session",
            page_icon="🎤",
            layout="centered"
        )
    
    # Initialize session state variables if they don't exist
    required_state = {
        'questions': [],
        'current_question_index': 0,
        'answers': {},
        'question_timers': {},
        'question_locked': {},
        'safety_settings': DEFAULT_SAFETY_SETTINGS.copy(),
        'generation_config': DEFAULT_GENERATION_CONFIG.copy(),
        'initialized': True,
        'google_api_key': st.session_state.get('google_api_key', ''),
        'prompt_strategy': st.session_state.get('prompt_strategy', 'chain_of_thought')
    }
    
    # Initialize any missing session state variables
    for key, default_value in required_state.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    st.markdown("""
        <style>
            .main {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .question-box {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                border-left: 5px solid #6C63FF;
            }
            .timer {
                font-size: 24px;
                font-weight: bold;
                color: #6C63FF;
                text-align: center;
                margin: 20px 0;
            }
            .controls {
                display: flex;
                justify-content: center;
                gap: 15px;
                margin: 30px 0;
            }
            .response-area {
                min-height: 200px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 20px 0;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Get parameters from query
    difficulty = st.query_params.get("difficulty", "Professional")
    round_type = st.query_params.get("round", "Coding")
    
    # Header
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("Practice Session")
        st.caption(f"{round_type} • {difficulty} Level")
    
    # Get parameters from query or use defaults
    role = st.query_params.get("role", "Software Engineer")
    company = st.query_params.get("company", "a tech company")
    round_type = st.query_params.get("round", "Coding")
    difficulty = st.query_params.get("difficulty", "Professional")
    # Coding rounds should NOT use audio - they need text input for code
    is_coding_round = round_type.lower() == "coding"
    if "audio_checkbox" not in st.session_state:
        default_audio = st.session_state.get("audio_mode_enabled")
        if default_audio is None:
            # Disable audio for coding rounds, enable for others by default
            default_audio = False if is_coding_round else True
        st.session_state.audio_checkbox = bool(default_audio)
    
    # Resolve API key (session first, then environment)
    api_key = st.session_state.get('google_api_key') or os.getenv('GOOGLE_API_KEY')

    # Generate questions if we don't have any yet
    if not st.session_state.questions:
        # Create a container for the loading message
        loading_placeholder = st.empty()
        
        try:
            # Show initial loading message
            with loading_placeholder.container():
                st.info("🔄 Preparing your interview questions...")
                progress_bar = st.progress(0)
            
            # Generate questions
            questions = []
            for i in range(5):
                # Update progress
                progress = (i + 1) / 5
                with loading_placeholder.container():
                    st.info(f"🔄 Generating question {i+1} of 5...")
                    progress_bar.progress(progress)
                
                question = generate_question(
                    role=role,
                    company=company,
                    round_type=round_type,
                    difficulty=difficulty,
                    previous_questions=questions,  # Use the local questions list
                    api_key=api_key,
                    generation_config=st.session_state.generation_config,
                    safety_settings=st.session_state.safety_settings,
                    prompt_strategy=st.session_state.get('prompt_strategy', 'chain_of_thought'),
                )
                questions.append(question)
            
            # Store all questions in session state at once
            st.session_state.questions = questions
            
            # Clear the loading message
            loading_placeholder.empty()
            
            # Rerun to show the first question
            st.rerun()
            
        except ValueError as e:
            loading_placeholder.empty()
            st.error(f"❌ Content safety violation: {str(e)}")
            st.info("Please adjust your safety settings or try again.")
            st.session_state.questions = []  # Reset questions
            st.stop()
            
        except Exception as e:
            loading_placeholder.empty()
            error_msg = str(e).lower()
            if "api key" in error_msg or "api_key" in error_msg or "finish reasons: 3" in error_msg:
                st.error("❌ API Error: Invalid or missing Google API key")
                st.info("Please check your API key in the settings and try again.")
            else:
                st.error(f"❌ An error occurred while generating questions: {str(e)}")
            st.session_state.questions = []  # Reset questions
            st.stop()
            
        st.session_state.question_timers = {}

    round_key = round_type.lower()
    difficulty_key = difficulty.lower()
    # Coding practice gets a dedicated 15-minute timer, all other rounds reuse the
    # legacy durations (Beginner → 3 min, Professional → 5 min).
    if round_key == "coding":
        per_question_seconds = 15 * 60
    else:
        per_question_seconds_map = {
            "beginner": 3 * 60,
            "professional": 5 * 60,
        }
        per_question_seconds = per_question_seconds_map.get(difficulty_key, 5 * 60)

    interview_finished = st.session_state.get('finished', False)
    if interview_finished:
        st.session_state.audio_mode_enabled = False
        st.session_state.audio_checkbox = False
        total_questions = len(st.session_state.questions)
        snapshot_answers: dict[int, str] = {}
        for idx in range(total_questions):
            widget_key = f"answer_input_{idx}"
            if widget_key in st.session_state:
                snapshot_answers[idx] = st.session_state[widget_key]
            else:
                snapshot_answers[idx] = st.session_state.answers.get(idx, "")
        st.session_state.answers.update(snapshot_answers)
        st.markdown(
            """
            <div style="
                display:flex;
                flex-direction:column;
                gap:4px;
                align-items:center;
                justify-content:center;
                padding:12px 16px;
                border:1px solid #e5e7eb;
                border-radius:10px;
                background:#fff;
                box-shadow:0 3px 8px rgba(0,0,0,0.05);
                font-family:'Source Sans Pro', 'Segoe UI', system-ui;
            ">
                <span style="font-size:0.9rem;color:#6b7280;">Status</span>
                <div style="font-size:1.1rem;font-weight:600;color:#10b981;">
                    Interview is ended
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        display_interview_summary(st.session_state.questions, st.session_state.answers)

        role = st.query_params.get("role", "Software Engineer").lower()
        st.write("### Overall Feedback")
        response_lengths = [len(st.session_state.answers.get(i, "")) for i in range(len(st.session_state.questions))]
        avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
        feedback = ["✅ You completed all the interview questions!"]
        if avg_response_length < 100:
            feedback.append("🔧 Consider providing more detailed answers with specific examples.")
        role_specific = {
            "software engineer": [
                "💻 Great job on the technical questions!",
                "💡 Consider discussing your problem-solving process in more detail.",
                "📚 Keep practicing coding challenges to improve your speed and accuracy.",
            ],
            "data scientist": [
                "📊 Good work on the data analysis questions!",
                "🧠 Consider discussing more about your approach to data cleaning and feature engineering.",
                "📈 Practice explaining complex statistical concepts in simple terms.",
            ],
            "product manager": [
                "🎯 Good job on the product thinking questions!",
                "🤝 Consider discussing more about stakeholder management.",
                "📝 Practice creating clear and concise product requirements.",
            ],
        }
        feedback.extend(
            role_specific.get(
                role,
                [
                    "😎 You're doing great!",
                    "📚 Keep practicing to improve your interview skills.",
                ],
            )
        )
        for item in feedback:
            st.write(f"- {item}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Start New Interview", use_container_width=True):
                all_keys = (
                    [
                        'paused',
                        'finished',
                        'questions',
                        'current_question_index',
                        'question_timers',
                        'question_locked',
                        'audio_mode_enabled',
                        'audio_checkbox',
                    ]
                    + [f"answer_{i}" for i in range(10)]
                )
                for key in all_keys:
                    st.session_state.pop(key, None)
                st.rerun()
        with col2:
            if st.button("🏠 Back to Setup", use_container_width=True):
                st.query_params.clear()
                st.session_state.clear()
                st.rerun()

        return
    else:
        current_index = st.session_state.current_question_index
        if 'question_timers' not in st.session_state:
            st.session_state.question_timers = {}
        if 'question_locked' not in st.session_state:
            st.session_state.question_locked = {}
        if current_index not in st.session_state.question_timers:
            st.session_state.question_timers[current_index] = time.time()

        question_start_time = st.session_state.question_timers[current_index]
        elapsed = max(0, int(time.time() - question_start_time))
        elapsed = min(elapsed, per_question_seconds)
        remaining = per_question_seconds - elapsed
        remaining_minutes = remaining // 60
        remaining_seconds = remaining % 60

        timer_dom_id = f"countdown-watch-{current_index}-{int(question_start_time)}"
        timer_html = f"""
        <div id=\"{timer_dom_id}\" style=\"
            display:flex;
            flex-direction:column;
            gap:2px;
            align-items:center;
            justify-content:center;
            padding:8px 12px;
            border:1px solid #e5e7eb;
            border-radius:8px;
            background:#fff;
            box-shadow:0 2px 4px rgba(0,0,0,0.05);
            font-family:'Source Sans Pro', 'Segoe UI', system-ui;
            min-width: 100px;
        \">
            <span style=\"font-size:0.9rem;color:#6b7280;\">Question Countdown</span>
            <div class=\"timer-watch__value\" style=\"font-size:1.8rem;font-weight:700;color:#6C63FF;\">
                {remaining_minutes:02d}:{remaining_seconds:02d}
            </div>
        </div>
        {"" if remaining <= 0 else f"""<script>
        (function() {{
            const container = document.getElementById('{timer_dom_id}');
            if (!container) return;
            const valueEl = container.querySelector('.timer-watch__value');
            let remaining = {remaining};
            const pad = (val) => String(val).padStart(2, '0');
            const render = () => {{
                const mins = pad(Math.floor(remaining / 60));
                const secs = pad(remaining % 60);
                valueEl.textContent = `${{mins}}:${{secs}}`;
            }};
            const notifyLock = () => {{
                if (window.parent) {{
                    window.parent.postMessage({{type: 'timer-lock', index: {current_index}}}, '*');
                    window.parent.postMessage({{type: 'streamlit:rerun'}}, '*');
                }} else {{
                    window.postMessage({{type: 'timer-lock', index: {current_index}}}, '*');
                    window.postMessage({{type: 'streamlit:rerun'}}, '*');
                }}
            }};
            render();
            const interval = setInterval(() => {{
                remaining = Math.max(remaining - 1, 0);
                render();
                if (remaining === 0) {{
                    clearInterval(interval);
                    notifyLock();
                }}
            }}, 1000);
        }})();
        </script>"""}
        """
        components.html(timer_html, height=110, scrolling=False)
        if remaining == 0:
            st.session_state.question_locked[current_index] = True
            st.warning("Time's up for this question. Move to the next one when you're ready.")

    # Get current question with safety check
    try:
        current_question = st.session_state.questions[st.session_state.current_question_index]
    except IndexError:
        st.error("No questions available. Please check your settings and try again.")
        return
    
    # Display current question and response area
    display_question(
        current_question,
        st.session_state.current_question_index,
        len(st.session_state.questions)
    )
    
    # Initialize answers in session state if not exists
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    # Get current answer or initialize empty
    current_answer = st.session_state.answers.get(st.session_state.current_question_index, "")
    
    # Display response area and get user input
    current_locked = st.session_state.question_locked.get(st.session_state.current_question_index, False)
    response_container_id = f"response-area-{st.session_state.current_question_index}"
    widget_key = f"answer_input_{st.session_state.current_question_index}"
    
    # Get audio mode state - but never enable for coding rounds
    audio_mode = st.session_state.get("audio_mode_enabled", st.session_state.get("audio_checkbox", False))
    # Force disable audio for coding rounds
    if is_coding_round:
        audio_mode = False
        audio_enabled = False
        audio_only_mode = False
    else:
        audio_enabled = bool(
            st.session_state.get(
                "audio_mode_enabled",
                st.session_state.get("audio_checkbox", True),
            )
        )
        audio_only_mode = audio_enabled

    # Main response area container
    with st.container():
        # Response area (text input - always visible for coding, hidden for audio mode in other rounds)
        st.markdown(f'<div id="{response_container_id}">', unsafe_allow_html=True)
        user_response = display_response_area(
            st.session_state.current_question_index,
            current_answer,
            disabled=current_locked,
            hidden=audio_mode and not current_locked and not is_coding_round,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Add some spacing before audio controls
        st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)

        # Audio input panel - NEVER show for coding rounds
        if not is_coding_round and audio_enabled and not current_locked:
            render_audio_input_panel(
                response_container_id,
                title="Prefer speaking? We'll transcribe in real time",
                initial_text=user_response,
            )
        elif not is_coding_round and audio_enabled and current_locked:
            st.info("🎧 Audio capture disabled because this question is locked. Use navigation to continue.")
        
        # Audio mode indicator - not shown for coding rounds
        if not is_coding_round and audio_only_mode and not current_locked:
            st.info("🎙️ Audio mode is enabled. Answers are captured from your microphone only.")
    
    # Get the latest response after potential audio updates
    latest_response = st.session_state.get(widget_key, user_response)
    st.session_state.answers[st.session_state.current_question_index] = latest_response
    aria_label = get_response_aria_label(st.session_state.current_question_index)
    
    # Add some spacing before navigation
    st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <script>
        (function() {{
            const containerId = '{response_container_id}';
            const ariaLabel = {json.dumps(aria_label)};
            const container = document.getElementById(containerId);
            let textarea = null;
            let isLocked = Boolean({1 if current_locked else 0});
            const audioOnly = Boolean({1 if audio_only_mode else 0});

            const pickVisible = (elements) => {{
                if (!elements || !elements.length) return null;
                for (const element of elements) {{
                    if (element && element.offsetParent !== null) {{
                        return element;
                    }}
                }}
                return elements[0] || null;
            }};

            const findTextarea = () => {{
                if (textarea && document.body.contains(textarea)) {{
                    return textarea;
                }}

                const candidates = [
                    container ? container.querySelector('textarea') : null,
                    ...Array.from(document.querySelectorAll(`textarea[aria-label="${{ariaLabel}}"]`)),
                    ...Array.from(document.querySelectorAll('textarea[placeholder="Type your answer here..."]')),
                    ...Array.from(document.querySelectorAll('textarea')),
                ].filter(Boolean);

                const nextMatch = pickVisible(candidates);
                if (nextMatch) {{
                    textarea = nextMatch;
                }}
                return textarea;
            }};

            const syncValue = (value) => {{
                const target = findTextarea();
                if (!target) return;
                target.value = value || '';
                target.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }};

            const lockTextarea = () => {{
                const target = findTextarea();
                if (!target) return;
                isLocked = true;
                target.setAttribute('readonly', 'true');
                target.setAttribute('disabled', 'true');
                target.classList.add('response-locked');
                target.blur();
            }};

            const enforceAudioOnly = () => {{
                const target = findTextarea();
                if (!target || isLocked) return;
                if (audioOnly) {{
                    target.setAttribute('readonly', 'true');
                    target.classList.add('response-audio-only');
                }} else {{
                    target.removeAttribute('readonly');
                    target.classList.remove('response-audio-only');
                }}
            }};

            if (isLocked) {{
                lockTextarea();
            }} else {{
                enforceAudioOnly();
            }}

            window.addEventListener('message', (event) => {{
                if (event?.data?.type === 'timer-lock' && event.data.index === {st.session_state.current_question_index}) {{
                    lockTextarea();
                }}
                if (event?.data?.type === 'audio-transcript' && event.data.targetId === containerId) {{
                    syncValue(event.data.value || '');
                    enforceAudioOnly();
                }}
            }});
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )
    if current_locked:
        st.info("✋ Time is up for this question. Use navigation to move on.")
    
    # Handle navigation buttons
    prev_clicked, next_clicked, new_question_clicked, finish_clicked = display_navigation_buttons(
        st.session_state.current_question_index,
        len(st.session_state.questions)
    )
    
    # Handle button actions
    if prev_clicked:
        st.session_state.current_question_index -= 1
        st.rerun()
    elif next_clicked:
        st.session_state.current_question_index += 1
        st.rerun()
    elif finish_clicked:
        st.session_state.finished = True
        st.session_state.audio_mode_enabled = False
        st.session_state.audio_checkbox = False
        st.rerun()

if __name__ == "__main__":
    practice_session()
