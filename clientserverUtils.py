import streamlit as st

import databaseUtils
from userUtils import SecurityOfficer
from userUtils import SecurityOfficer
import userUtils
from databaseUtils import CredentialsDB
import pandas as pd
from typing import Union
from timeit import default_timer

RELATIVE_PATH_TO_LOCAL_LLM_TRAINED = "../dynabicChatbot"

import sys
import os
sys.path.append(RELATIVE_PATH_TO_LOCAL_LLM_TRAINED)

import QuestionAndAnswerUtils
from QuestionAndAnswerUtils import *


# Which platform for feedback retention, either trubrics or manual processing
option_use_trubrics = True

if option_use_trubrics:
    from trubrics.integrations.streamlit import FeedbackCollector
    g_feedbackCollector: FeedbackCollector = None

option_saveFeedbackAsJSON: bool = True

# The maximum number of responses to hold when saving a feedback. 4 means last 2 for user 2 for AI
option_conversation_context_to_save_len: int = 4

TRIGGER_TIMER_STARTED_TIME = None
TRIGGER_TIMER_ENDED_TIME = None
TIME_UNTIL_TRIGGER_TIMER = 2.0 # 2 seconds

def startDemoTrigger():
    global TRIGGER_TIMER_STARTED_TIME
    global TRIGGER_TIMER_ENDED_TIME

    TRIGGER_TIMER_STARTED_TIME = default_timer()
    TRIGGER_TIMER_ENDED_TIME = default_timer() + TIME_UNTIL_TRIGGER_TIMER

def isTriggered(cancel_trigger:bool)->bool:
    global TRIGGER_TIMER_STARTED_TIME
    global TRIGGER_TIMER_ENDED_TIME

    if TRIGGER_TIMER_ENDED_TIME is None or TRIGGER_TIMER_STARTED_TIME is None:
        return False
    res = (default_timer() > TRIGGER_TIMER_ENDED_TIME)
    if res and cancel_trigger:
        TRIGGER_TIMER_STARTED_TIME = TRIGGER_TIMER_ENDED_TIME = None
    return True

def getFeedbackCollector() -> Union[FeedbackCollector, None]:
    global g_feedbackCollector
    if g_feedbackCollector is None and option_use_trubrics:
        g_feedbackCollector = FeedbackCollector(
            project="DynabicChatbot",
            email=st.secrets.TRUBRICS_EMAIL,
            password=st.secrets.TRUBRICS_PASSWORD,
        )

        if g_feedbackCollector is None:
            use_trubrics = False
            RegisterError("Can't use proper feedback collector from trubrics. Please try again or investigate")

    return g_feedbackCollector
#####

g_credentialsDB: CredentialsDB = None

g_securityChatBotLocal = None

def getLocalChatBotModelInstance():
    global g_securityChatBotLocal
    if g_securityChatBotLocal is None:

        # Need to change the directory then revert back since ther model needs to load some vector data for RAG stored locally
        # but relative to the model's path!
        import os
        cwd = os.getcwd()
        os.chdir(RELATIVE_PATH_TO_LOCAL_LLM_TRAINED)

        g_securityChatBotLocal = QuestionAndAnsweringCustomLlama3(
            QuestionRewritingPrompt=QuestionAndAnsweringCustomLlama3.QUESTION_REWRITING_TYPE.QUESTION_REWRITING_DEFAULT,
            QuestionAnsweringPrompt=QuestionAndAnsweringCustomLlama3.SECURITY_PROMPT_TYPE.PROMPT_TYPE_SECURITY_OFFICER_WITH_RAG_MEMORY_NOSOURCES,
            ModelType=QuestionAndAnsweringCustomLlama3.LLAMA2_VERSION_TYPE.LLAMA3_8B_chat,
            debug=False, streamingOnAnotherThread=True, demoMode=False)

        # Changing back here
        os.chdir(cwd)

    return g_securityChatBotLocal


def logged_in() -> bool:
    if g_credentialsDB is None:
        checkCreateCredentialsDB()
    return g_credentialsDB.isLoggedIn()

def getCurrentUser() -> SecurityOfficer:
    if g_credentialsDB is None:
        checkCreateCredentialsDB()

    if not logged_in(): # I hope this is the debug mode :) should check maybe in the future to be sure
        g_credentialsDB.logDefaultUser()

    return g_credentialsDB.getCurrentUser()

def logout()-> bool:
    res = st.session_state.cdb.logout()
    st.rerun()
    return res

# Returns true if valid credentials are valid and login
def tryLogin(userName: str, password: str) -> bool:
    # Check if user and passwords are ok. If they do mark as logged in.
    return g_credentialsDB.tryLogin(userName, password)

# Clear and save
def RegisterError(msg : str):
    st.markdown(f"## <span style='color:red'>{msg}</span>", unsafe_allow_html=True)
    #st.write("## " + msg)

def ShowTODO(msg : str):
    st.markdown(f"## <span style='color:green'>{msg}</span>", unsafe_allow_html=True)
    #st.write("## " + msg)

def checkCreateCredentialsDB():
    global g_credentialsDB
    st.session_state.cdb = CredentialsDB()
    st.session_state.cdb.initialize()
    g_credentialsDB = st.session_state.cdb

def getCachedImgPathForUsername(username: str):
    res = f"data/{username}_cachedProfilePic.png"
    return res

def register_credentials(newUser: SecurityOfficer):

    bytes_data = newUser.picture.getvalue()
    # Check the type of bytes_data:
    # Should output: <class 'bytes'>
    #st.write(type(bytes_data))

    with open(getCachedImgPathForUsername(newUser.username), "wb") as f:
        f.write(bytes_data)

    g_credentialsDB.insertNewUser(newUser)
    g_credentialsDB.save_credentials_dataset()

def isValidNewUsername(new_username: str) -> bool:
    return not g_credentialsDB.userExists(new_username)


def showLoggedUserSidebar():
    assert logged_in(), "Not logged in"
    user: SecurityOfficer = getCurrentUser()
    user_profile_pic_path = getCachedImgPathForUsername(user.username)
    st.sidebar.markdown(f"## <span style='color:green'>Hi, {user.name}! Let's work.</span>", unsafe_allow_html=True)
    st.sidebar.image(user_profile_pic_path)

    if st.sidebar.button("Logout"):
        logout()

    st.sidebar.write("Some hidden data normally..:")
    st.sidebar.write(f"Expertise declared: {userUtils.getUserExpertiseStr(user.expertise)}")
    st.sidebar.write(f"Tech eval individual score: {user.technical_responses_eval}")
    st.sidebar.write(f"Tech eval in team score: {user.team_work_tech_value}")
    st.sidebar.write(f"How easy you can be tricked: {min(1.0, user.can_be_tricked_out_factor)}")
    st.sidebar.write(f"Teamwork {user.correct_teamwork}")
    st.sidebar.write(f"How likely you may cause intentional damage: {user.intentional_damage_factor}")
    st.sidebar.write(f"Your motivation factor: {user.motivation_factor}")


