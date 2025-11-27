import streamlit as st

def get_response_aria_label(question_index: int) -> str:
    return f"Answer for question {question_index + 1}"

def display_question(question: str, current_index: int, total_questions: int) -> None:

    # Display question counter and current question
    st.markdown(f"**Question {current_index + 1} of {total_questions}**")
    
    # Display the question in a styled box matching countdown dimensions
    st.markdown(
        f'''
        <div class="question-box" style="
            display: flex;
            flex-direction: column;
            gap: 2px;
            align-items: center;
            justify-content: center;
            padding: 8px 12px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            background: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            font-family: 'Source Sans Pro', 'Segoe UI', system-ui;
            margin: 1rem 0;
            min-width: 100px;
        ">
            <div style="font-size: 0.9rem; color: #6b7280;">Question {current_index + 1} of {total_questions}</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #333333; text-align: center;">{question}</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

def display_response_area(
    question_index: int,
    current_answer: str = "",
    *,
    disabled: bool = False,
    hidden: bool = False,
) -> str:
    aria_label = get_response_aria_label(question_index)
    widget_key = f"answer_input_{question_index}"
    
    # Only show the response header when not hidden
    if not hidden:
        st.markdown("### Your Response")
    
    # Add a hidden indicator for screen readers when in audio mode
    if hidden:
        st.markdown(
            '<div class="sr-only-response" aria-live="polite">Audio mode is active; text input is hidden.</div>',
            unsafe_allow_html=True,
        )
    
    # Create the text area with a valid height
    # We'll hide it completely with CSS if needed
    response = st.text_area(
        aria_label,
        value=current_answer,
        height=200,  # Always use a valid height
        key=widget_key,
        label_visibility="collapsed",
        placeholder="Type your answer here..." if not hidden else "",
        disabled=disabled or hidden,
    )
    
    # Apply CSS to hide the text area when in audio mode
    if hidden:
        st.markdown(
            f"""
            <style>
                [data-testid="stTextArea"][aria-label="{aria_label}"] {{
                    display: none !important;
                }}
                textarea[aria-label="{aria_label}"] {{
                    display: none !important;
                }}
                .sr-only-response {{
                    position: absolute;
                    width: 1px;
                    height: 1px;
                    padding: 0;
                    margin: -1px;
                    overflow: hidden;
                    clip: rect(0, 0, 0, 0);
                    white-space: nowrap;
                    border: 0;
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    return response

def display_navigation_buttons(current_index: int, total_questions: int) -> tuple[bool, bool, bool, bool]:
   
    col1, col2, col3 = st.columns([1, 1, 2])
    prev_clicked = next_clicked = new_question_clicked = finish_clicked = False
    
    with col1:
        prev_clicked = st.button(
            "⏮️ Previous",
            disabled=current_index == 0,
            use_container_width=True
        )
    
    with col2:
        next_clicked = st.button(
            "Next ⏭️",
            disabled=current_index >= total_questions - 1,
            use_container_width=True
        )
    
    with col3:
        if current_index < total_questions - 1:
            new_question_clicked = st.button(
                "🔀 New Question",
                use_container_width=True
            )
        else:
            finish_clicked = st.button(
                "✅ Finish Interview",
                type="primary",
                use_container_width=True
            )
    
    return prev_clicked, next_clicked, new_question_clicked, finish_clicked

def display_interview_summary(questions: list, answers: dict) -> None:
   
    st.success("🎉 Great job on completing the interview!")
    st.write("### Interview Summary")
    
    # Show all questions and answers
    for i, question in enumerate(questions):
        answer = answers.get(i, "")
        with st.expander(f"Question {i + 1}: {question}"):
            st.write(f"**Your Answer:**\n{answer}" if answer else "**No response provided**")
    
    # Add download button for the interview
    st.download_button(
        label="📥 Download Interview",
        data="\n\n".join(
            f"Question {i+1}: {q}\nAnswer: {answers.get(i, 'No response')}"
            for i, q in enumerate(questions)
        ),
        file_name="interview_responses.txt",
        mime="text/plain"
    )
