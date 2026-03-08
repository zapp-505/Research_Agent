import logging
import os
from datetime import datetime

LOG_FILE=f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"

#cwd point to where you ran the script
logs_path=os.path.join(os.getcwd(),"logs",LOG_FILE)
os.makedirs(logs_path,exist_ok=True)

LOG_FILE_PATH=os.path.join(logs_path,LOG_FILE)
#All log messages of current exec will be written into the file at LOG_FILE_PATH.
'''
Level: Set to logging.INFO (or configurable) to capture informational messages and above.
Format: A custom formatter for log messages, including timestamps, log levels, module names, and messages (e.g., "%(asctime)s - %(name)s - %(levelname)s - %(message)s").

you're importing the standard logging module itself (which is imported at the top of logger.py). Since logger.py calls logging.basicConfig() when the module is loaded, it configures the root logger globally for the entire application.
'''
logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
