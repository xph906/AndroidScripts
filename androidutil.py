#!/usr/bin/python

'''utils for giving adb, emulator commands; assume them in path
   and that they will not be'''

import subprocess
import shlex
import os.path
import os
import sys

# set this for use by everyone in plg
ADB = 'adb'

def killserver():
    subprocess.check_call([ADB, 'kill-server'])

def startserver():
    subprocess.check_call([ADB, 'start-server'])

def getadbcmd(args=None, device=None):
    ''' helper function:
        args - arguments excluding adb and device'''
    preargs = [ADB]
    if device:
        device = device.strip()
        if device:
            preargs += ['-s', device]
    if not args:
        return preargs
    return preargs + args

def runadbcmd(args, device=None):
    return subprocess.check_call(getadbcmd(args, device))

def waitfordevice(device=None, timeout=None):
    ''' wait for device to come online.

    It is preferable to keep a `timeout` here for error handling. When you
    expecting an emulator to be there, it may not actually be there (may not
    get launched, for example).
    '''
    subprocess.check_call(getadbcmd(['wait-for-device'], device),
            timeout=timeout)

def install(filename, device=None):
    subprocess.check_call(getadbcmd(['install', filename], device))

def uninstall(pkgname, device=None):
    subprocess.check_call(getadbcmd(['uninstall', pkgname], device))

def forward_tcp(local, remote, no_rebind=False, device=None):
    args = ['forward']
    if no_rebind:
        args.append('--no-rebind')
    args.extend(['tcp:{}'.format(local), 'tcp:{}'.format(remote)])
    print('forward', local, remote)
    return runadbcmd(args, device)

def remove_forward_tcp(local, device=None):
    args = ['forward', '--remove', 'tcp:{}'.format(local)]
    return runadbcmd(args, device)

def screencap(png, device=None):
    if not png.endswith('.png'):
        png += '.png'
    cmd = r"{}{} shell screencap -p | sed 's/\r$//' > {}".format(ADB,
            '' if not device else ' -s ' + device, png)
    return subprocess.call(cmd, shell=True)

def startactivity(activity, device=None):
    return runadbcmd(['shell', 'am', 'start', '-a',
        'android.intent.action.MAIN', '-n', activity], device)

def dumpsys(args, device=None):
    return subprocess.check_output(getadbcmd(['shell', 'dumpsys'] + args,
        device)).decode()

def getdevices():
    args = [ADB, 'devices']
    output = subprocess.check_output(args)
    devices = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line == b'List of devices attached':
            continue
        [name, type_] = line.split()
        if type_ == b'device':
            devices.append(name.decode())
    return devices

def getstatus(device=None):
    return subprocess.check_output(getadbcmd(['get-state'],
        device)).strip().decode()

def onlinedevices():
    return [device for device in getdevices() if getstatus(device) == 'device']

def launchemulator(args):
    ''' returns corresponding process; can operate on it as p.poll()
        or p.terminate() '''
    if not os.path.basename(args[0]).startswith('emulator'):
        args = 'emulator' + args
    proc = subprocess.Popen(args)
    return proc

def killemulator(device=None):
    ''' no snapshot will be saved
        better option may be to terminate the process returned by
        launchemulator '''
    return subprocess.call(getadbcmd(['emu', 'kill'], device))

def init(logfile=None):
    if not logfile:
        logfile = sys.stderr
    print('(re)starting adb server', file=logfile)
    killserver()
    startserver()
    #sleep(10) # let adb start
    print('killing any emulators already present', file=logfile)
    for device in getdevices():
        killemulator(device)
