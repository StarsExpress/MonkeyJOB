"""All paths configurations."""

import os

APP_BASE_PATH = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

IMAGES_FOLDER_PATH = os.path.join(APP_BASE_PATH, "images")
