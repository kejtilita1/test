#exception class used to throw errors
class ScmError(Exception):
    def __init__(self, msg):
        self.msg = msg.strip()

    def __str__(self):
        return str(self.msg)
        
class ScmCommandError(ScmError):
    def __init__(self, msg, cmd, rc):
        super(ScmCommandError, self).__init__(msg)
        self.cmd = cmd
        self.rc = rc
        
    def __str__(self):
        errstr = str(self.msg)
        errstr += "\n" + "Command=" + str(self.cmd)
        errstr += "\n" + "Return code=" + str(self.rc)
        return errstr
