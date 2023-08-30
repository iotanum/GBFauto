import json

from selenium.common.exceptions import WebDriverException


class GbfRequests:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver

    def get_logs(self):
        logs_raw = self.driver.get_log("performance")
        logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
        filtered = filter(self.log_filter, logs)
        return filtered

    def log_filter(self, log):
        return log["method"] == "Network.responseReceived"

    def find_request(self, request_uri):
        logs = self.get_logs()
        reqs = []

        for log in logs:
            request_id = log["params"]["requestId"]
            resp_url = log["params"]["response"]["url"]

            if request_uri in resp_url:
                reqs.append({"id": request_id, "uri": resp_url})

        return reqs if reqs else None

    def get_resp_body(self, request_id):
        try:
            resp_body = self.driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id}
            )
            resp_body_dict = json.loads(resp_body["body"])
            return resp_body_dict
        except WebDriverException:
            return None
