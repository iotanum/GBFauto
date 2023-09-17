class ValidResponses:
    BATTLE_START = "start.json"
    ABILITY_RESULT = "ability_result.json"
    NORMAL_ATTACK = "normal_attack_result.json"
    PRE_FIGHT_CHECK = "user_action_point"
    CONTENT = "content"
    NORMAL_ITEM_LIST = "normal_item_list"
    USE_NORMAL_ITEM = "use_normal_item"
    QUEST_INFO = "quest/cleared_list"

    @classmethod
    async def is_valid(cls, response):
        for k, val in cls.__dict__.items():
            if str(val) in response.url:
                if response.request.resource_type == "xhr":
                    return cls.__dict__[k]
