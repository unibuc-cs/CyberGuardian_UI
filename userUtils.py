import datetime
from enum import IntEnum
from typing import Dict, List, Union

class SecurityOfficerExpertise(IntEnum):
    BEGINNER = 0
    MIDDLE = 1
    ADVANCED = 2

class ResonsePreferences(IntEnum):
    DETAILED = 0
    CONCISE = 1


class Preference_Politely(IntEnum):
    POLITE_PRESENTATION = 0
    FORMAL_PRESENTATION = 1

class Preference_Emojis(IntEnum):
    USE_EMOJIS = 0
    NO_EMOJIS = 1

class Preference_FeedbackArea(IntEnum):
    ALLOW_FEEDBACK_ON_HISTORY = 0
    ALLOW_FEEDBACK_ONLY_ON_LAST_MSG = 1

class SecurityOfficer():
    def __init__(self):
        super().__init__()

        self.loggedin : bool = False

        self.name: str = "defaultUser"
        self.username: str = "defaultUserName"
        self.password: str = "defaultUserPassword"
        self.birthday: datetime.datetime = datetime.datetime.now()

        self.expertise: SecurityOfficerExpertise = SecurityOfficerExpertise.BEGINNER
        self.preference: ResonsePreferences = ResonsePreferences.DETAILED
        self.politely: Preference_Politely = Preference_Politely.POLITE_PRESENTATION
        self.emojis: Preference_Emojis = Preference_Emojis.USE_EMOJIS
        self.feedbackArea: Preference_FeedbackArea = Preference_FeedbackArea.ALLOW_FEEDBACK_ONLY_ON_LAST_MSG

        self.motivation_factor: float = 1.0 # A float between 0-1

        # How easy it can be tricked out to give access to hackers
        # E.g. phishing attack, give password, stick etc.
        # 0-1
        self.can_be_tricked_out_factor: float = 0.0

        # How likely is to attack from inside
        # 0-1
        self.intentional_damage_factor: float = 0.0

        # If 0 - does not report when seeing strange situation from colleagues, 1 - report everything as expected
        self.correct_teamwork: float = 1.0

    def __repr__(self):
        return "".join({f"{key}:{value}\n" for key,value in self.__dict__.items()})

    """
    def login(self, user_settings: Dict):
        for key, value in user_settings.items():
            setattr(self, key, value)
        self.loggedin = True
    """