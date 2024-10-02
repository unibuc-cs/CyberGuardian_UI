
from enum import Enum
import os
class UseCase(Enum):
    Default = 0
    Hospital = 1
    SmartHome = 2
    SmartCity = 3

# Set the use case by the environment variable
USE_CASE = UseCase.Default

def check_demo_use_case():
    global USE_CASE
    check_env = os.environ.get("DEMO_USE_CASE", None)
    if check_env is not None:
        if "hospital" in os.environ["DEMO_USE_CASE"].lower():
            USE_CASE = UseCase.Hospital
        elif "smart_home" in os.environ["DEMO_USE_CASE"].lower():
            USE_CASE = UseCase.SmartHome
        else:
            assert False, "Unknown use case given!"

check_demo_use_case()
