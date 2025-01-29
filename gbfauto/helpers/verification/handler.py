import re
import logging
import asyncio

from ultralytics import YOLO

from gbfauto.common.utils import get_xpath_from_ele, get_response_body


_log = logging.getLogger(__name__)


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
        self.utils = self.bot.utils

    async def handler(self):
        retries = 5
        for _ in range(retries):
            await self.screenshot_verification_img()

            _log.info(f"Try {_ + 1} of {retries}.")
            prediction = await self.predict_captcha_from_element()
            await self.send_captcha_answer(prediction)

            if await self.is_successful_verification():
                break
            _log.info("Prediction was incorrect. Retrying...")
            await asyncio.sleep(5)

    async def is_successful_verification(self):
        resp_regex = re.compile(".*\/c\/a\?.*")
        _log.debug("Waiting to see if prediction was correct...")
        async with self.bot.page.expect_response(resp_regex) as resp:
            response = await resp.value
            r_body = await get_response_body(response)

            if "is_correct" in r_body.keys():
                if not r_body["is_correct"]:
                    return False

        return True

    async def screenshot_verification_img(self):
        """
        Check if a verification popup is displayed.

        Returns:
            The verification popup element or False if not found.
        """
        _log.debug("Taking screenshot of verification image...")
        popup_body_ele = await self.utils.bs(find=("div", {"class": "prt-popup-body"}))
        xpath = await get_xpath_from_ele(popup_body_ele)
        img_xpath = f"{xpath}//img"
        locator = self.bot.page.locator(f"xpath={img_xpath}")
        await locator.wait_for()
        await locator.screenshot(path="verification.png")
        _log.debug("Screenshot taken.")

    @staticmethod
    async def get_captcha_model():
        """
        Get the captcha model.

        Returns:
            The captcha model.
        """
        model_path = "captcha_model/model.pt"
        model = YOLO(model_path)
        return model

    @staticmethod
    async def predict_captcha(model, image):
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
        return result

    async def predict_captcha_from_element(self):
        """
        Predict the captcha from a verification element.

        Returns:
            The captcha prediction.
        """
        model = await self.get_captcha_model()
        image = "./verification.png"

        result = await self.predict_captcha(model, image)
        _log.info(f"Captcha prediction: {result}")
        return result

    async def send_captcha_answer(self, prediction):
        """
        Send the captcha answer.

        Args:
            prediction: The captcha prediction.
        """

        # Enter the prediction in the box
        _log.debug(f"Entering '{prediction}' captcha answer...")
        text_entry_element = await self.utils.bs(
            find=("textarea", {"class": "frm-message"})
        )
        text_entry_xpath = await get_xpath_from_ele(text_entry_element)
        text_entry_locator = self.bot.page.locator(text_entry_xpath)
        await text_entry_locator.press_sequentially(prediction, delay=100)

        # Press "send"
        _log.debug(f"Confirming '{prediction}' captcha answer...")
        send_element = await self.utils.bs(find=("div", {"class": "btn-talk-message"}))
        send_xpath = await get_xpath_from_ele(send_element)
        await self.bot.page.locator(f"{send_xpath}").click()
