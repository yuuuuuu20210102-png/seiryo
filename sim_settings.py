CLASS_NAMES = [
    "11R", "12R", "13R", "14R",
    "15R", "16R", "17R", "18R"
]

DEFAULT_MAX_STEPS = 3000
DEFAULT_PROCESS_STEPS_PER_FRAME = 1
DEFAULT_DISPLAY_INTERVAL_MS = 150

DEFAULT_DOOR_ASSIGNMENT = {
    "11R": "5",
    "12R": "5",
    "13R": "5",
    "14R": "5",
    "15R": "5",
    "16R": "5",
    "17R": "5",
    "18R": "5",
}

DEFAULT_START_STEPS = {
    "11R": 0,
    "12R": 0,
    "13R": 0,
    "14R": 0,
    "15R": 0,
    "16R": 0,
    "17R": 0,
    "18R": 0,
}

SUB1_INPUT_CSV = "data/sub1_cases.csv"
SUB1_OUTPUT_CSV = "output/sub1_results.csv"


def 扉列名(class_name):
    return f"door_{class_name}"


def 開始時刻列名(class_name):
    return f"start_{class_name}"