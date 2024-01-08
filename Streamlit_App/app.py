import InvokeAgent as agenthelper
import streamlit as st
import json
import pandas as pd
from PIL import Image, ImageOps, ImageDraw

# Streamlit page configuration
st.set_page_config(page_title="Co. Portfolio Creator", page_icon=":robot_face:", layout="wide")

# Function to crop image into a circle
def crop_to_circle(image):
    mask = Image.new('L', image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + image.size, fill=255)
    result = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    return result

# Title
st.title("Co. Portfolio Creator")

# Display a text box for input
prompt = st.text_input("Please enter your query?", max_chars=2000)
prompt = prompt.strip()

# Display a primary button for submission
submit_button = st.button("Submit", type="primary")

# Display a button to end the session
end_session_button = st.button("End Session")

# Sidebar for user input
st.sidebar.title("Trace Data")


def filter_trace_data(trace_data, query):
    if query:
        # Filter lines that contain the query
        return "\n".join([line for line in trace_data.split('\n') if query.lower() in line.lower()])
    return trace_data
    
    

# Session State Management
if 'history' not in st.session_state:
    st.session_state['history'] = []

# Function to parse and format response
def format_response(response_body):
    try:
        # Try to load the response as JSON
        data = json.loads(response_body)
        # If it's a list, convert it to a DataFrame for better visualization
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return response_body
    except json.JSONDecodeError:
        # If response is not JSON, return as is
        return response_body



# Handling user input and responses
if submit_button and prompt:
    event = {
        "sessionId": "MYSESSION",
        "question": prompt
    }
    response = agenthelper.lambda_handler(event, None)
    
    # Parse the JSON string
    response_data = json.loads(response['body'])
    print("TRACE & RESPONSE DATA ->  ", json.loads(response['body']))
    
    # Extract the response and trace data
    all_data = format_response(response_data['response'])
    the_response = response_data['trace_data']

    # Use trace_data and formatted_response as needed
    st.sidebar.text_area("Trace Data", value=all_data, height=300)
    st.session_state['history'].append({"question": prompt, "answer": the_response})
    st.session_state['trace_data'] = the_response

    
    

if end_session_button:
    st.session_state['history'].append({"question": "Session Ended", "answer": "Thank you for using AnyCompany Support Agent!"})
    event = {
        "sessionId": "MYSESSION",
        "question": "placeholder to end session",
        "endSession": True
    }
    agenthelper.lambda_handler(event, None)
    st.session_state['history'].clear()


# Display conversation history
st.write("## Conversation History")

for chat in reversed(st.session_state['history']):
    
    # Creating columns for Question
    col1_q, col2_q = st.columns([2, 10])
    with col1_q:
        human_image = Image.open('images/human_face.png')
        circular_human_image = crop_to_circle(human_image)
        st.image(circular_human_image, width=125)
    with col2_q:
        st.text_area("Q:", value=chat["question"], height=50, key=str(chat)+"q", disabled=True)

    # Creating columns for Answer
    col1_a, col2_a = st.columns([2, 10])
    if isinstance(chat["answer"], pd.DataFrame):
        with col1_a:
            robot_image = Image.open('images/robot_face.jpg')
            circular_robot_image = crop_to_circle(robot_image)
            st.image(circular_robot_image, width=100)
        with col2_a:
            st.dataframe(chat["answer"])
    else:
        with col1_a:
            robot_image = Image.open('images/robot_face.jpg')
            circular_robot_image = crop_to_circle(robot_image)
            st.image(circular_robot_image, width=150)
        with col2_a:
            st.text_area("A:", value=chat["answer"], height=100, key=str(chat)+"a")


# Example Prompts Section

st.write("## Test Knowledge Base Prompts")
st.markdown("""
- "Give me a summary of financial market developments and open market operations in January 2023"

- "Tell me the participants view on economic conditions and economic outlook"
   
- "Provide any important information I should know about inflation, or rising prices"
   
- "Tell me about the Staff Review of the Economic & financial Situation"

""")

st.write("## Test Action Group Prompts")
st.markdown("""

- "Create a portfolio with 3 companies in the real estate industry"

- "Create portfolio of 3 companies that are in the technology industry"

- "Provide more details on these companies"

- "Create a new investment portfolio of companies"

- "Do company research on TechStashNova Inc."

""")

st.write("## Test KB, AG, history Prompt")
st.markdown("""
- Send an email to test@example.com that includes the company portfolio and FOMC summary `(The logic for this method is not implemented to send emails)`             
""")

###Example Prompts
#Tests action groups:
#1-	Do a company research on TechNova Inc.
#2-	Create me a portfolio with top 3 company profit earners. The companies need to be in the real estate industry.
#3-	please provide more details on these companies
#4-	create me another portfolio of top 3 company profit earners. They need to be in the technology industry
#5-	please help me create a new investment portfolio of companies

###Tests knowledge base:
#6-	give me a summary of development in financial market and open market operations in january 2023
#7-	what is the SEC participants view on current economic conditions and economic outlook for september 2023
#8-	can you provide any other important information I should know about inflation, or rising prices?
#9-	What can you tell me about the Staff Review of the Economic & financial Situation?
