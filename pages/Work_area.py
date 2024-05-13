import random
import time

import clientserverUtils as csu
import userUtils
import streamlit as st
from streamlit_feedback import streamlit_feedback
from pathlib import Path
from datetime import datetime
import json
import base64
import importlib
from streamlit_extras.stylable_container import stylable_container
import threading

if csu.option_use_trubrics:
    from trubrics.integrations.streamlit import FeedbackCollector

# This is a paid-like service to capture metrics, very good but restricted...
# We implemented both variants

st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Hello", page_icon=":rocket:")

USE_BASE_CLOUD_MODEL = False
LOCAL_CHATBOT_MODEL = csu.getLocalChatBotModelInstance() if USE_BASE_CLOUD_MODEL is False else None
replicate_api = None
showREPLICATE_details = False

debug = 0
debug_model = 0
if debug == 0:  # Require signin if not logged in
    if not csu.logged_in():
        st.warning("You need to login")
        st.stop()

    csu.showLoggedUserSidebar()

DEMO_MODE = (USE_BASE_CLOUD_MODEL is False) and True # If to implement the DdoS trigger stuff
DEMO_MODE_SCRIPT = True # If true, the script will be run without user input

#######################################

if USE_BASE_CLOUD_MODEL:
    import replicate
import os

# Parameter models
temperature = None
top_p = None
max_length = None
llm = None

file_ = open("data/characters/man.png", "rb")
contents = file_.read()
data_url = base64.b64encode(contents).decode("utf-8")
file_.close()

st.sidebar.markdown(
    f'<img src="data:image/gif;base64,{data_url}" width="200" height="200" style="opacity:0.4;filter:alpha(opacity=40);" alt="cat gif">',
    unsafe_allow_html=True,
)
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]


def save_current_history():
    currentUser = csu.getCurrentUser()
    timestamp = str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
    jsonSavePath = Path("data") / Path("saved_conversations") / f"{currentUser.username}_{timestamp}.json"
    if jsonSavePath is not None:
        with open(jsonSavePath, "w") as write:
            json.dump(st.session_state.messages, write)


# Function for generating llm response.


def generate_cloud_llm_response_baseversion(prompt_input: str):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"

    global temperature, top_p, max_length, llm
    output = replicate.run(llm,
                           input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                  "temperature": temperature, "top_p": top_p, "max_length": max_length,
                                  "repetition_penalty": 1})
    return output, False


def generate_local_llm_response_dynabicModel(prompt_input: str, add_to_history: True):
    response, isfullConversationalType = LOCAL_CHATBOT_MODEL.ask_question(prompt_input, add_to_history=add_to_history)
    return response, isfullConversationalType


# TODO in the next versions:
def parseFunctionCalling(output: str):
    if "st.write" in output:
        st.write("YES")


def collapse_sidebar():
    st.session_state.sidebar_state = 'collapsed'
    st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state)

def setup_model_and_keys():
    global replicate_api
    global temperature, top_p, max_length, llm
    global showREPLICATE_details

    # Setup the model and parameters controllers
    with st.sidebar:

        st.title("Our Dynabic chatbot powered by 🦙💬")

        st.button('Clear Chat History', on_click=clear_chat_history)
        st.button('Save Chat', on_click=save_current_history)
        st.button('Collapse', on_click=collapse_sidebar)

        if USE_BASE_CLOUD_MODEL:
            if debug_model == 0 or USE_BASE_CLOUD_MODEL is False:
                if 'REPLICATE_API_TOKEN' in st.secrets:
                    if showREPLICATE_details:
                        st.success('API key already provided!', icon='✅')

                    replicate_api = st.secrets['REPLICATE_API_TOKEN']
                else:
                    replicate_api = st.text_input('Enter Replicate API token:', type='password')
                    if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
                        st.warning('Please enter your credentials!', icon='⚠️')
                    else:
                        st.success('Proceed to entering your prompt message!', icon='👉')


            else:
                replicate_api = "not_needed"

            os.environ['REPLICATE_API_TOKEN'] = replicate_api

            if showREPLICATE_details:
                st.subheader('Models and parameters')
                selected_model = st.sidebar.selectbox('Choose a Llama3 model', ['Llama3-8B', 'Llama3-70B'],
                                                      key='selected_model')
                if selected_model == 'Llama3-8B':
                    llm = 'meta/meta-llama-3-8b'
                elif selected_model == 'Llama3-70B':
                    llm = 'meta/meta-llama-3-70b'

                temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
                top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
                max_length = st.sidebar.slider('max_length', min_value=32, max_value=4096, value=4096, step=8)
            else:
                llm = 'meta/meta-llama-3-8b'
                temperature = 0.1
                top_p = value = 0.95
                max_length = 4096


FIRST_TIME_DEMOTIMER_CREATION = False
if 'g_DemoTimer' not in st.session_state:
    st.session_state.g_DemoTimer: threading.Timer = None
    FIRST_TIME_DEMOTIMER_CREATION = True
    st.session_state.DEMO_MODE_TRIGGERED = False

def check_triggers():
    if csu.isTriggered(cancel_trigger=False):
        if 'g_DemoTimer' in st.session_state:
            st.session_state.g_DemoTimer.cancel()

def initialize_work_area():
    setup_model_and_keys()

    # Init LLM generated responses - TODO: update assist message here
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant",
                                      "content": "Hi! I will let you know when a problem appears. Meantime you can ask me anything"}]

    if DEMO_MODE and FIRST_TIME_DEMOTIMER_CREATION:
        csu.startDemoTrigger()

        # Use another thread but for now...
        st.session_state.g_DemoTimer = threading.Timer(1.0, check_triggers)
        st.session_state.g_DemoTimer.start()


def _submit_feedback(user_response, emoji=None):
    st.toast(f"Thank you, your feedback was submitted: {user_response}", icon=emoji)
    return user_response.update({"some metadata": 123})


def display_feedback(feedback_key: str, use_emojis: bool, user: userUtils.SecurityOfficer):
    emojis_for_feedback = ["🤠", "🤡", "🤪", "🤲", "☘️"]
    global feedbackCollector

    conversation_context_to_save = st.session_state.messages[-csu.option_conversation_context_to_save_len:]

    if not csu.option_use_trubrics:
        res = streamlit_feedback(
            feedback_type="faces",  # "thumbs",
            optional_text_label="If you are kind, please provide extra information",
            on_submit=_submit_feedback,
            kwargs={"emoji": random.choice(emojis_for_feedback) if use_emojis else None},
            key=feedback_key
            # ,path=jsonSavePath
        )

        # todo: TAKE THE CODE from below if we ever need this method again...
    else:
        res = csu.getFeedbackCollector().st_feedback(
            component="WorkArea",
            feedback_type="faces",
            model="llama3_slightlyfinetuned",
            prompt_id=None,  # see prompts to log prompts and model generations
            open_feedback_label="If you are kind, please provide extra information",
            key=feedback_key,
            user_id=user.username,
            metadata={'conversation_context': conversation_context_to_save}
        )

        if res:
            timestamp = str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
            jsonSavePath = Path("data") / Path("feedback_collected") / f"{user.username}_{timestamp}.json" \
                if csu.option_saveFeedbackAsJSON is True else None

            res["created_on"] = str(res["created_on"])
            # print(res)
            if jsonSavePath is not None:
                with open(jsonSavePath, "w") as write:
                    json.dump(res, write)

    return res


# Parse any function call in the response and returns True if that's the case otherwise return True


def display_chat_history():
    # Display or clear chat messages

    currentUser = csu.getCurrentUser()
    use_emojis = currentUser.emojis is userUtils.Preference_Emojis.USE_EMOJIS

    # Find the last assistant message
    last_assistant_msg_index = None
    num_messages = len(st.session_state.messages)
    for n, message in enumerate(reversed(st.session_state.messages), start=1):
        if message["role"] == "assistant":
            last_assistant_msg_index = num_messages - n
            break

    for n, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                if not USE_BASE_CLOUD_MODEL:
                    res = LOCAL_CHATBOT_MODEL.solveFunctionCalls(message["content"])

        if currentUser.feedbackArea == userUtils.Preference_FeedbackArea.ALLOW_FEEDBACK_ON_HISTORY:
            if message["role"] == "assistant" and n > 1:
                feedback_key = f"feedback_{int(n / 2)}"
                if feedback_key not in st.session_state:
                    st.session_state[feedback_key] = None

                display_feedback(feedback_key, use_emojis, currentUser)
        else:
            if n == last_assistant_msg_index and message["role"] == "assistant":
                feedback_key = f"feedback_{int(n / 2)}"
                display_feedback(feedback_key, use_emojis, currentUser)

from schedule import every, repeat, run_pending

def doDemoScript():
    if st.session_state.DEMO_MODE_STEP == 1:
        st.session_state.messages.append({"role": "user",
                                          "content": "Ok. I'm on it, can you show me a resource utilization graph comparison between a normal session and current situation"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(3)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 2:
        st.session_state.messages.append({"role": "user",
                                          "content": "Show me the logs of the devices grouped by IP which have more than 25% requests over the median of a normal session per. Sort them by count"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(3)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 3:
        st.session_state.messages.append({"role": "user",
                                          "content": "Can you show a sample of GET requests from the top 3 demanding IPs, including their start time, end time? Only show the last 10 logs."})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(3)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 4:
        st.session_state.messages.append({"role": "user",
                                          "content": "Give me a world map of requests by comparing the current data and a known snapshot with bars"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(3)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 5:
        st.session_state.messages.append({"role": "user",
                                          "content": "What could it mean if there are many IPs from different locations sending GET commands in a short time with random queries ?"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(3)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 6:
        st.session_state.messages.append({"role": "user",
                                          "content": "Generate me a python code to insert in a pandas dataframe named Firewalls a new IP 10.20.30.40 as blocked under the name of IoTDevice"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(3)
        st.rerun()



################### ACtive rendering code
initialize_work_area()
display_chat_history()

llm_response_func = generate_cloud_llm_response_baseversion if USE_BASE_CLOUD_MODEL is True else \
    generate_local_llm_response_dynabicModel

# User-provided prompt
if prompt := st.chat_input(disabled=not replicate_api and LOCAL_CHATBOT_MODEL is None):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
need_to_ignore_standalone_question_chain = False
if csu.isTriggered(cancel_trigger=True) and ('DEMO_MODE_TRIGGERED' not in st.session_state or st.session_state.DEMO_MODE_TRIGGERED is False):
    st.session_state.messages.append({"role": "assistant",
                                  "content": "Alert: there seems to be many timeouts and 503 error codes on the IoT Hub. Please investigate! I can help you with this."})

    st.session_state.DEMO_MODE_TRIGGERED = True
    st.session_state.DEMO_MODE_STEP = 1
    st.rerun()

elif st.session_state.messages[-1]["role"] != "assistant":
    # This is the case when the last run didn't succeed and a rerun was called
    if prompt is None:
        prompt = st.session_state.messages[-1]["content"]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if not USE_BASE_CLOUD_MODEL:
                # This is needed since the local model produces the standalone output first (if history exists),
                # and after that produces the output to the question
                need_to_ignore_standalone_question_chain = LOCAL_CHATBOT_MODEL.hasHistoryMessages()

            # TODO: fix second param to work for python code too!
            response, isfullConversationalType = llm_response_func(
                prompt, add_to_history=False) if debug_model == 0 else "dummy debug response"
            if not isfullConversationalType:
                need_to_ignore_standalone_question_chain = False
            placeholder = st.empty()
            full_response = ''

            if need_to_ignore_standalone_question_chain:
                for item in response:
                    pass
                placeholder.markdown("<br>")

            for item in response:
                full_response += item
                placeholder.markdown(full_response)

            # Parse a bit the response
            if not USE_BASE_CLOUD_MODEL:
                res = LOCAL_CHATBOT_MODEL.solveFunctionCalls(full_response)
                if DEMO_MODE and DEMO_MODE_SCRIPT:
                    time.sleep(5)
            # if res is False:
            placeholder.markdown(full_response)

    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
    st.rerun()

elif DEMO_MODE is True and st.session_state.DEMO_MODE_TRIGGERED:
    doDemoScript()



