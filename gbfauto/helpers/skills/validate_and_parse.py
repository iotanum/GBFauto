import logging

_log = logging.getLogger(__name__)

# Define constants
MIN_SEQUENCE_LENGTH = 2
MAX_SEQUENCE_LENGTH = 4
CHARACTER_RANGE = range(1, 6)
SKILLS_FOR_CHARACTERS = {"abcd": range(1, 5), "abcdef": range(1, 7)}

# Define the action mapping dictionary
ACTION_MAPPING = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6}


async def _map_action(action):
    """
    Map characters based on the provided mapping dictionary.

    Args:
        action (str): The action character.

    Returns:
        int: The mapped action.
    """
    return ACTION_MAPPING.get(action)


async def validate_and_parse(sequence) -> tuple:
    """
    Validate the input sequence according to the specified rules.

    Args:
        sequence (str): The input sequence to validate.

    Raises:
        ValueError: If the input sequence does not meet the validation criteria.
    """
    if not sequence:
        raise ValueError("Input is empty.")

    if len(sequence) < MIN_SEQUENCE_LENGTH or len(sequence) > MAX_SEQUENCE_LENGTH:
        raise ValueError("Input length is invalid.")

    char = int(sequence[0])

    if char not in CHARACTER_RANGE:
        raise ValueError(f"Character number is invalid. {char} is not in 1-5 range.")

    available_skills = "abcd" if char in SKILLS_FOR_CHARACTERS["abcd"] else "abcdef"

    action = sequence[1]

    if action not in available_skills:
        raise ValueError(f"2nd step is invalid. {action} is not in {available_skills}")
    else:
        action = await _map_action(action)

    target = None
    refresh = False

    if len(sequence) > 2:
        target_or_refresh = sequence[2].lower()

        try:
            target = int(target_or_refresh)
            if target not in range(1, 5):
                raise ValueError(
                    f"3rd step is invalid. Target is invalid. Must be 1, 2, 3, or 4. Got: {target}"
                )
        except ValueError:
            if target_or_refresh != "r":
                raise ValueError(
                    "3rd step is invalid. Invalid input. Must be a target (1-4) or R."
                )
            else:
                refresh = True

    if len(sequence) > 3:
        if sequence[3].lower() != "r":
            raise ValueError("4th step is invalid. Refresh is invalid. Must be R.")
        else:
            refresh = True

    return char, action, target, refresh
