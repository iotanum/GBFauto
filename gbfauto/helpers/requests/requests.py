class ValidRequests:
    BATTLE_START = "start.json"
    ABILITY_RESULT = "ability_result.json"
    NORMAL_ATTACK = "normal_attack.json"

    @classmethod
    def is_valid(cls, response):
        for attr_name, val in cls.__dict__.items():
            if "__" in attr_name:
                continue
            if str(val) in response.url:
                return val
        return None  # Not a valid response
