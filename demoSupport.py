
from enum import Enum
import os
class UseCase(Enum):
    Default = 0
    Hospital = 1
    SmartHome = 2
    SmartCity = 3

# Set the use case by the environment variable
USE_CASE = UseCase.Default
if "DEMO_USE_CASE" in os.environ:
    if "hospital" in os.environ["DEMO_USE_CASE"].lower():
        USE_CASE = UseCase.Hospital
    elif "smart_home" in os.environ["DEMO_USE_CASE"].lower():
        USE_CASE = UseCase.SmartHome
    else:
        assert False, "Unknown use case"

