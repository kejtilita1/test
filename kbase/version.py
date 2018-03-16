import sys
import os, twidl_os


class Version(object):
   
    def __init__(self,version=None):

        if ( None == version ):

            # if the sys module has attribute _MEIPASS, we are running from
            # a PyInstaller executable.  If so, we must load the shared
            # library from the tmp directory created by the PyInstaller
            # executable and must do so *without* full path to the shared
            # library and (linux only) using the LD_LIBRARY_PATH environment variable
            # set by the PyInstaller run-time process.  See the PyInstaller
            # docs for more on this.
            if (twidl_os.isPyInstallerExecutable() or twidl_os.isPy2ExeExecutable()):
                version_name = os.path.join(twidl_os.getRoot(), "release.txt")
            else:
                version_name = os.path.join(twidl_os.getRoot(),  'kbase', "release.txt")

            self._version = open(version_name).readline()

    def getVersion(self):
        """
        Brief:
            getVersion() - Return the TWIDL release portion of the version string.

        Description:
            Return the TWIDL release portion of the version string. Specifically:
                "TWIDL Release n.nn.nn [YYWW##]"

        Argument(s):
            None

        Return Value(s):
            The TWIDL version as a string.

        Example:
            print 'Current version: %s' % getVersion()

        Related: -
            None

        Author(s):
            Ofer Levy
        """
        return(self._version)

    def getRelease(self):
        """
        Brief:
            getRelease() - Return the TWIDL release portion of the version string.

        Description:
            Return the TWIDL release portion of the version string. Specifically:
                "TWIDL Release n.nn.nn [YYWW##]"

        Argument(s):
            None

        Return Value(s):
            The TWIDL version as a string.

        Example:
            getRelease()

        Related: -
            None

        Author(s):
            Ofer Levy
        """
        return(self._version.split(",")[0])

   
    def getReleaseInfo(self):        
        """
        Brief:
            getReleaseInfo() - Read in and print the entire release.txt file.

        Description:
            Read in and print the entire release.txt file.

        Argument(s):
            None

        Return Value(s):
            None. Prints to standard out.

        Example:
            getReleaseInfo()

        Related: -
            None

        Author(s):
            Ofer Levy
        """
        # see comment about _MEIPASS, above.
        if (twidl_os.isPyInstallerExecutable() or twidl_os.isPy2ExeExecutable()):
            releaseFileName = os.path.join(twidl_os.getRoot(), "release.txt")
        else:
            releaseFileName = os.path.join(twidl_os.getRoot(), 'kbase', "release.txt")

        for line in open(releaseFileName).readlines() :
            print line
