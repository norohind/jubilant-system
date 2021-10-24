import requests
from EDMCLogging import get_main_logger

logger = get_main_logger()


def authed_request(url: str, method: str = 'get', **kwargs) -> requests.Response:
    """Makes request to any url with valid bearer token"""
    bearer: str = _get_bearer()

    logger.debug(f'Requesting {method.upper()} {url!r}')

    fapiRequest: requests.Response = requests.request(
        method=method,
        url=url,
        headers={'Authorization': f'Bearer {bearer}'},
        **kwargs
    )

    logger.debug(f'Request complete, code {fapiRequest.status_code!r}, len {len(fapiRequest.content)}')

    return fapiRequest


def _get_bearer() -> str:
    """Gets bearer token from capi.demb.design (companion-api project)"""
    bearer_request: requests.Response = requests.get(
        url='https://capi.demb.design/users/2yGDATq_zzfudaQ_8XnFVKtE80gco1q1-2AkSL9gxoI=')

    try:
        bearer: str = bearer_request.json()['access_token']

    except Exception as e:
        logger.exception(f'Unable to parse capi.demb.design answer\nrequested: {bearer_request.url!r}\n'
                         f'code: {bearer_request.status_code!r}\nresponse: {bearer_request.content!r}', exc_info=e)
        raise e

    return bearer


def fdev2people(hex_str: str) -> str:
    """Converts string with hex chars to string"""
    return bytes.fromhex(hex_str).decode('utf-8')


def notify_discord(message: str) -> None:
    """Just sends message to discord, without rate limits respect"""
    logger.debug('Sending discord message')

    # hookURL: str = 'https://discord.com/api/webhooks/896514472280211477/LIKgbgNIr9Nvuc-1-FfylAIY1YV-a7RMjBlyBsVDellMbnokXLYKyBztY1P9Q0mabI6o'  # noqa: E501  # FBSC
    hookURL: str = 'https://discord.com/api/webhooks/901531763740913775/McqeW4eattrCktrUo2XWhwaJO3POSjWbTb8BHeFAKrsTHOwc-r9rQ2zkFxtGZ1eQ_Ifd'  # noqa: E501  # dev
    content: bytes = f'content={requests.utils.quote(message)}'.encode('utf-8')

    if len(content) >= 2000:  # discord limitation
        logger.warning(f'Refuse to send len={len(content)}, content dump:\n{content}')
        return

    discord_request: requests.Response = requests.post(
        url=hookURL,
        data=content,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    try:
        discord_request.raise_for_status()

    except Exception as e:
        logger.exception(f'Fail on sending message to discord ({"/".join(hookURL.split("/")[-2:])})'
                         f'\n{discord_request.content}', exc_info=e)
        return

    logger.debug('Sending successful')
    return

