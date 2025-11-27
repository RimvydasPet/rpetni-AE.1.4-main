import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from interview_flow import handle_practice_navigation
from llm_utils import (
    generate_question,
    validate_google_api_key,
    DEFAULT_GENERATION_CONFIG,
    DEFAULT_SAFETY_SETTINGS,
    HarmCategory,
    HarmBlockThreshold,
)
from prompt_strategies import get_available_strategies

DOTENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, override=False)

def get_google_api_key() -> str | None:
    # Check session state first (user-provided API key)
    if 'user_api_key' in st.session_state and st.session_state.user_api_key:
        return st.session_state.user_api_key.strip()

    load_dotenv(dotenv_path=DOTENV_PATH, override=True)
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        return key.strip()

    if DOTENV_PATH.exists():
        try:
            with open(DOTENV_PATH, encoding="utf-8") as env_file:
                for line in env_file:
                    if line.strip().startswith("GOOGLE_API_KEY="):
                        _, value = line.split("=", 1)
                        value = value.strip().strip('"').strip("'")
                        if value:
                            return value
        except OSError:
            pass
    return None

def set_page_config():
    st.set_page_config(
        page_title="Interview Preparation",
        page_icon="🎯",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    apply_app_styles()


def apply_app_styles() -> None:
    styles_path = Path(__file__).resolve().parent / "styles.css"
    if styles_path.exists():
        with open(styles_path, encoding="utf-8") as css_file:
            st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("styles.css file is missing. UI may not render as expected.")

def main():
    set_page_config()
    
    # Initialize session state for role and company if not exists
    if 'role' not in st.session_state:
        st.session_state.role = ""
    if 'company' not in st.session_state:
        st.session_state.company = ""
    if 'user_api_key' not in st.session_state:
        st.session_state.user_api_key = ""

    practice_mode_active = handle_practice_navigation()

    # Defaults when practice session is already running
    api_key_validation_error: str | None = None
    role_provided = bool(st.session_state.role.strip())
    api_key_available = False

    if not practice_mode_active:
        # API Key Input Section (at the top)
        st.markdown('<div class="section-title">API Key</div>', unsafe_allow_html=True)
        st.markdown('Get a Google API key from [Google AI Studio](https://aistudio.google.com/app/apikey)')

        user_api_key = st.text_input(
            "Paste your Google API Key here",
            value=st.session_state.user_api_key,
            type="password",
            placeholder="Enter your API key",
            key="api_key_input",
            help="Your API key is only stored in this session and never saved to disk."
        )
        if user_api_key:
            st.session_state.user_api_key = user_api_key

        st.markdown("---")

        # Header with job title and company
        col1, col2 = st.columns([5, 1])
        with col1:
            # Role input
            st.session_state.role = st.text_input(
                "Role", 
                value=st.session_state.role, 
                label_visibility="collapsed", 
                placeholder="Enter role (e.g., Full Stack Developer)",
                key="role_input"
            )
            st.markdown(f'<div class="job-title">{st.session_state.role}</div>', unsafe_allow_html=True)
            
            # Company input
            st.session_state.company = st.text_input(
                "Company", 
                value=st.session_state.company, 
                label_visibility="collapsed", 
                placeholder="Enter company name (optional)",
                key="company_input"
            )
            if st.session_state.company:
                st.markdown(f'<div class="company">{st.session_state.company}</div>', unsafe_allow_html=True)
        
        # Select Round
        st.markdown('<div class="section-title">Select Round</div>', unsafe_allow_html=True)
        role_text = st.session_state.role.lower()
        coding_keywords = ["developer", "engineer", "coder", "coding", "programmer", "software"]
        coding_round_enabled = any(keyword in role_text for keyword in coding_keywords)

        if coding_round_enabled:
            rounds = ["Warm Up", "Coding", "Role Related", "Behavioral"]
        else:
            rounds = ["Warm Up", "Role Related", "Behavioral"]
            if st.session_state.get("round_radio") == "Coding":
                st.session_state.round_radio = "Warm Up"
        st.radio(
            "Select Round", 
            options=rounds, 
            index=0 if st.session_state.get("round_radio") not in rounds else rounds.index(st.session_state.round_radio), 
            format_func=lambda x: x, 
            key="round_radio", 
            horizontal=True, 
            label_visibility="collapsed",
        )
        
        # Difficulty Level
        st.markdown('<div class="section-title">Difficulty Level</div>', unsafe_allow_html=True)
        difficulty_levels = ["Beginner", "Professional"]
        st.radio(
            "Difficulty Level", 
            options=difficulty_levels, 
            index=1, 
            format_func=lambda x: x, 
            key="difficulty_radio", 
            horizontal=True, 
            label_visibility="collapsed",
        )
        
        # Practice Settings
        st.markdown('<div class="section-title">Practice Settings</div>', unsafe_allow_html=True)
        col1, = st.columns(1)
        with col1:
            selected_round = st.session_state.get("round_radio", "Warm Up")
            # Coding round should NOT use audio mode - it needs text input for code
            audio_disabled_for_coding = selected_round == "Coding"
            if audio_disabled_for_coding:
                st.session_state.audio_checkbox = False
                st.session_state.audio_mode_enabled = False
                st.checkbox(
                    "Audio (disabled for Coding)",
                    value=False,
                    key="audio_checkbox",
                    disabled=True,
                    help="Coding practice requires text input for writing code.",
                )
            else:
                current_audio_pref = st.session_state.get("audio_checkbox", True)
                audio_pref = st.checkbox("Audio", value=current_audio_pref, key="audio_checkbox")
                st.session_state.audio_mode_enabled = audio_pref

        if "generation_config" not in st.session_state:
            st.session_state.generation_config = DEFAULT_GENERATION_CONFIG.copy()
        else:
            # Update max_output_tokens if it's too low (from old default)
            if st.session_state.generation_config.get("max_output_tokens", 0) < 1024:
                st.session_state.generation_config["max_output_tokens"] = DEFAULT_GENERATION_CONFIG["max_output_tokens"]
        generation_config = st.session_state.generation_config

        # Prompt Strategy Selection
        st.markdown('<div class="section-title">Prompt Strategy</div>', unsafe_allow_html=True)
        st.caption("Choose which prompting technique to use for generating questions")
        
        # Initialize prompt strategy in session state
        if 'prompt_strategy' not in st.session_state:
            st.session_state.prompt_strategy = "chain_of_thought"
        
        # Get available strategies
        strategies = get_available_strategies()
        strategy_options = {
            strategies[key]["name"]: key 
            for key in strategies.keys()
        }
        
        # Create selectbox with strategy names
        selected_strategy_name = st.selectbox(
            "Prompting Technique",
            options=list(strategy_options.keys()),
            index=list(strategy_options.values()).index(st.session_state.prompt_strategy),
            help="Different prompting techniques can produce different quality questions. Experiment to find what works best!",
            key="strategy_selectbox"
        )
        
        # Store the strategy key
        st.session_state.prompt_strategy = strategy_options[selected_strategy_name]
        
        # Show description of selected strategy
        selected_strategy_info = strategies[st.session_state.prompt_strategy]
        st.info(f"ℹ️ **{selected_strategy_info['name']}**: {selected_strategy_info['description']}")

        with st.expander("LLM Generation Settings", expanded=False):
            st.caption(
                "Tune how creative or focused Gemini should be while crafting interview questions."
            )
            col_a, col_b = st.columns(2)
            with col_a:
                generation_config["temperature"] = st.slider(
                    "Temperature",
                    min_value=0.3,
                    max_value=1.0,
                    step=0.05,
                    value=float(generation_config.get("temperature", 0.75)),
                    help="0.6–0.9 recommended. Higher = more creative interviewer styles.",
                )
                generation_config["top_k"] = st.slider(
                    "Top-k",
                    min_value=1,
                    max_value=128,
                    step=1,
                    value=int(generation_config.get("top_k", 40)),
                    help="Lower values keep answers focused; higher values sample from a wider vocabulary.",
                )
            with col_b:
                generation_config["top_p"] = st.slider(
                    "Top-p",
                    min_value=0.5,
                    max_value=1.0,
                    step=0.05,
                    value=float(generation_config.get("top_p", 0.9)),
                    help="0.8–1.0 keeps follow-ups diverse without going off-topic.",
                )
                generation_config["max_output_tokens"] = st.slider(
                    "Max Tokens",
                    min_value=512,
                    max_value=8192,  # Increased from 4096 to 8192
                    step=128,
                    value=int(generation_config.get("max_output_tokens", 3000)),  # Updated default
                    help="1024-3000 recommended for interview questions. Higher values allow longer responses.",
                )
        
        # Safety Settings
        st.markdown("### Content Safety Settings")
        st.caption("Configure content safety filters for generated questions.")
        
        if 'safety_settings' not in st.session_state:
            st.session_state.safety_settings = DEFAULT_SAFETY_SETTINGS
            
        # Safety threshold options mapping
        safety_thresholds = {
            "Block None": HarmBlockThreshold.BLOCK_NONE,
            "Block Few": HarmBlockThreshold.BLOCK_ONLY_HIGH,
            "Block Some": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            "Block Most": HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
        }
        
        # Safety categories to show in UI
        safety_categories = {
            "Harassment": HarmCategory.HARM_CATEGORY_HARASSMENT,
            "Hate Speech": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            "Sexually Explicit": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            "Dangerous Content": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
        }
        
        # Create a column for each safety category
        cols = st.columns(len(safety_categories))
        
        for i, (category_name, category) in enumerate(safety_categories.items()):
            with cols[i % len(cols)]:
                threshold = st.selectbox(
                    category_name,
                    options=list(safety_thresholds.keys()),
                    index=2,  # Default to "Block Some"
                    key=f"safety_{category_name}",
                    help=f"Safety threshold for {category_name.lower()} content"
                )
                st.session_state.safety_settings[category] = safety_thresholds[threshold]
        
        api_key = get_google_api_key()
        if api_key:
            cached_key = st.session_state.get("validated_api_key")
            try:
                if cached_key != api_key:
                    validate_google_api_key(
                    api_key,
                    generation_config=st.session_state.generation_config,
                    safety_settings=st.session_state.safety_settings,
                )
                    st.session_state.validated_api_key = api_key
                st.success("API key loaded from environment (.env file or shell). You're ready to call external services.")
                st.session_state.google_api_key = api_key
            except Exception as exc: 
                api_key_validation_error = str(exc)
                api_key = None
                st.error(f"Invalid API key: {api_key_validation_error}")
        else:
            # Only show API key instructions when a key isn't available yet
            st.markdown('### API Key')
            st.markdown('You need a Google API key to generate interview questions. Get one from [Google AI Studio](https://aistudio.google.com/app/apikey)')
            st.error("No API key detected. Create a .env file with GOOGLE_API_KEY=your-key, then restart the app.")
        
        # No API key needed anymore - using local questions
        st.info("ℹ️ Practice with automatically generated questions")
        
        role_provided = bool(st.session_state.role.strip())
        api_key_available = bool(api_key)

    # Action Buttons
    warning_messages: list[str] = []
    start_clicked = False
    with st.container():
        st.markdown('<div class="action-row">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("CANCEL", use_container_width=True, type="secondary"):
                st.rerun()
        with col2:
            if practice_mode_active:
                st.button(
                    "PRACTICE RUNNING",
                    use_container_width=True,
                    type="primary",
                    disabled=True,
                )
            else:
                start_clicked = st.button(
                    "START PRACTICE",
                    type="primary",
                    use_container_width=True
                )
        st.markdown('</div>', unsafe_allow_html=True)

    if start_clicked and not practice_mode_active:
        if not role_provided:
            warning_messages.append("Enter a position title before starting your practice session.")
        if role_provided and not api_key_available:
            warning_messages.append("Add a valid GOOGLE_API_KEY to .env and restart before generating questions.")
        if role_provided and api_key_validation_error:
            warning_messages.append("Your Google API key appears invalid. Update it in .env and restart before generating questions.")
        if role_provided and api_key_available:
            st.session_state.start_practice = True
            handle_practice_navigation()
            st.rerun()

    for message in warning_messages:
        st.markdown(f'<div class="inline-warning">{message}</div>', unsafe_allow_html=True)

    if practice_mode_active:
        from practice_app import practice_session

        st.markdown("<div class='section-title'>Practice Session</div>", unsafe_allow_html=True)
        try:
            practice_session(standalone=False)
        except Exception as e:
            st.error(f"An error occurred during the practice session: {str(e)}")
            st.info("Please check your settings and try again. If the problem persists, try adjusting the content safety settings.")

if __name__ == "__main__":
    main()