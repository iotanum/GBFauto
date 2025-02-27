class ValidResponses:
    BATTLE_START = "start.json"
    ABILITY_RESULT = "ability_result.json"
    NORMAL_ATTACK = "normal_attack_result.json"
    PRE_FIGHT_CHECK = "user_action_point"
    CONTENT = "content"
    NORMAL_ITEM_LIST = "normal_item_list"
    USE_NORMAL_ITEM = "use_normal_item"
    QUEST_INFO = "quest/cleared_list"
    SUMMON = "summon_result.json"
    CHECK_MULTI_START = "check_multi_start"

    @classmethod
    async def is_valid(cls, response):
        """
        Checks if the response is valid based on its URL.

        Args:
            response: The response object to check.

        Returns:
            str or None: The valid response type if valid, None otherwise.
        """
        for attr_name, val in cls.__dict__.items():
            if "__" in attr_name:
                continue
            if str(val) in response.url and response.request.resource_type == "xhr":
                return val
        return None  # Not a valid response
