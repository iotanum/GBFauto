import json


class GbfRequests:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver

    def get_logs(self):
        logs_raw = self.driver.get_log("performance")
        logs = [json.loads(lr["message"])["message"] for lr in logs_raw]

        return logs

    # stinking 95+ chrome version changes
    def log_filter(self, log):
        return (
            log["method"] == "Network.responseReceived"
            or log["method"] == "Network.loadingFinished"
        )

    def find_request(self, request_uri, return_uri=False):
        logs = self.get_logs()
        responses = []
        for log in filter(self.log_filter, logs):
            # currently only need to find responses
            # even tho I have multiple filters
            if log["method"] == "Network.responseReceived":
                request_id = log["params"]["requestId"]
                resp_url = log["params"]["response"]["url"]
                if request_uri in resp_url:
                    # print(resp_url)
                    if return_uri:
                        return resp_url

                    responses.append(request_id)
                    break

        return responses

    def finish_loading_responses(self, request_ids):
        finished_loading = []
        while True:
            print(f"Checking '{request_ids}' if it's loaded.")
            try:
                logs = self.get_logs()

                for log in filter(self.log_filter, logs):
                    if log["method"] == "Network.loadingFinished":
                        loaded_id = log["params"]["requestId"]
                        print(loaded_id)

                        for request_id in request_ids:
                            if request_id in finished_loading:
                                continue

                            if request_id == loaded_id:
                                finished_loading.append(request_id)

                if len(request_ids) == len(finished_loading):
                    return

            # TypeError occures when there's still no request being made
            except TypeError:
                return

    # attack request, which request url has 'attack_results' or smth in it
    def find_attack_btn_response(self):
        attack_request = "normal_attack_result"
        request_ids = self.find_request(attack_request)
        return request_ids

    # contains information of a battle start situation
    def find_battle_start_response(self):
        battle_start = "start.json"
        request_ids = self.find_request(battle_start)

        return request_ids

    def find_generic_request(self, uri_contains: str, return_uri: bool = False):
        request_ids = self.find_request(uri_contains, return_uri=return_uri)

        return request_ids
