class ValidRequests:
    BATTLE_START = "start.json"
    ABILITY_RESULT = "ability_result.json"
    NORMAL_ATTACK = "normal_attack.json"

    @classmethod
    def is_valid(cls, response):
        return any(str(val) in response for val in cls.__dict__.values())
