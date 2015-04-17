import pty
from multiprocessing import Process
import subprocess
import os
from queue import Queue, Empty
from threading import Thread

from plg.utils import androidutil

# inspired from http://stackoverflow.com/a/4896288/567555
def _enqueue_output(out, q):
    for line in iter(out.readline, b''):
        q.put(line)
    out.close()

def logcatlines(device=None, args=''):
    cmd = ' '.join(androidutil.getadbcmd(args, device)) + ' logcat ' +args
    logmaster, logslave = pty.openpty()
    logcatp = subprocess.Popen(cmd, shell=True,
            stdout=logslave, stderr=logslave, close_fds=True)
    stdout = os.fdopen(logmaster)
    q = Queue()
    t = Thread(target=_enqueue_output, args=(stdout, q))
    t.daemon = True
    t.start()
    while logcatp.poll() is None:
        try:
            yield q.get(True, 1)
        except Empty:
            continue

def _logcat(device, fname, logcatargs):
    with open(fname, 'w') as f:
        for line in logcatlines(device, logcatargs):
            f.write(line)
            f.flush()

def logcat(fname, device=None, logcatargs=''):
    ''' run logcat and collect output in file fname.'''
    proc = Process(target=_logcat, args=(device, fname, logcatargs))
    proc.start()

def clearlogcat(device=None):
    return androidutil.runadbcmd(['logcat', '-c'], device)
