#!/usr/bin/env python


# Get a value
# ------------------------------------------------
def get_value(prompt, conv_func = lambda s:s.strip(), check_func = None):
    """
    Aks the value from the user.

    If only "prompt" is given, this function is equal to the
    built-in function "input".

    If "conv_func" is given, the function will be called with the
    input-value. If the conversion fails, the input prompt will be
    shown again.

    If "check_func" is given, the function will be called with the
    converted input-value, if there's a "conv_func" else with the
    string value. If the function returns "True", the input-value will be
    returned.
    """
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


def ask(question):
    """
    Asks the user the question until he answers it with yes or no.
    
    Returns true if the user answered with yes.
    """
    prompt = question + " (yes|no) "
    while True:
        temp = input(prompt)
        temp = temp.strip()
        temp = temp.upper()
        if temp in ("Y", "YES"):
            return True
        elif temp in ("N", "NO"):
            return False
