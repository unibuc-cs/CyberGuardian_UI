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
from typing import Tuple, List, Any, Dict, Union
import os

import projsecrets
from projsecrets import project_path, TOKEN_CODE_EXEC_CONFIRM, HOOK_FUNC_NAME_TOKEN

# This is the UI part of the code with different functions to call to show visualizations
dynabicFunctionsUIModule = importlib.import_module("dynabicagenttools")

import os
from demoSupport import UseCase, USE_CASE, check_demo_use_case

if csu.option_use_trubrics:
    from trubrics.integrations.streamlit import FeedbackCollector

# This is a paid-like service to capture metrics, very good but restricted...
# We implemented both variants

st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="Hello", page_icon=":rocket:")

cwd = os.getcwd()
#print(f"Current working dir: {cwd}")

USE_BASE_CLOUD_MODEL = False
if "LocalChatBotModel" in st.session_state:
    # This is resetting everything so reset the session state except the model
    LOCAL_CHATBOT_MODEL = st.session_state.LocalChatBotModel
    #
    # st.session_state.clear()
    # st.session_state.LocalChatBotModel = LOCAL_CHATBOT_MODEL
    #
else:
    LOCAL_CHATBOT_MODEL = csu.getLocalChatBotModelInstance() if USE_BASE_CLOUD_MODEL is False else None
    st.session_state.LocalChatBotModel = LOCAL_CHATBOT_MODEL

replicate_api = None
showREPLICATE_details = False

SLEEP_TIME_BETWEEN_QUESTIONS = 5

debug = 1 if "DEMO_MODE_NOLOGIN" in os.environ else 0
debug_model = 0
if debug == 0:  # Require signin if not logged in
    if not csu.logged_in():
        st.warning("You need to login")
        st.stop()

    csu.showLoggedUserSidebar()

check_demo_use_case() # Could switch at runtime
DEMO_MODE = (USE_BASE_CLOUD_MODEL is False) and (USE_CASE != UseCase.Default)
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

#print(os.getcwd())
file_ = open(os.path.join(projsecrets.project_path_UI_folder, "localdata/characters/man.png"), "rb")
contents = file_.read()
data_url = base64.b64encode(contents).decode("utf-8")
file_.close()

st.sidebar.markdown(
    f'<img src="Data:image/gif;base64,{data_url}" width="200" height="200" style="opacity:0.4;filter:alpha(opacity=40);" alt="cat gif">',
    unsafe_allow_html=True,
)
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]


def save_current_history():
    currentUser = csu.getCurrentUser()
    timestamp = str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
    jsonSavePath = Path(projsecrets.project_path_UI_folder) / Path("Data") / Path("saved_conversations") / f"{currentUser.username}_{timestamp}.json"
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



def history_update_cloud_llm(old_message: str, new_message: str) -> bool:
    assert False, "not implemented"

def history_update_local_llm(old_message: str, new_message: str) -> bool:
    return LOCAL_CHATBOT_MODEL.updateHistory(old_message, new_message)


def generate_local_llm_response_dynabicModel(prompt_input: str, add_to_history: True, use_history: True):
    response, isfullConversationalType, source_code_tool, source_code_ui, tool_code_needs_confirm = LOCAL_CHATBOT_MODEL.ask_question(prompt_input,
                                                                          add_to_history=add_to_history,
                                                                          use_history=use_history)
    return response, isfullConversationalType, source_code_tool, source_code_ui, tool_code_needs_confirm


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
    st.session_state.DEBUG_SKIP_TO_STEP = None # 4 # None # Skip to a specific step in the demo
    st.session_state.DEBUG_SKIP_JUMP_TO_NEXT = None # 6  # None # Jump to this step after the previous skip step

def check_triggers():
    if csu.isTriggered(cancel_trigger=False):
        if 'g_DemoTimer' in st.session_state:
            st.session_state.g_DemoTimer.cancel()

def initialize_work_area():
    setup_model_and_keys()

    # Init LLM generated responses - TODO: update assist message here
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant",
                                      "content": "Hi! I will let you know when a problem appears. Meantime you can ask me anything",
                                        "source_code_tool": None,
                                    "source_code_ui": None}]

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
            jsonSavePath = Path(projsecrets.project_path_UI_folder) / Path("localdata") / Path("feedback_collected") / f"{user.username}_{timestamp}.json" \
                if csu.option_saveFeedbackAsJSON is True else None

            res["created_on"] = str(res["created_on"])
            # print(res)
            if jsonSavePath is not None:
                with open(jsonSavePath, "w") as write:
                    json.dump(res, write)

    return res


def remove_double_quota(input_str: str) -> str:
    if input_str is None:
        return None
    if input_str[0] == '"' and input_str[-1] == '"':
        return input_str[1:-1]
    if input_str[0] == "'" and input_str[-1] != "'":
        return input_str[1:-1]

    return input_str


# Parse the function call from the UI code
def process_python_code_ui_func_call(python_code_ui: str) -> Tuple[Union[str, None], Union[None, List[Any]]]:
    # Remove the leading and trailing spaces
    python_code_ui = python_code_ui.strip()

    # Find the function name
    idx_func_name = python_code_ui.find("FUNC")
    # If no FUNC return None
    if idx_func_name == -1:
        return None, None

    # Skip the FUNC and the space
    idx_func_name += len("FUNC") + 1

    # Find the parameters
    idx_params_token = python_code_ui.find("PARAMS")
    func_name = remove_double_quota(python_code_ui[idx_func_name:idx_params_token].strip())
    idx_params_name = idx_params_token + len("PARAMS") + 1

    # Check if the params are in a list format and remove the leading and trailing spaces, double quotes
    assert python_code_ui[idx_params_name] == "[" and python_code_ui[-1] == "]", "Check if the params are in a list"
    params = python_code_ui[idx_params_name + 1:-1].split(',')
    params = [remove_double_quota(p.strip()) for p in params]

    return func_name, params

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
        with (((st.chat_message(message["role"])))):
            st.write(message["content"])
            if message["role"] == "assistant":
                if USE_BASE_CLOUD_MODEL:
                    continue

                # Display the source code if suggested by the LLM
                python_code_tool = message.get("source_code_tool", None)
                if python_code_tool is not None and python_code_tool != "":
                    st.code(python_code_tool, language="python")

                # Display the confirmation result if any
                if "source_code_ui_confirm_msg" in message:
                    print("The confirmation message to render is: ", message["source_code_ui_confirm_msg"])
                    st.markdown(message["source_code_ui_confirm_msg"])

                # Call the function if the code is generated by the tool on front or back end
                python_code_ui = message.get("source_code_ui", None)
                if python_code_ui is not None and python_code_ui != "":
                    # Get the function name and parameters from string
                    func_name, params = process_python_code_ui_func_call(python_code_ui)

                    # Get the function to call from the module
                    func_to_call = getattr(dynabicFunctionsUIModule, func_name)

                    # If no confirmation needed to execute, then run the code
                    if "tool_code_needs_confirm" not in message or message["tool_code_needs_confirm"] is False:
                        res = func_to_call(*params)
                    else:
                        # Otherwise, show the code and ask for confirmation
                        # Present a confirmation button for the code to be run
                        st.write("The code below is generated by the tool. Please confirm if you want to run it.")
                        if st.button("Confirm"):
                            # If the user confirms, then run the code
                            python_tool_code = message.get("source_code_tool", None)
                            assert python_tool_code, "No tool code to run!!!"  # This should never happen

                            # Get the hook function to run the code
                            python_tool_code_hook = getattr(dynabicFunctionsUIModule, HOOK_FUNC_NAME_TOKEN)
                            assert python_tool_code_hook, "No hook function to run the code!!!"  # This should never happen
                            res = python_tool_code_hook(None, python_tool_code)#, {TOKEN_CODE_EXEC_CONFIRM: True})

                            # If some additional code with func call is returned, then run it
                            if res is not None and type(res) is str:
                                exec_code_confirm_result = res.strip()
                                additional_func_name, additional_call_params = process_python_code_ui_func_call(res)
                                if additional_func_name is not None:
                                    additional_func = getattr(dynabicFunctionsUIModule, additional_func_name)
                                    exec_code_confirm_result = additional_func(*additional_call_params)
                                    message["source_code_ui"] = None # Update the UI code to run  |||| or res ???

                                print(f"Confirmation call result: {exec_code_confirm_result}")
                                message["source_code_ui_confirm_msg"] = f"### :green[{exec_code_confirm_result}]"

                            # Set the flag to False so the code is not run again and confirm button is not shown
                            message["tool_code_needs_confirm"] = False

                            st.rerun()





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

######## DEMO STUFF


## Case 1: smart home
def demo_trigger_msg_SmartHome():
    st.session_state.messages.append({"role": "assistant",
                                      "content": "Alert: there seems to be many timeouts and 503 error codes on the IoT Hub. Please investigate! I can help you with this."})

def doDemoScript_SmartHome():
    if st.session_state.DEBUG_SKIP_TO_STEP is not None:
        st.session_state.DEMO_MODE_STEP = st.session_state.DEBUG_SKIP_TO_STEP
        st.session_state.DEBUG_SKIP_TO_STEP = None

    if st.session_state.DEMO_MODE_STEP == 1:
        st.session_state.messages.append({"role": "user",
                                          "content": "Ok. I'm on it, can you show me a resource utilization graph comparison between a normal session and current situation"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 2:
        st.session_state.messages.append({"role": "user",
                                          "content": "Show me the logs of the devices grouped by IP which have more than 25% requests over the median of a normal session per. Sort them by count"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 3:
        st.session_state.messages.append({"role": "user",
                                          "content": "Can you show a sample of GET requests from the top 3 demanding IPs, including their start time, end time? Only show the last 10 logs."})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 4:
        st.session_state.messages.append({"role": "user",
                                          "content": "Give me a world map of requests by comparing the current Data and a known snapshot with bars"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 5:
        st.session_state.messages.append({"role": "user",
                                          "content": "What could it mean if there are many IPs from different locations sending GET commands in a short time with random queries ?"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 6:
        st.session_state.messages.append({"role": "user",
                                          "content": "Generate and execute a python code to insert in the Firewall dataset these top IPs excepting 130.112.80.168 which seems like a legit one."})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()


## Case 2: Hospital IT

def demo_trigger_msg_Hospital():
    st.session_state.messages.append({"role": "assistant",
                                      "content": "Alert: there are many issues opened in the ticketing system suggesting "
                                                 "that that doctors can't access the patients' DICOM and X-Ray records. "
                                                 "Please investigate! I can help you with this."})

    st.session_state.DEMO_MODE_STEP = 1 # Reset the step

def doDemoScript_Hospital():
    if st.session_state.DEBUG_SKIP_TO_STEP is not None:
        st.session_state.DEMO_MODE_STEP = st.session_state.DEBUG_SKIP_TO_STEP
        st.session_state.DEBUG_SKIP_TO_STEP = None

    if st.session_state.DEMO_MODE_STEP == 1:
        st.session_state.messages.append({"role": "user",
                                          "content": "What are the IPs of the servers hosting the DICOM "
                                                     "and X-Ray records? Can you show me a graph "
                                                     "of their resource utilization over the last 24 hours?"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 2:
        # st.session_state.messages.append({"role": "user",
        #                                   "content": "Can you show the logs of internal servers handling these services "
        #                                              "grouped by IP which have more than 35% requests over "
        #                                              "the median of a normal session per. Sort them by count"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 3:
        st.session_state.messages.append({"role": "user",
                                          "content": "Give me a map with locations where these requests come from by comparing the current "
                                                     "requests and a normal day usage, using bars and colors"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 4:
        st.session_state.messages.append({"role": "user",
                                          "content": "Can you show a sample of GET requests from the top 10 demanding IPs, highlighting the first 4?"
                                                     " Include their IDs, locations, and number of requests."})
        st.session_state.DEMO_MODE_STEP += 1

        if st.session_state.DEBUG_SKIP_JUMP_TO_NEXT:
            st.session_state.DEMO_MODE_STEP = st.session_state.DEBUG_SKIP_JUMP_TO_NEXT
            st.session_state.DEBUG_SKIP_JUMP_TO_NEXT = None

        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()

    elif st.session_state.DEMO_MODE_STEP == 5:
        st.session_state.messages.append({"role": "user",
                                          "content": "Can it be an attack if several servers receive too many queries from different IPs at random locations in a very short time window?"})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
    elif st.session_state.DEMO_MODE_STEP == 6:
        st.session_state.messages.append({"role": "user",
                                          "content": "Generate and execute a python code to insert in the Firewall dataset these top IPs excepting 130.112.80.168 which seems like a legit one."})
        st.session_state.DEMO_MODE_STEP += 1
        time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)
        st.rerun()
        ##########################################


# Switch between the use cases
DEMO_TRIGGER_MSG_FUNC = None
DEMO_TRIGGER_MSG_FOLLOWUP = None
if USE_CASE == UseCase.SmartHome:
    DEMO_TRIGGER_MSG_FUNC = demo_trigger_msg_SmartHome
    DEMO_TRIGGER_MSG_FOLLOWUP = doDemoScript_SmartHome
elif USE_CASE == UseCase.Hospital:
    DEMO_TRIGGER_MSG_FUNC = demo_trigger_msg_Hospital
    DEMO_TRIGGER_MSG_FOLLOWUP = doDemoScript_Hospital
else:
    DEMO_TRIGGER_MSG_FUNC = None
    DEMO_TRIGGER_MSG_FOLLOWUP = None

################### ACtive rendering code
initialize_work_area()
display_chat_history()

llm_response_func = generate_cloud_llm_response_baseversion if USE_BASE_CLOUD_MODEL is True else \
    generate_local_llm_response_dynabicModel

ll_history_update_func = history_update_cloud_llm if USE_BASE_CLOUD_MODEL is True else history_update_local_llm

# User-provided prompt
if prompt := st.chat_input(disabled=not replicate_api and LOCAL_CHATBOT_MODEL is None):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)


# Generate a new response if last message is not from assistant
need_to_ignore_standalone_question_chain = False
if csu.isTriggered(cancel_trigger=True) and ('DEMO_MODE_TRIGGERED' not in st.session_state
                                             or st.session_state.DEMO_MODE_TRIGGERED is False):
    assert DEMO_TRIGGER_MSG_FUNC, "DEMO_TRIGGER_MSG_FUNC is not defined"
    DEMO_TRIGGER_MSG_FUNC()

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

            add_to_hist = True 
            use_history = True 
            response_streamer, isfullConversationalType, source_code_tool, source_code_ui, tool_code_needs_confirm = generate_local_llm_response_dynabicModel(
                prompt, add_to_history=add_to_hist, use_history=use_history) if debug_model == 0 else "dummy debug response"
            if not isfullConversationalType:
                need_to_ignore_standalone_question_chain = False
            placeholder = st.empty()
            full_response = ''

            if need_to_ignore_standalone_question_chain:
                for item in response_streamer:
                    pass
                placeholder.markdown("<br>")

            for item in response_streamer:
                full_response += item
                placeholder.markdown(full_response)


            # Parse a bit the response
            if not USE_BASE_CLOUD_MODEL:
                # res = LOCAL_CHATBOT_MODEL.solveFunctionCalls(full_response, do_history_update=add_to_hist)

                if DEMO_MODE and DEMO_MODE_SCRIPT:
                    time.sleep(SLEEP_TIME_BETWEEN_QUESTIONS)

            # if res is False:
            placeholder.markdown(full_response)

    message = {"role": "assistant",
               "content": full_response,
               "source_code_tool": source_code_tool,
               "source_code_ui": source_code_ui,
               "tool_code_needs_confirm": tool_code_needs_confirm}

    st.session_state.messages.append(message)
    st.rerun()

elif DEMO_MODE is True and st.session_state.DEMO_MODE_TRIGGERED:
    DEMO_TRIGGER_MSG_FOLLOWUP()



