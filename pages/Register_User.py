import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from userUtils import SecurityOfficer, SecurityOfficerExpertise, ResonsePreferences, Preference_Politely, \
    Preference_Emojis
import clientserverUtils as csu
from validator import validator
import datetime
from enum import IntEnum
from databaseUtils import CredentialsDB
from typing import Union, List, Dict
from streamlit_image_select import image_select

g_uiKeyCounter: int = 0


# Returns the index of the chosen option
def UIUtil_UserResponse(question: str, options: List[str], classtype, initial_index=0) -> int:
    global g_uiKeyCounter
    g_uiKeyCounter += 1
    choice = classtype(question,
                       options=options, index=0, key=g_uiKeyCounter)
    choiceIndex = options.index(choice)
    return choiceIndex


class RegistrationState(IntEnum):
    BASIC_REGISTRATION = 0
    BEHAVIORAL_REGISTRATION = 1
    TECHNICAL_REGISTRATION = 2
    PREFERENCES_REGISTRATION = 3
    FINISHED_REGISTRATION = 4


if 'cdb' not in st.session_state:
    csu.checkCreateCredentialsDB()


def getRegistrationState() -> RegistrationState:
    res = st.session_state.get('REG_STATE', None)
    if res is None:
        st.session_state['REG_STATE'] = RegistrationState.BASIC_REGISTRATION
        st.session_state['InProgRegistration'] = SecurityOfficer()

    return st.session_state['REG_STATE']


def getInProgressRegistrationUser() -> SecurityOfficer:
    return st.session_state['InProgRegistration']


def updateRegistrationState(newRegState: Union[RegistrationState, None]):
    st.session_state['REG_STATE'] = newRegState


def register_user_basic(form_name: str, location: str = 'main') -> bool:
    """
    Creates a register new user widget.
    """
    succeed = False

    if location not in ['main', 'sidebar']:
        raise ValueError("Location must be one of 'main' or 'sidebar'")
    if location == 'main':
        register_user_form = st.form('Basic registration')
    elif location == 'sidebar':
        register_user_form = st.sidebar.form('Basic registration')

    register_user_form.subheader(form_name)
    new_email = register_user_form.text_input('Email', value="")
    new_username = register_user_form.text_input('Username', value="").lower()
    new_name = register_user_form.text_input('Name', value="")
    new_password = register_user_form.text_input('Password', type='password', value="")
    new_password_repeat = register_user_form.text_input('Repeat password', type='password', value="")
    birthday = register_user_form.date_input("Birthday",
                                             value=datetime.date(1986, 9, 3),
                                             max_value=datetime.date.today(),
                                             min_value=datetime.date(1900, 7, 6))

    picture = register_user_form.camera_input("Take a picture of yourself")

    if register_user_form.form_submit_button('Next'):
        if len(new_email) > 0 and len(new_username) > 0 and len(new_name) > 0 and len(new_password) > 0 and (
                picture is not None):
            validSetup = True
            if not validator.validate_username(new_username):
                csu.RegisterError("Invalid username")
                validSetup = False
            if not validator.validate_email(new_email):
                csu.RegisterError("Invalid email")
                validSetup = False
            if not validator.validate_name(new_name):
                csu.RegisterError("Invalid name")
                validSetup = False
            if not validator.validate_birthday(birthday):
                validSetup = False
                csu.RegisterError("Invalid birthday")
            if not picture:
                csu.RegisterError("No picture provided")
                validSetup = False
            if new_password != new_password_repeat:
                csu.RegisterError("Passwords do not match")

            if validSetup:
                if csu.isValidNewUsername(new_username):
                    succeed = True
                    userInProgress = getInProgressRegistrationUser()
                    userInProgress.username = new_username
                    userInProgress.email = new_email
                    userInProgress.birthday = birthday
                    userInProgress.name = new_name
                    userInProgress.password = new_password
                    userInProgress.picture = picture
                else:
                    csu.RegisterError('Username already taken')
            else:
                pass
                # csu.RegisterError('Username already taken')
        else:
            csu.RegisterError('Please fill in Data and take the photo')

    return succeed


def register_user_behavioral(form_name: str, location: str = 'main') -> bool:
    """
    Creates a register new user widget.
    """
    succeed = False

    if location not in ['main', 'sidebar']:
        raise ValueError("Location must be one of 'main' or 'sidebar'")
    if location == 'main':
        register_user_form = st.form('Behavioral profile')
    elif location == 'sidebar':
        register_user_form = st.sidebar.form('Behavioral profile')

    register_user_form.subheader(form_name)

    csu.ShowTODO("TODO SSH: Will tune this set of questions")

    user = getInProgressRegistrationUser()

    # How likely is to attack from inside
    internalDamageChoice = UIUtil_UserResponse(
        question="Would you try to test the reliability of our production systems without a concrete task from your "
                 "team lead? (Hidden: this is the intentional damage factor thing)",
        classtype=register_user_form.radio,
        #options=[":rainbow[Never]", "Just for fun or to test it a bit :movie_camera:", "***Maybe***"]
        options = ["Never", "Just for fun or to test it a bit", "Maybe"]
    )
    if internalDamageChoice == 0:
        user.intentional_damage_factor = 0.0
    elif internalDamageChoice == 1:
        user.intentional_damage_factor = 0.5
    else:
        user.intentional_damage_factor = 1.0

    convinceChoice = UIUtil_UserResponse(classtype=register_user_form.radio,
                                         question="Would you try to convince colleagues to give you their credentials "
                                                  "or send them an external link to open?",
                                         options=['No', 'Yes', 'Maybe'])
    convinceValue = 0.0
    if convinceChoice == 1:
        confidenceValue = 1.0
    elif convinceChoice == 2:
        confidenceValue = 0.5

    convinceChoice_2 = UIUtil_UserResponse(classtype=register_user_form.radio,
                                           question="Would you try to convince a colleague to give details about the "
                                                    "network, infrastructure, or security, that you normally should "
                                                    "not know ?",
                                           options=['No', 'Yes', 'Maybe'])
    convinceValue_2 = 0.0
    if convinceChoice_2 == 1:
        confidenceValue_2 = 1.0
    elif convinceChoice_2 == 2:
        confidenceValue_2 = 0.5

    user.intentional_damage_factor = min(1.0, user.intentional_damage_factor + (convinceValue + convinceValue_2) * 0.5)

    user.correct_teamwork = register_user_form.slider(
        "How likely is to report a colleague who brings in without authorization their own software, "
        "or causes intentional damage? (Hidden: Correct teamwork factor)",
        min_value=1, max_value=10, value=5, step=1) / 10.0

    motivationValue = register_user_form.slider("How motivated are you by your daily job?"
                                                " (Hidden: Motivation factor)",
                                                min_value=1, max_value=10, value=5, step=1) / 10.0

    confidenceChoise = UIUtil_UserResponse(classtype=register_user_form.selectbox,
                                           question="How confident are you on your job?  (Hidden: Motivation factor)",
                                           options=['Very confident', 'Somehow confident', 'Not confident'])
    confidenceValue = 1.0
    if confidenceChoise == 1:
        confidenceValue = 0.5
    elif confidenceChoise == 2:
        confidenceValue = 1.0

    user.motivation_factor = (motivationValue + confidenceValue) / 2.0

    if register_user_form.form_submit_button('Next'):
        succeed = True

    return succeed


from typing import List, Union, Dict


def register_user_technical(form_name: str, location: str = 'main') -> bool:
    """
    Creates a register new user widget.
    """
    succeed = False

    if location not in ['main', 'sidebar']:
        raise ValueError("Location must be one of 'main' or 'sidebar'")
    if location == 'main':
        register_user_form = st.form('Technical evaluation')
    elif location == 'sidebar':
        register_user_form = st.sidebar.form('Technical evaluation')

    register_user_form.subheader(form_name)
    csu.ShowTODO("TODO: an LLM-guided interview with questions based on an uploaded CV,"
                 "previous answers and feedback. Or a dynamic interview with different threads of discussion.")

    user = getInProgressRegistrationUser()

    # Expertise evaluation
    experienceChoice = UIUtil_UserResponse(question="How many years of expertise do you have in cybersecurity?",
                                           classtype=register_user_form.radio,
                                           options=["1-3 years", "3-7 years", "more than 7 years"])
    user.expertise = SecurityOfficerExpertise.BEGINNER
    if experienceChoice == 1:
        user.expertise = SecurityOfficerExpertise.MIDDLE
    elif experienceChoice == 2:
        user.expertise = SecurityOfficerExpertise.ADVANCED

    register_user_form.divider()

    ######################################### Tehnical questions ######################

    register_user_form.write('What is a phishing attack? Check all that apply')
    option_1 = register_user_form.checkbox('An attempt to steal sensitive information, typically in the form of usernames, passwords, credit cards, bank account information in order to utilize or sell the stolen information.', key="11")
    option_2 = register_user_form.checkbox('Using a program that records every keystroke made by a computer user', key="12")
    option_3 = register_user_form.checkbox('Form of a malware attack in which an attacker encrypts the user’s Data, folders, or entire device until a ‘ransom’ fee is paid', key="13")
    option_4 = register_user_form.checkbox('A virus from a USB stick', key="14")

    tech_que_score_1 = 1.0 if option_1 is True and option_2 is False and option_3 is False and option_4 is False else 0.0

    register_user_form.divider()

    register_user_form.write('What is a ransomware attack? Check all that apply')
    option_1 = register_user_form.checkbox(
        'Attackers are sending frequent or large Data from different IPs to consume the server resources', key="21")
    option_2 = register_user_form.checkbox('Using a program that records every keystroke made by a computer user', key="22")
    option_3 = register_user_form.checkbox(
        'Form of malware attack in which an attacker encrypts the user’s Data, folders, or entire device until a ‘ransom’ fee is paid', key="23")
    option_4 = register_user_form.checkbox('A virus from a USB stick', key="24")

    tech_que_score_2 = 1.0 if option_1 is False and option_2 is True and option_3 is False and option_4 is False else 0.0

    register_user_form.divider()

    register_user_form.write('What is a DDoS attack? Check all that apply ')
    option_1 = register_user_form.checkbox(
        'Attackers are sending frequent or large Data from a single IP to consume the server resources', key="31")
    option_2 = register_user_form.checkbox('Using a program that records every keystroke made by a computer user', key="32")
    option_3 = register_user_form.checkbox(
        'Multiple IPs from different locations try to connect and send information to servers or network resources',
        key="33")
    option_4 = register_user_form.checkbox('Form of malware attack in which an attacker encrypts the user’s Data, '
                                           'folders, or entire device until a ‘ransom’ fee is paid', key="34")

    tech_que_score_3 = 1.0 if option_1 is False and option_2 is False and option_3 is True and option_4 is False else 0.0

    user.technical_responses_eval = (tech_que_score_3 + tech_que_score_2 + tech_que_score_1) / 3
    #############################################################

    register_user_form.divider()

    ########## Tech teamwork set of questions ###########
    team_work_1_choice = UIUtil_UserResponse(
        question="Do you respect the best practices in the field suggested by the company, e.g., make regular backups? ",
        options=['Yes', 'Sometimes I know better what to do'],
        classtype=register_user_form.radio)
    team_work_1_value = 1.0 if team_work_1_choice == 0 else 0.0

    register_user_form.divider()

    team_work_2_choice = UIUtil_UserResponse(question="Would you alert your manager when you are not confident in "
                                                      "fixing a critical problem in the required time?",
                                             classtype=register_user_form.radio,
                                             options=['Yes', 'I would try first as much as possible myself'])
    team_work_2_value = 1.0 if team_work_2_choice == 0 else 0.0

    register_user_form.divider()

    team_work_3_choice = UIUtil_UserResponse(question="Would you escalate a problem to another group or "
                                                      "expert colleague when it is not your competence?",
                                             classtype=register_user_form.radio,
                                             options=['Yes', 'I would try first as much as possible myself.'])
    team_work_3_value = 1.0 if team_work_3_choice == 0 else 0.0

    register_user_form.divider()

    user.team_work_tech_value = (team_work_1_value + team_work_2_value + team_work_3_value) / 3

    ###########################   Easy to fool TEST ##################

    fulled_phishing_choice = UIUtil_UserResponse(question="Would you open an external link or program in "
                                                          "an email from colleagues, friends, or family? "
                                                          "(Hidden: how easy is to be fooled)",
                                                 classtype=register_user_form.selectbox,
                                                 options=['I do not know', 'No', 'Maybe'])
    fulled_phishing_value = 1.0
    if fulled_phishing_choice == 1:
        fulled_phishing_value = 0.5
    elif fulled_phishing_choice == 2:
        fulled_phishing_value = 1.0

    register_user_form.divider()

    fulled_externaldevices_choice = UIUtil_UserResponse(question="Would you plug in a personal USB stick in a company's  "
                                                                 "computer or when asked by a colleague?",
                                                        classtype=register_user_form.selectbox,
                                                        options=['No', 'I do not know', 'Maybe'])
    fulled_externaldevices_value = 1.0
    if fulled_externaldevices_choice == 1:
        fulled_externaldevices_value = 0.5
    elif fulled_externaldevices_choice == 2:
        fulled_externaldevices_value = 1.0

    register_user_form.divider()

    sharing_choice = UIUtil_UserResponse(
        question="Would you share internal network security or infrastructure info with friends,"
                 "family, or other people who should not be aware of?",
        classtype=register_user_form.radio,
        options=['No', 'I do not know', 'Maybe'])

    sharing_choice_value = 1.0
    if sharing_choice == 1:
        sharing_choice_value = 0.5
    elif sharing_choice == 2:
        sharing_choice_value = 1.0

    user.can_be_tricked_out_factor = (fulled_externaldevices_value + fulled_phishing_value + sharing_choice_value) * 0.5

    if register_user_form.form_submit_button('Next'):
        succeed = True

    return succeed


def register_user_preferences(form_name: str, location: str = 'main') -> bool:
    """
    Creates a register new user widget.
    """
    csu.ShowTODO("TODO SSH: To tune this set of questions based on the profile")

    succeed = False

    if location not in ['main', 'sidebar']:
        raise ValueError("Location must be one of 'main' or 'sidebar'")
    if location == 'main':
        register_user_form = st.form('User preferences')
    elif location == 'sidebar':
        register_user_form = st.sidebar.form('User preferences')

    register_user_form.subheader(form_name)
    user = getInProgressRegistrationUser()

    user.preference = ResonsePreferences.DETAILED \
        if register_user_form.toggle('Use detailed answers instead of concise', True) is True \
        else ResonsePreferences.CONCISE

    user.emojis = Preference_Emojis.USE_EMOJIS \
        if register_user_form.toggle('Use emojis in answers', True) is True \
        else Preference_Emojis.NO_EMOJIS

    user.politely = Preference_Politely.POLITE_PRESENTATION \
        if register_user_form.toggle('Use polite formulations', True) is True \
        else Preference_Politely.FORMAL_PRESENTATION

    avatarsList = ["Data/characters/woman.png", "Data/characters/man.png", "Data/characters/None.png"]
    img = image_select("Select which avatar you would like between the first two, or the last if you don't want one.", avatarsList)
    user.avatar_choice = img

    if register_user_form.form_submit_button('Next'):
        succeed = True

    return succeed


if csu.logged_in():
    st.write("## Already logged in, logout please to continue!")
    csu.showLoggedUserSidebar()
else:
    if getRegistrationState() == RegistrationState.BASIC_REGISTRATION:
        res = register_user_basic("Basic registration")
        if res:
            updateRegistrationState(RegistrationState.BEHAVIORAL_REGISTRATION)
            st.rerun()
    elif getRegistrationState() == RegistrationState.BEHAVIORAL_REGISTRATION:
        res = register_user_behavioral("Behavioral registration")
        if res:
            updateRegistrationState(RegistrationState.TECHNICAL_REGISTRATION)
            st.rerun()
    elif getRegistrationState() == RegistrationState.TECHNICAL_REGISTRATION:
        res = register_user_technical("Technical registration")
        if res:
            updateRegistrationState(RegistrationState.PREFERENCES_REGISTRATION)
            st.rerun()
    elif getRegistrationState() == RegistrationState.PREFERENCES_REGISTRATION:
        res = register_user_preferences("Preferences registration")
        if res:
            updateRegistrationState(None)
            csu.register_credentials(getInProgressRegistrationUser())
            switch_page("Main Page")
            st.rerun()
