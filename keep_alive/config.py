APP_LOGGER_NAME = "discord-online"
SERVICE_NAME = "discord-online"
PACKAGE_MODULE = "keep_alive"

DEFAULT_INTERVAL = 200
DEFAULT_METHOD = "mouse"
DEFAULT_CRON = "* * * * *"
MIN_INTERVAL = 10
WARN_INTERVAL = 290
LOG_TAIL_LINES = 20

METHOD_CHOICES = ("mouse", "keyboard", "combined")

CRON_PRESETS = {
    "always": "* * * * *",
    "comercial": "* 8-18 * * 1-5",
    "business": "* 8-18 * * 1-5",
    "noturno": "* 22-23,0-5 * * *",
    "night": "* 22-23,0-5 * * *",
    "weekdays": "* 8-20 * * 1-5",
    "weekend": "* 10-22 * * 0,6",
    "fds": "* 10-22 * * 0,6",
    "manha": "* 6-12 * * *",
    "morning": "* 6-12 * * *",
    "tarde": "* 12-18 * * *",
    "afternoon": "* 12-18 * * *",
}
