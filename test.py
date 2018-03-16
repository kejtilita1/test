import time
import os
import sys
import subprocess
from intelsite import inteldatetime
import argparse
import autocodepromote

# parse out arguments
parser = argparse.ArgumentParser()
#parser.add_argument("--username",
#                    required="True")
#parser.add_argument("--password",
#                    required="True")
# parser.add_argument("--url",
#                    required="True")
args = vars(parser.parse_args())
#username = args.get('username')
#password = args.get('password')
# repoURL = args.get('url')

# set up our locations
repodir = r'.'
print "This is the repodir" + repodir
#username = username.replace("'", "")
#password = password.replace("'","")
#print username
#print password
#hgpath = r"C:\Program Files\TortoiseHg\hg.exe" # PATH TO HG.EXE

#repoURL = "https://" + username + ':' + password + "@nsg-hg.intel.com/index.py/SVC_SQE_Firmware_Test/"
#repoURL = "https://" + username + ':' + password + "@nsg-hg.intel.com/index.py/TWIDL_Trunk"


if not os.path.exists(repodir):
    print 'Whoops, invalid local directory for repository.'
    sys.exit(1)
# if not os.path.exists(hgpath):
#     print 'Invalid hg.exe path. Is it really installed at ' + hgpath + '?'
#     sys.exit(1)

# pull the most recent changeset
# hg = subprocess.Popen([hgpath, 'pull', '-u', repoURL], stdin=subprocess.PIPE,
#                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=repodir)
# cout, cerr = hg.communicate()
# hg.wait()
# print cout, cerr
# if hg.returncode != 0:
#     sys.exit(1)

# update the working repository
#hg = subprocess.Popen([hgpath, 'update'], stdin=subprocess.PIPE,
#                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=repodir)
#cout, cerr = hg.communicate()
#hg.wait()
#print cout, cerr
#if hg.returncode != 0:
#    sys.exit(1)
def create_revision(repodir):
    f = open(repodir + r'\kbase\release.txt', 'r+')
    firstLine = f.readline().strip().split()

    # get the intel workweek
    date_time = map(int,(time.strftime("%Y,%m,%d,%H,%M,%S")).split(','))
    date_time = inteldatetime(*date_time)
    workweek = date_time.workweek

    # adjust the version number
    version = firstLine[2].split('.')
    version = map(int, version)
    if version[2] == 99:
        version[2] = '00'
        if version[1] == 99:
            version[1] = '00'
            version[0] += 1
        else:
            version[1] += 1
            if version[1] < 10:
                version[1] = '0' + str(version[1])
    else:
        version[2] = version[2] + 1
        if version[2] < 10:
            version[2] = '0' + str(version[2])
    version = map(str, version)
    version = version[0] + '.' + version[1] + '.' + version[2]
    firstLine[2] = version

    # edit release notes with updated version and workweek
    firstLine[3] = "[" + time.strftime("%Y")[2:] + "WW" + str(workweek) + "]"
    f.seek(0)
    f.write(' '.join(firstLine) + '\n')
    f.close()

def commit_msg(repodir):
    f = open(repodir + r'\kbase\release.txt', 'r+')
    firstLine = f.readline().strip().split()
    firstLine[2] = version
    print version
    commitMsg= "Update Test environment with TWIDL " + version

    return commitMsg



#autocodepromote.AutoCodePromote.promote_change( )


a = AutoCodePromote(r"C:\test", disable_lfs=True, promote_retry_count=3)
commit_hash = a.promote_change(create_revision(repodir), "klita_test", commit_msg(repodir), tmp_banch_prefix="tmp", ff_ancestor_branch='master')

def create_releasenotes():
    gitpath ='C:\Program Files\Git\mingw64\\bin\git.exe'
    repodir = r'.'
    git = subprocess.Popen(['git', 'show','-1', '--pretty=format:"%H"', '--no-patch'],
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=repodir)
    cout, cerr = git.communicate()
    git.wait()
    print cout, "is cout"

    notes = cout.strip("\"\"").split('\n')
    print notes , 'is notes'

    if git.returncode != 0:
        sys.exit(1)
    # f = open(r'Y:\fast-tools-sqe\rev.txt', 'r+')
    f = open(r'C:\Users\klita\Documents\twidlgit\rev1.txt', 'r+')
    old = f.readline().strip()
    print old , "is old "
    f.seek(0)
    f.write(cout.strip("\""))
    f.close()

    diff_revisions = old.strip("\"") + '^..' + cout.strip().strip("\"")
    #diff_revisions = '460e9412fd54deb6ae54e014897f3e2f13318546' +'a6e27f64d1de2b67cfada1ba9b0f2448c99bb365'
    print 'Storing all commits between', diff_revisions
    git = subprocess.Popen(['git', 'log', '-M', '-r','--pretty=oneline', diff_revisions],
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=repodir)
    cout, cerr = git.communicate()
    git.wait()
    print cout
    if git.returncode != 0:
        if ('no changes found' not in cout):
            sys.exit(1)
    notes = cout.strip().split('\n')[0:]
    #f = open(r'Y:\fast-tools-sqe\ReleaseNotes.txt', 'w+')
    f = open(r'C:\Users\klita\Documents\twidlgit\ReleaseNotes.txt', 'w+')
    for elem in notes:
        f.write(elem)
        f.write('\n')
    f.close()


create_releasenotes()