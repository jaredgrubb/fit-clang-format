COLORS = {
    'reset': "\x1b[0m",
    'reverse': "\x1b[7m",

    'black':  "\x1b[22;30m",
    'dk_red': "\x1b[22;31m",
    'dk_green' : "\x1b[22;32m",
    'dk_yellow' : "\x1b[22;33m",
    'dk_blue': "\x1b[22;34m",
    'dk_magenta': "\x1b[22;35m",
    'dk_cyan': "\x1b[22;36m",
    'lt_gray': "\x1b[22;37m",
    'dk_gray': "\x1b[1;30m",
    'red': "\x1b[1;31m",
    'green': "\x1b[1;32m",
    'yellow': "\x1b[1;33m",
    'blue': "\x1b[1;34m",
    'magenta': "\x1b[1;35m",
    'cyan': "\x1b[1;36m",
    'white': "\x1b[1;37m",
    'default': "\x1b[22;39m",

    'back_black': "\x1b[40m\x1b[K", # adding the "K" command clears the line going forward so the whole line gets the color
    'back_red': "\x1b[41m\x1b[K",
    'back_green': "\x1b[42m\x1b[K",
    'back_yellow': "\x1b[43m\x1b[K",
    'back_blue': "\x1b[44m\x1b[K",
    'back_magenta': "\x1b[45m\x1b[K",
    'back_cyan': "\x1b[46m\x1b[K",
    'back_white': "\x1b[47m\x1b[K",
    'back_default': "\x1b[49m\x1b[K",
}

def wrap(color, txt, reset=COLORS['reset']):
    # if the color is empty, then no need to reset either
    if not isinstance(txt, basestring):
        txt = str(txt)
    if color:
        return color+txt+reset
    return txt
