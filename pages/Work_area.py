import random

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


if csu.option_use_trubrics:
    from trubrics.integrations.streamlit import FeedbackCollector

# This is a paid-like service to capture metrics, very good but restricted...
# We implemented both variants


USE_BASE_CLOUD_MODEL = False
LOCAL_CHATBOT_MODEL = csu.getLocalChatBotModelInstance() if USE_BASE_CLOUD_MODEL is False else None
replicate_api = None
showREPLICATE_details = False

debug = 1
debug_model = 0
if debug==0: # Require signin if not logged in
    if not csu.logged_in():
        st.warning("You need to login")
        st.stop()

    csu.showLoggedUserSidebar()

#######################################

if USE_BASE_CLOUD_MODEL:
    import replicate
import os

# Parameter models
temperature = None
top_p = None
max_length = None
llm = None

file_ = open("data/characters/dog.gif", "rb")
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

# Function for generating LLaMA2 response.


def generate_llama2_response_baseversion(prompt_input: str):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"

    global temperature, top_p, max_length, llm
    output = replicate.run(llm,
                           input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                  "temperature":temperature, "top_p":top_p, "max_length":max_length, "repetition_penalty":1})
    return output

def generate_llama2_response_dynabicModel(prompt_input: str):
    response = LOCAL_CHATBOT_MODEL.ask_question(prompt_input)
    return response

# TODO in the next versions:
def parseFunctionCalling(output: str):
    if "st.write" in output:
        st.write("YES")


def setup_model_and_keys():
    global replicate_api
    global temperature, top_p, max_length, llm
    global showREPLICATE_details

    # Setup the model and parameters controllers
    with st.sidebar:

        st.title("Our Dynabic chatbot powered by 🦙💬")

        st.button('Clear Chat History', on_click=clear_chat_history)
        st.button('Save Chat', on_click=save_current_history)

        if USE_BASE_CLOUD_MODEL:
            if debug_model == 0 or USE_BASE_CLOUD_MODEL is False:
                if 'REPLICATE_API_TOKEN' in st.secrets:
                    if showREPLICATE_details:
                        st.success('API key already provided!', icon='✅')

                    replicate_api = st.secrets['REPLICATE_API_TOKEN']
                else:
                    replicate_api = st.text_input('Enter Replicate API token:', type='password')
                    if not (replicate_api.startswith('r8_') and len(replicate_api)==40):
                        st.warning('Please enter your credentials!', icon='⚠️')
                    else:
                        st.success('Proceed to entering your prompt message!', icon='👉')


            else:
                replicate_api = "not_needed"

            os.environ['REPLICATE_API_TOKEN'] = replicate_api

            if showREPLICATE_details:
                st.subheader('Models and parameters')
                selected_model = st.sidebar.selectbox('Choose a Llama2 model', ['Llama2-7B', 'Llama2-13B'], key='selected_model')
                if selected_model == 'Llama2-7B':
                    llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
                elif selected_model == 'Llama2-13B':
                    llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'

                temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
                top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
                max_length = st.sidebar.slider('max_length', min_value=32, max_value=4096, value=4096, step=8)
            else:
                llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
                temperature = 0.1
                top_p = value=0.95
                max_length = 4096

def initialize_work_area():
    setup_model_and_keys()

    # Init LLM generated responses - TODO: update assist message here
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

def _submit_feedback(user_response, emoji=None):
    st.toast(f"Thank you, your feedback was submitted: {user_response}", icon=emoji)
    return user_response.update({"some metadata": 123})

def display_feedback(feedback_key: str, use_emojis: bool, user: userUtils.SecurityOfficer):
    emojis_for_feedback=["🤠", "🤡", "🤪", "🤲", "☘️"]
    global feedbackCollector

    conversation_context_to_save = st.session_state.messages[-csu.option_conversation_context_to_save_len:]

    if not csu.option_use_trubrics:
        res = streamlit_feedback(
            feedback_type="faces",  # "thumbs",
            optional_text_label="If you are kind, please provide extra information",
            on_submit=_submit_feedback,
            kwargs={"emoji":random.choice(emojis_for_feedback) if use_emojis else None},
            key=feedback_key
            #,path=jsonSavePath
        )

        # todo: TAKE THE CODE from below if we ever need this method again...
    else:
        res = csu.getFeedbackCollector().st_feedback(
            component="WorkArea",
            feedback_type="faces",
            model="llama2_slightlyfinetuned",
            prompt_id=None,  # see prompts to log prompts and model generations
            open_feedback_label="If you are kind, please provide extra information",
            key=feedback_key,
            user_id=user.username,
            metadata={'conversation_context':conversation_context_to_save}
        )

        if res:
            timestamp = str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
            jsonSavePath = Path("data") / Path("feedback_collected") / f"{user.username}_{timestamp}.json" \
                if csu.option_saveFeedbackAsJSON is True else None

            res["created_on"] = str(res["created_on"])
            #print(res)
            if jsonSavePath is not None:
                with open(jsonSavePath, "w") as write:
                    json.dump(res, write)

    return res


#Parse any function call in the response and returns True if that's the case otherwise return True
def solveFunctionCalls(full_response: str) -> bool:
    if 'FUNC_CALL' not in full_response:
        return False

    # Identify which function call it is being asked
    # TODO: allow user to inject his own tools
    # TODO: make exception and fail method
    # Parse the parameters in function call
    words_in_func_call = list(full_response.split())
    words_in_func_call = [w.strip() for w in words_in_func_call]
    assert words_in_func_call[0] == 'FUNC_CALL', "First argument should be FUNC_CALL token"
    assert words_in_func_call[2] == 'Params', "Third argument needs to be Params token"
    assert "</s>" in words_in_func_call[-1]
    words_in_func_call[-1] = words_in_func_call[-1].replace("</s>", "")

    # Remove double quotes stuff
    words_in_func_call = [w if w[0] not in ["'", '"'] else w[1:len(w)-1]   for w in words_in_func_call]

    # Second expected as module.func
    mod_name, func_name = words_in_func_call[1].rsplit('.', 1)
    func_params = words_in_func_call[3:]

    # import the module where function is
    mod = importlib.import_module(mod_name)

    # Get the function
    func = getattr(mod, func_name)

    # Call it
    result = func(*func_params)


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
                res = solveFunctionCalls(message["content"])



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

################### ACtive rendering code
initialize_work_area()
display_chat_history()



llama2_response_func = generate_llama2_response_baseversion if USE_BASE_CLOUD_MODEL is True else\
                        generate_llama2_response_dynabicModel

# User-provided prompt
if prompt := st.chat_input(disabled=not replicate_api and LOCAL_CHATBOT_MODEL is None):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = llama2_response_func(prompt) if debug_model == 0 else "dummy debug response"
            placeholder = st.empty()
            full_response = ''

            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            res = solveFunctionCalls(full_response)
            #if res is False:
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
    st.rerun()
