import subprocess
import types

# Run a command and return the stdout by default
# Set include_stderr if you want the stderr too (will return the pair).
def run(command, include_stdout=True, include_stderr=False, check=True, **kwargs):
    #print " $$ ", ' '.join(command)
    if include_stdout:
        kwargs['stdout'] = subprocess.PIPE
    if include_stderr:
        kwargs['stderr'] = subprocess.PIPE

    p = subprocess.Popen(command, **kwargs)
    stdout, stderr = p.communicate()

    if check and p.returncode:
        raise ValueError("git command returned code %s" % p.returncode)

    if include_stdout and include_stderr:
        return stdout, stderr
    elif include_stdout:
        return stdout
    elif include_stderr:
        return stderr
    else:
        return None

def check(command, **kwargs):
    try:
        run(command, **kwargs)
        return True
    except ValueError:
        return False

def get_files_with_extensions(path, extensions):
    cmd = ['find', '.',
        '-type', 'f',
        '(']
    add_or = False
    for extension in extensions:
        if add_or:
            cmd.append('-or')
        else:
            add_or = True
        cmd.extend(['-name', '*.%s'%extension])
    cmd.append(')')
    cmd.append('-print0')
    files = sorted(f[2:] for f in run(cmd, cwd=path).split('\0') if f)
    return files


def flatten(values):
    if isinstance(values, (list, types.GeneratorType, set)):
        ret = []
        for value in values:
            ret.extend(flatten(value))
        return ret
    else:
        return [values]

# A 'box' to allow us to hash things that arent hashable (like dict or list)
class BoxedThing(object):
    def __init__(self, thing):
        self.thing = thing
    def __hash__(self):
        if isinstance(self.thing, dict):
            return hash(frozenset(((x,boxed(y)) for x,y in self.thing.iteritems())))
        if isinstance(self.thing, list):
            return hash(tuple((boxed(x) for x in self.thing)))
        return hash(self.thing)
    def __str__(self):
        return str(self.thing)
    def __repr__(self):
        return repr(self.thing)
    def __eq__(self, other):
        return self.thing==unboxed(other)
    def __ne__(self, other):
        return self.thing!=unboxed(other)
    def __cmp__(self, other):
        return cmp(self.thing, unboxed(other))

# Box things that can't be hashed (list and dict); returns the input on all other types.
def boxed(thing):
    if isinstance(thing, (list,dict)):
        return BoxedThing(thing)
    return thing

# Unbox things that are boxed. Returns the input on all other types.
def unboxed(thing):
    if isinstance(thing, BoxedThing):
        return thing.thing
    return thing

# A class property that evaluates on the first call and then returns a cached value.
class lazy_property(object):
    def __init__(self,fget):
        self.fget = fget
        self.func_name = fget.__name__

    def __get__(self,obj,cls):
        if obj is None:
            return None
        value = self.fget(obj)
        setattr(obj,self.func_name,value)
        return value
