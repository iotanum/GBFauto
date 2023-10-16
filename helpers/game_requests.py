import json
import time

from dateutil.parser import parse
from selenium.common.exceptions import WebDriverException


class GbfRequests:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver

    def is_log_new(self, log):
        try:
            date = log["params"]["response"]["headers"]["Date"]
            req_date_parsed = parse(date)
            return req_date_parsed > self.bot.req_start_time
        except KeyError:
            return False

    def log_filter(self, log):
        return (
            log["method"] == "Network.responseReceived"
            and "json" in log["params"]["response"]["mimeType"]
            and self.is_log_new(log)
        )

    def get_logs(self):
        logs_raw = self.driver.get_log("performance")
        logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
        return filter(self.log_filter, logs)

    def find_request(self, req_uris):
        logs = self.get_logs()
        reqs = []

        for log in logs:
            request_id = log["params"]["requestId"]
            resp_url = log["params"]["response"]["url"]

            for req in req_uris:
                if req in resp_url:
                    print(resp_url, "resp_url, find_request")
                    reqs.append({"id": request_id, "uri": resp_url})

        if reqs:
            return reqs

    def get_resp_body(self, req, can_be_empty=False):
        start = time.time()
        timeout = 5

        req_id = req["id"]
        while True:
            try:
                resp_json = self.driver.execute_cdp_cmd(
                    "Network.getResponseBody", {"requestId": req_id}
                )
                return json.loads(resp_json["body"])
            except WebDriverException:
                if can_be_empty:
                    print("Empty response body, returning None.")
                    return

                if time.time() - start > timeout:
                    print("Timeout on getting response body.")
                    return

                uri = req["uri"].split("/")[-1]
                print(f"Ups, didn't load '{uri}'. Retrying...")
                pass
