#!/usr/bin/env python3

# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org>


"""
This module provides some useful functions to get valid input from the
command line.
"""


# Functions
# ------------------------------------------------

def get_value(prompt, conv_func=None, check_func=None):
    """
    Tries to get a value from the user.

    If only "prompt" is given, this function is equal to the
    built-in function "input".

    If "conv_func" is given, the function will be called with the
    input-value. If the conversion fails, the input prompt will be
    shown again.

    If "check_func" is given, the function will be called with the
    converted input-value, if there's a "conv_func" else with the
    converted value. If the function returns "True", the converted-value will
    be returned.
    """
    if not prompt.endswith(" "):
        prompt += " "

    while True:
        temp = input(prompt)

        if conv_func is not None:
            try:
                temp = conv_func(temp)
            except:
                continue

        if check_func is None:
            break
        elif check_func(temp):
            break
    return temp


def get_int(prompt, check_func=None):
    """
    """
    return get_value(prompt, int, check_func)


def get_float(prompt, check_func=None):
    """
    """
    return get_value(prompt, float, check_func)


def choose(prompt, choices):
    """
    The user has to choose an element of *choices*.
    """
    # We add a list of the coices to the prompt. The items
    # index starts by 1.
    for i, choice in enumerate(choices):
        prompt += "\n{}. {}".format(i + 1, choice)
    prompt += "\n"

    # Let the user choose.
    while True:
        try:
            index = int(input(prompt)) - 1
            choice = choices[index]
        except KeyboardInterrupt:
            # This makes sure, that the user can still leave
            # the application by [ctrl + c].
            raise
        except:
            # Show the prompt again ...
            pass
        else:
            # Everything is ok: The user entered an integer
            # and the *index* is in the correct range: [0, len(choices)].
            # So we've got our value.
            break
    return (index, choice)


def ask(question, default=None):
    """
    Asks the user the question until he answers it with *yes* or *no*.

    Returns true if the user answered with yes.
    Returns *default* if the user only hit enter.
    """
    if default is None:
        prompt = question + " (yes|no) "
    elif default:
        prompt = question + " (YES|no) "
    else:
        prompt = question + " (yes|NO) "

    while True:
        temp = input(prompt)
        temp = temp.strip()
        temp = temp.upper()
        if default is not None and not temp:
            return default
        elif temp in ("Y", "YES"):
            return True
        elif temp in ("N", "NO"):
            return False
