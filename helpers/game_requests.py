import json

from selenium.common.exceptions import WebDriverException


class GbfRequests:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver

    def get_logs(self):
        logs_raw = self.driver.get_log("performance")
        logs = [json.loads(lr["message"])["message"] for lr in logs_raw]

        return logs

    def get_resp_body(self, request_id):
        try:
            resp_body = self.driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id}
            )
            resp_body_dict = json.loads(resp_body["body"])
            return resp_body_dict
        except WebDriverException:
            return None

    def log_filter(self, log):
        return log["method"] == "Network.responseReceived"

    def find_request(self, request_uri, return_uri=False):
        request_id = None

        logs = self.get_logs()
        for log in filter(self.log_filter, logs):
            # currently only need to find responses
            # even tho I have multiple filters
            request_id = log["params"]["requestId"]
            resp_url = log["params"]["response"]["url"]
            if request_uri in resp_url:
                request_id = request_id
                if return_uri:
                    return resp_url

                return request_id

    # attack request, which request url has 'attack_results' or smth in it
    def find_attack_btn_response(self):
        attack_request = "normal_attack_result"
        request_id = self.find_request(attack_request)
        return request_id

    # contains information of a battle start situation
    def find_battle_start_response(self):
        battle_start = "start.json"
        request_id = self.find_request(battle_start)

        return request_id

    def find_generic_request(
        self, uri_contains: str, return_uri: bool = False
    ):
        request_id = self.find_request(uri_contains, return_uri=return_uri)
        if request_id:
            return request_id
