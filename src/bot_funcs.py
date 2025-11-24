from threading import Timer

import globs


class UserState:
    def __init__(self):
        self.timeout_timer = None
        self.state: str | None = None


USER_STATES: dict[int, UserState] = {}


def reset_user_timer(chat_id):
    if chat_id in USER_STATES:
        if USER_STATES[chat_id].timeout_timer:
            USER_STATES[chat_id].timeout_timer.cancel()
        USER_STATES[chat_id].timeout_timer = None


def set_timeout(chat_id, timeout_func):
    if chat_id in USER_STATES and USER_STATES[chat_id].timeout_timer:
        USER_STATES[chat_id].timeout_timer.cancel()

    timeout_timer = Timer(globs.TIMEOUT, timeout_func)
    timeout_timer.start()

    if chat_id not in USER_STATES:
        USER_STATES[chat_id] = UserState()
    USER_STATES[chat_id].timeout_timer = timeout_timer
