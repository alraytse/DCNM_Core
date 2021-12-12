#!/usr/bin/env python
"""Our own API support utilities

Jose Lima
Tue Feb 12 5:02:59 PM 2019

This module contains classes and functions related to API support functions.
in general no code is hosted here related to specific API calls, most of these
functions and classes are used as decorators to augment existing functionality.

    Example:
        1) import all modules within, this can get heavy

            import core.utilities

        2) import only specific modules, light and easier on resources depending
        on the module being imported

            from core.utilties import retry_on_server_error

    Todo:
"""

# `========== time_me decorator used to time function/object run time ==========`
import time
import sys


def time_me(f):
    """times function execution time

    Jose Lima
    2019-02-11 14:17

    can be used as a decorator to other functions to time and report execution time

    Examples:

        from core.utilities import time_me

        @time_me
        def func1():
            print('test')

    Returns:
        string: `>>> func1 took 10 ms to run.`
    """
    import time
    from functools import wraps

    def wrapper(*args, **kwargs):
        start = time.time()
        results = f(*args, **kwargs)
        end = time.time()
        print(
            f">>> {f.__name__} took {((end - start) * 1000) / 1000.0:.1f} seconds to run."
        )
        return results

    return wrapper


# `========== API connection reliability decorators==========`

# this is docorator is for reference only
# def retry_on_server_error_depricated(f):
#     import time
#     from functools import wraps
#     wraps(f)

#     def function_to_retry(*args, **kwargs):
#         MAX_TRIES = 5
#         tries = 0
#         while True:
#             resp = f(*args, **kwargs)
#             if resp.status_code >= 500 and tries < MAX_TRIES:
#                 tries += 1
#                 # wait tries + 1, if retries 1 + 1, sleep = 2 seconds
#                 time.sleep(tries + 1)
#                 print(f'Serser error: {resp.status_code}, retries: {tries})')
#                 continue
#             break
#         return resp

#     return function_to_retry


class Retry:
    """Adds reliablitiy to API calls by doing a retry on certain failures

    Jose Lima
    2019-02-11 14:17

    The decorated function must return response.status_code via the API call
    this class allows flexibility by using class inheritance and allowing us to
    modify certain aspects of the class based on certain server responses.

    Notes:
        requires return value to be API response code with valid status_code
        attribute.

        return resp, must have valid server response code, resp.status_code

    Examples:

        from core.utilies import retry_on_server_error

        @retry_on_server_error
        def get(self):
            url = self.base_url + url
            resp = requests.get(url, headers=self.headers, verify=False)
            if not resp.ok:
                print(f'Error: {url}.  Response: {resp.text}')
            return resp

    Returns:
        Original wrapped function when used as a decorator
    """

    MAX_TRIES = 5

    def is_valid(self, resp):
        return not resp.status_code == 500

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            tries = 0
            try:
                while True:
                    resp = f(*args, **kwargs)
                    if self.is_valid(resp) or tries >= self.MAX_TRIES:
                        break
                    try:
                        resp.json()["stackTrace"]
                        print(
                            f'\n\n[ caller: {sys._getframe(2).f_code.co_name} --> {sys._getframe(1).f_code.co_name} ] {resp.json()["message"] }\n\n'
                        )
                        return resp
                    except Exception as e:
                        pass
                    tries += 1
                    time.sleep(tries + 1)
                    print(f"Server error: {resp.status_code}, retries: {tries}\n")
                return resp
            except Exception as e:
                print(e)
                exit(1)

        return wrapper


class RetryOnAuthError(Retry):
    """clone Retry and make Auth error class"""

    MAX_TRIES = 1

    def is_valid(self, resp):
        return not resp.status_code >= 401


class RetryOnServerError(Retry):
    """clone Retry and make Server error class"""

    MAX_TRIES = 5

    def is_valid(self, resp):
        return not resp.status_code >= 500 and resp.status_code <= 599


class RetryOnServerErrorLogin(Retry):
    """clone Retry and make Server error class"""

    MAX_TRIES = 1

    def is_valid(self, resp):
        return not resp.status_code >= 500 and resp.status_code <= 599


# create callable functions from class to use as decorators
# this functions will be imported at run time by sessions.py
retry_on_auth_failure = RetryOnAuthError()
retry_on_auth_and_error = RetryOnAuthError()
retry_on_server_error = RetryOnServerError()
retry_on_login_error = RetryOnServerErrorLogin()