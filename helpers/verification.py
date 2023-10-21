import io
import time

from PIL import Image
from ultralytics import YOLO
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By


class Verification:
    """
    Class for handling verification tasks.
    """

    def __init__(self, bot):
        """
        Initialize the Verification class.

        Args:
            bot: The bot object.
        """
        self.bot = bot
        self.driver = bot.driver

    def is_verification_popup(self):
        """
        Check if a verification popup is displayed.

        Returns:
            The verification popup element or False if not found.
        """
        parser = bs(self.driver.page_source, "lxml")
        popup_ele = parser.find("div", {"class": "prt-popup-header"})

        if popup_ele:
            if "verification" in popup_ele.text.lower():
                popup_body_ele = parser.find("div", {"class": "prt-popup-body"})
                xpath = self.bot.handle.get_xpath_from_ele(popup_body_ele)

                while True:
                    ele = self.driver.find_element("xpath", f"{xpath}//img")
                    if ele.is_displayed():
                        time.sleep(3)
                        return ele

        return False

    @staticmethod
    def crop_verification_image(verification_img_element, page_picture):
        """
        Crop the verification image.

        Args:
            verification_img_element: The verification image element.
            page_picture: The full page picture.

        Returns:
            The cropped verification image.
        """
        full_page_img = Image.open(io.BytesIO(page_picture))

        location = verification_img_element.location
        x, y = location["x"], location["y"]

        dimensions = verification_img_element.size
        width, height = dimensions["width"], dimensions["height"]

        cropped_img = full_page_img.crop((x, y, x + width, y + height))
        cropped_img.save("verification.png")
        return cropped_img

    @staticmethod
    def get_captcha_model():
        """
        Get the captcha model.

        Returns:
            The captcha model.
        """
        model_path = "model/model.pt"
        model = YOLO(model_path)
        return model

    @staticmethod
    def predict_captcha(model, image):
        """
        Predict the captcha.

        Args:
            model: The captcha model.
            image: The captcha image.

        Returns:
            The captcha prediction.
        """
        predictions = model.predict(image, save_txt=None)

        to_sort = []
        total_confidence = 0
        total_predictions = 0

        # parse predictions
        for idx, prediction in enumerate(predictions[0].boxes.xywhn):
            cls = int(predictions[0].boxes.cls[idx].item())
            cls_name = predictions[0].names[cls]

            # position of the bounding box in the image
            x = prediction[0].item()
            to_sort.append((x, cls_name))
            total_confidence += predictions[0].boxes.conf[idx].item()
            total_predictions += 1

        # sort by x position
        to_sort.sort(key=lambda x: x[0])
        # parse to string by class name
        result = "".join([x[1] for x in to_sort])
        print("Captcha prediction:", result)
        return result

    def predict_captcha_from_element(self, verification_element):
        """
        Predict the captcha from a verification element.

        Args:
            verification_element: The verification element.

        Returns:
            The captcha prediction.
        """
        model = self.get_captcha_model()
        page_pic = self.driver.get_screenshot_as_png()

        cropped_img = self.crop_verification_image(verification_element, page_pic)
        result = self.predict_captcha(model, cropped_img)
        return result

    def send_captcha_answer(self, prediction):
        """
        Send the captcha answer.

        Args:
            prediction: The captcha prediction.
        """
        text_box = self.driver.find_element(By.CLASS_NAME, "frm-message")
        text_box.send_keys(prediction)
        self.driver.find_element(By.CLASS_NAME, "btn-talk-message").click()
