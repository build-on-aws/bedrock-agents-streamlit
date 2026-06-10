import invoke_agent as agenthelper
import streamlit as st
import json
import re
import pandas as pd
from PIL import Image, ImageOps, ImageDraw
import pathlib

# Streamlit page configuration
st.set_page_config(page_title="Co. Portfolio Creator", page_icon=":robot_face:", layout="wide")

# Resolve app directory for image paths
_app_dir = pathlib.Path(__file__).parent

# Function to crop image into a circle
def crop_to_circle(image):
    mask = Image.new('L', image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + image.size, fill=255)
    result = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    return result

# Load images once
human_image = Image.open(_app_dir / 'human_face.png')
robot_image = Image.open(_app_dir / 'robot_face.jpg')
circular_human_image = crop_to_circle(human_image)
circular_robot_image = crop_to_circle(robot_image)

# Title
st.title("Co. Portfolio Creator")

# -------------------------------------------------------------------
# Sidebar: Tabs for Configuration, Example Prompts, Trace Data
# -------------------------------------------------------------------
sidebar_tab1, sidebar_tab2, sidebar_tab3 = st.sidebar.tabs(["⚙️ Config", "💡 Prompts", "📊 Trace"])

# --- Tab 1: Agent Configuration ---
with sidebar_tab1:
    if 'agent_id' not in st.session_state:
        st.session_state['agent_id'] = ""
    if 'agent_alias_id' not in st.session_state:
        st.session_state['agent_alias_id'] = ""

    agent_id = st.text_input("Agent ID", value=st.session_state['agent_id'], placeholder="e.g. ABCDEF1234")
    agent_alias_id = st.text_input("Agent Alias ID", value=st.session_state['agent_alias_id'], placeholder="e.g. ZYXWVU9876")

    st.session_state['agent_id'] = agent_id
    st.session_state['agent_alias_id'] = agent_alias_id

if not agent_id or not agent_alias_id:
    st.warning("Please enter your **Agent ID** and **Agent Alias ID** in the sidebar to get started.")

# --- Tab 2: Example Prompts ---
with sidebar_tab2:
    st.markdown("**Knowledge Base**")
    st.markdown("""
- Give me a summary of financial market developments and open market operations in January 2023
- Tell me the participants view on economic conditions and economic outlook
- Provide any important information I should know about consumer inflation, or rising prices
- Tell me about the Staff Review of the Economic & financial Situation
    """)

    st.markdown("**Action Group**")
    st.markdown("""
- Create a portfolio with 3 companies in the real estate industry
- Create a portfolio of 4 companies that are in the technology industry
- Return me information on the company on TechStashNova Inc.
    """)

    st.markdown("**KB + AG + Email**")
    st.markdown("""
- Send an email to test@example.com that includes the summary and portfolio report
    """)
    st.caption("Note: Replace with your verified SES email address")

# --- Tab 3: Trace Data ---
with sidebar_tab3:
    # Full-screen trace dialog
    @st.dialog("Trace Data", width="large")
    def show_full_trace():
        trace = st.session_state.get('last_trace', 'No trace data yet.')
        if isinstance(trace, pd.DataFrame):
            st.dataframe(trace, use_container_width=True)
        else:
            st.code(trace, language=None)

    if st.button("Expand Full View"):
        show_full_trace()

# Session State Management
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'last_trace' not in st.session_state:
    st.session_state['last_trace'] = ""

# -------------------------------------------------------------------
# Helper: Clean up raw trace data for display
# -------------------------------------------------------------------
def clean_trace_data(raw_trace):
    """Extract meaningful trace steps from the raw debug output."""
    if not raw_trace or not isinstance(raw_trace, str):
        return "No trace data available."

    lines = raw_trace.strip().split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        # Skip raw binary/encoded data and internal debug noise
        if not line:
            continue
        if line.startswith("Decoded response:"):
            continue
        if line.startswith("Split Response:"):
            continue
        if line.startswith("Length of split:"):
            continue
        if line.startswith("Last Response:"):
            continue
        if line.startswith("No bytes at index"):
            continue
        if line.startswith("Bytes in last response"):
            continue
        if "message-type" in line and len(line) > 200:
            continue
        if re.match(r'^[A-Za-z0-9+/=]{50,}$', line):
            continue
        # Keep meaningful decoded content
        cleaned.append(line)

    if not cleaned:
        return "No trace details captured."

    return '\n'.join(cleaned)


# -------------------------------------------------------------------
# Helper: Format response body
# -------------------------------------------------------------------
def format_response(response_body):
    try:
        data = json.loads(response_body)
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return response_body
    except json.JSONDecodeError:
        return response_body

# -------------------------------------------------------------------
# Input area
# -------------------------------------------------------------------
prompt = st.text_input("Please enter your query?", max_chars=2000)
prompt = prompt.strip()

submit_button = st.button("Submit", type="primary")
end_session_button = st.button("End Session")

# -------------------------------------------------------------------
# Handle submit
# -------------------------------------------------------------------
if submit_button and prompt:
    if not agent_id or not agent_alias_id:
        st.error("Please enter your Agent ID and Agent Alias ID in the sidebar before submitting a query.")
    else:
        event = {
            "sessionId": "MYSESSION",
            "question": prompt,
            "agentId": agent_id,
            "agentAliasId": agent_alias_id
        }
        response = agenthelper.lambda_handler(event, None)

        trace_raw = ""
        the_response = ""

        try:
            if response and 'body' in response and response['body']:
                response_data = json.loads(response['body'])
            else:
                response_data = None
        except json.JSONDecodeError:
            response_data = None

        try:
            if response_data is None:
                trace_raw = "No response data"
                the_response = "Failed to get response from agent"
            elif 'error' in response_data:
                trace_raw = "Error occurred"
                the_response = f"Agent error: {response_data['error']}"
            elif 'response' in response_data and 'trace_data' in response_data:
                trace_raw = format_response(response_data['response'])
                the_response = response_data['trace_data']
            else:
                trace_raw = str(response_data)
                the_response = "Unexpected response format"
        except Exception as e:
            trace_raw = "..."
            the_response = f"Error occurred: {str(e)}"

        # Display cleaned trace data in sidebar and store for full view
        if isinstance(trace_raw, str):
            cleaned_trace = clean_trace_data(trace_raw)
            st.session_state['last_trace'] = cleaned_trace
            with sidebar_tab3:
                st.text_area("", value=cleaned_trace, height=300, label_visibility="collapsed")
        else:
            st.session_state['last_trace'] = trace_raw
            with sidebar_tab3:
                st.dataframe(trace_raw)

        # Add to history (newest will be rendered first)
        st.session_state['history'].append({"question": prompt, "answer": the_response})

# -------------------------------------------------------------------
# Handle end session
# -------------------------------------------------------------------
if end_session_button:
    st.session_state['history'].append({"question": "Session Ended", "answer": "Thank you for using AnyCompany Support Agent!"})
    event = {
        "sessionId": "MYSESSION",
        "question": "placeholder to end session",
        "endSession": True,
        "agentId": agent_id,
        "agentAliasId": agent_alias_id
    }
    agenthelper.lambda_handler(event, None)
    st.session_state['history'].clear()

# -------------------------------------------------------------------
# Conversation History (newest first)
# -------------------------------------------------------------------
st.write("## Conversation History")

for index, chat in enumerate(reversed(st.session_state['history'])):
    # Question
    col1_q, col2_q = st.columns([1, 11])
    with col1_q:
        st.image(circular_human_image, width=50)
    with col2_q:
        st.text(f"You: {chat['question']}")

    # Answer
    col1_a, col2_a = st.columns([1, 11])
    if isinstance(chat["answer"], pd.DataFrame):
        with col1_a:
            st.image(circular_robot_image, width=50)
        with col2_a:
            st.dataframe(chat["answer"], key=f"answer_df_{index}")
    else:
        with col1_a:
            st.image(circular_robot_image, width=50)
        with col2_a:
            with st.container(border=True):
                st.write(chat['answer'])

    st.divider()
