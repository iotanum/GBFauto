import logging


_log = logging.getLogger(__name__)


# Find ele ment with bs4 and get xpath with this function
async def get_xpath_from_ele(element):
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name
            if 1 == len(siblings)
            else "%s[%d]"
            % (child.name, next(i for i, s in enumerate(siblings, 1) if s is child))
        )
        child = parent
    components.reverse()

    _log.debug(f"Xpath parsed from BS4 element: /{'/'.join(components)}")
    return "/%s" % "/".join(components)


async def keys_exists(element, *keys, resp_url=None):
    """
    Check if *keys (nested) exists in `element` (dict).
    """

    if not isinstance(element, dict):
        raise AttributeError("keys_exists() expects dict as first argument.")
    if len(keys) == 0:
        raise AttributeError("keys_exists() expects at least two arguments, one given.")

    _element = element
    for key in keys:
        try:
            _element = _element[key]

        except KeyError:
            _log.debug(
                f"Key {keys} not found in resp {resp_url if resp_url else element}"
            )
            return False

    _log.debug(f"Key {keys} found in resp {resp_url if resp_url else element}")
    return _element


async def get_response_body(resp):
    _log.debug(f"Getting response body from {resp.url}..")
    return await resp.json()
