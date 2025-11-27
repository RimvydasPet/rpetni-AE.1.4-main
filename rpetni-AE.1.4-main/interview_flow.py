import streamlit as st


def handle_practice_navigation() -> bool:
    if st.session_state.get("start_practice", False):
        st.session_state.start_practice = False

        selected_round = st.session_state.get("round_radio", "Coding")
        selected_difficulty = st.session_state.get("difficulty_radio", "Professional")
        role = st.session_state.get("role", "Software Engineer")
        company = st.session_state.get("company", "")

        params = dict(st.query_params)
        params.update(
            {
                "page": "practice",
                "round": selected_round,
                "difficulty": selected_difficulty,
                "role": role,
                "company": company,
            }
        )
        st.query_params.update(**params)
        st.rerun()

    return st.query_params.get("page") == "practice"
