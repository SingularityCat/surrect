from sys import path

runes = {}

def rune(runeid, registry=runes):
    def regrune(runefunc):
        registry[runeid] = runefunc
    return regrune

def load(fpath):
    with open(fpath, "r") as src:
        runescope = {
            "rune": rune
        }
        code = compile(src.read(), fpath, "exec",)
        exec(code, runescope)

