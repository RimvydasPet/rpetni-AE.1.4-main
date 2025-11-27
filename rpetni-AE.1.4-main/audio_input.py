from __future__ import annotations
import json
from textwrap import dedent
import streamlit as st
import streamlit.components.v1 as components

def render_audio_input_panel(
    target_container_id: str,
    *,
    title: str = "Speak your answer",
    initial_text: str = "",
) -> None:
    panel_dom_id = f"audio-panel-{target_container_id}"
    html = dedent(
        f"""
        <div id="{panel_dom_id}" class="audio-panel">
            <style>
                #{panel_dom_id} {{
                    border: 1px solid #e5e7eb;
                    border-radius: 10px;
                    padding: 16px;
                    margin: 12px 0 0 0;
                    background: #f9fafb;
                    font-family: 'Source Sans Pro', 'Segoe UI', system-ui;
                    width: 100%;
                    max-width: 100%;
                    box-sizing: border-box;
                }}
                #{panel_dom_id} .audio-panel__header {{
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                    margin-bottom: 8px;
                }}
                #{panel_dom_id} .audio-panel__title {{
                    font-size: 0.95rem;
                    font-weight: 600;
                    color: #111827;
                }}
                #{panel_dom_id} button {{
                    border: none;
                    border-radius: 999px;
                    padding: 8px 16px;
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: #fff;
                    background: #6366f1;
                    cursor: pointer;
                }}
                #{panel_dom_id} button[disabled] {{
                    opacity: 0.5;
                    cursor: not-allowed;
                }}
                #{panel_dom_id} .audio-panel__status {{
                    margin-top: 10px;
                    font-size: 0.85rem;
                    color: #4b5563;
                }}
                #{panel_dom_id} textarea {{
                    width: 100%;
                    min-height: 80px;
                    margin: 0;
                    padding: 10px;
                    border-radius: 8px;
                    border: 1px solid #d1d5db;
                    resize: vertical;
                    font-size: 0.95rem;
                    font-family: inherit;
                    box-sizing: border-box;
                }}
            </style>
            <div class="audio-panel__header">
                <span class="audio-panel__title">{title}</span>
                <button data-role="toggle" type="button">Start Recording</button>
            </div>
            <div class="audio-panel__status" data-role="status">Idle</div>
            <textarea data-role="transcript" placeholder="Transcript will appear here...">{initial_text}</textarea>
        </div>
        <script>
        (function() {{
            const targetId = {json.dumps(target_container_id)};
            const root = document.getElementById('{panel_dom_id}');
            if (!root) return;
            const statusEl = root.querySelector('[data-role="status"]');
            const toggleBtn = root.querySelector('[data-role="toggle"]');
            const transcriptEl = root.querySelector('[data-role="transcript"]');
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            let recognition = null;
            let listening = false;

            const postMessage = (payload) => {{
                if (window.parent) {{
                    window.parent.postMessage(payload, '*');
                }} else {{
                    window.postMessage(payload, '*');
                }}
            }};

            const sendTranscript = (value) => {{
                postMessage({{
                    type: 'audio-transcript',
                    targetId: targetId,
                    value: value || ''
                }});
            }};

            const setStatus = (text) => {{
                if (statusEl) statusEl.textContent = text;
            }};

            if (!SpeechRecognition) {{
                toggleBtn.disabled = true;
                setStatus('Browser does not support speech recognition.');
                return;
            }}

            recognition = new SpeechRecognition();
            recognition.lang = 'en-US';
            recognition.continuous = true;
            recognition.interimResults = true;

            const handleResult = (event) => {{
                let combined = '';
                for (let i = 0; i < event.results.length; i += 1) {{
                    combined += event.results[i][0].transcript;
                }}
                transcriptEl.value = combined.trim();
                sendTranscript(transcriptEl.value);
            }};

            recognition.onresult = handleResult;
            recognition.onerror = (event) => {{
                setStatus('Error: ' + (event.error || 'Unknown'));
                if (listening) {{
                    listening = false;
                    toggleBtn.textContent = 'Start Recording';
                }}
            }};
            recognition.onstart = () => {{
                listening = true;
                toggleBtn.textContent = 'Stop Recording';
                setStatus('Listening... speak now.');
            }};
            recognition.onend = () => {{
                listening = false;
                toggleBtn.textContent = 'Start Recording';
                setStatus('Recording stopped.');
            }};

            toggleBtn.addEventListener('click', () => {{
                if (!recognition) return;
                if (listening) {{
                    recognition.stop();
                }} else {{
                    try {{
                        recognition.start();
                        setStatus('Requesting microphone access...');
                    }} catch (err) {{
                        setStatus('Unable to start recording: ' + err.message);
                    }}
                }}
            }});

            if ({json.dumps(bool(initial_text))}) {{
                sendTranscript(transcriptEl.value);
            }}
        }})();
        </script>
        """
    )

    components.html(html, height=260, scrolling=False)
