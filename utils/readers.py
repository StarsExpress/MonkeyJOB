import os
from PIL import Image
from configs.paths_config import IMAGES_FOLDER_PATH, RULES_PATHS_DICT


def read_cards_images():
    """
    Read card images from images directory and return a dictionary mapping card names to images.

    Returns:
        dict: dict where keys are card names and values are Image objects.
    """
    images_dict = dict()
    images_names = os.listdir(IMAGES_FOLDER_PATH)

    for img_name in images_names:
        if img_name.endswith(".jpg"):  # Only read jpg files.
            image_path = os.path.join(IMAGES_FOLDER_PATH, img_name)
            images_dict.update(
                {
                    img_name.split(".")[0]: Image.open(image_path)
                }
            )
    return images_dict


def read_rules():
    """
    Read rules of available languages from rules folder.

    Returns:
        dict: dict where keys are language names and values are corresponding rules.
    """
    rules_dict = {}
    for key in RULES_PATHS_DICT.keys():
        with open(RULES_PATHS_DICT[key], "r", encoding="UTF-8") as file:
            rules_dict.update({key: file.read()})
    return rules_dict
