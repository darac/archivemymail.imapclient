import subprocess as sp

class subprocess:
    def __init__(self, cmd, stdin=None, input=None, check=False):
        try:
            if input is not None:
                self.obj = sp.run(cmd, input=input, check=check)
            else:
                self.obj = sp.run(cmd, stdin=stdin, check=check)
        except AttributeError:
            # Fall back to Python2 semantics
            print( dir( sp ) )
            self.obj = sp.Popen(cmd, stdin=stdin)
            self.obj.communicate(input)
            if check:
                self.check(obj)

    def check(self):
        if self.obj is None:
            return
        try:
            self.obj.check_returncode()
        except AttributeError:
            if self.obj.returncode:
                raise sp.CalledProcessError(self.obj.returncode, self.obj.args)

