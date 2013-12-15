#!/usr/bin/python3
# Benedikt Schmitt <benedikt@benediktschmitt.de>


"""
Some useful functions to get a valid input from the command line.

"""


__all__ = ["get_value", "ask"]


def get_value(prompt, conv_func=None, check_func=None):
    """
    Aks the value from the user.

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
    return get_value(prompt, int, check_func)

def get_float(prompt, check_func=None):
    return get_value(prompt, float, check_func)

def choose(choices):
    """
    The user has to choose an element of choices.
    """
    choices_str = [str(e) for e in choices]
    prompt = "> Choose from:\n" +\
             ">   [{}] ".format("|".join(choices_str))
    
    choice = get_value(prompt, lambda s: s.strip(), lambda s: s in choices_str)
    index = choices_str.index(choice)
    return (choice, index)

def ask(question, default=None):
    """
    Asks the user the question until he answers it with yes or no.
    
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


if __name__ == "__main__":
    v = get_int("> an integer please")
    print(v)
    v = get_int("> an integer between 1 and 10", lambda i: 1 <= i <= 10)
    print(v)

    yes = ask("Do you like foo")
    print(yes)
    yes = ask("Do you like bar?", False)
    print(yes)

    choice = choose(["foo", "bar"])
    print(choice)
