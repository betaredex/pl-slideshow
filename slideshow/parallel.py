import os
import sys
import time
from filelock import FileLock
from inotify.adapters import Inotify

NUM_SYNC_PATH = '/tmp/num_sync'
NUM_SYNC_LOCK = FileLock(NUM_SYNC_PATH+'.lock')
WORKER_STATE_DIR = '/tmp/worker_state'
WORKER_COMMAND_DIR = '/tmp/worker_command'
WORKER_NUM_TIME_LIMIT = 60

IDLE = 0
START = 1
EXIT = 2

# Followers never return from this function, and instead enter their processing loop. Organizes the various workers and sets up the directories needed to communicate between them
def init_worker():
    if not os.path.exists(WORKER_STATE_DIR):
        os.mkdir(WORKER_STATE_DIR)
    if not os.path.exists(WORKER_COMMAND_DIR):
        os.mkdir(WORKER_COMMAND_DIR)
    worker_num = assign_worker_num()
    print("Got worker number: {}".format(worker_num))
    if(worker_num == 0):
        for i in range(1, int(os.environ['NUMBER_OF_WORKERS'])):
            write_state(IDLE, i)
    else:
        run_follower(worker_num)

# The follower processing loop. Checks the state of this worker and runs commands or stops the worker
def run_follower(worker_num):
    try:
        state = read_state(worker_num)
    except FileNotFoundError:
        state = IDLE
    while state != EXIT:
        if state == IDLE:
            wait_for_changes(os.path.join(WORKER_STATE_DIR, 'worker_state_{}'.format(worker_num)))
            state = read_state(worker_num)
        if state == START:
            for command in read_commands(worker_num):
                print("Running command: {}".format(command))
                os.system(command)
            state = IDLE
            write_state(IDLE, worker_num)
    os.remove(os.path.join(WORKER_COMMAND_DIR, 'worker_command_{}'.format(worker_num)))
    os.remove(os.path.join(WORKER_COMMAND_DIR, 'worker_command_{}.lock'.format(worker_num)))
    os.remove(os.path.join(WORKER_STATE_DIR, 'worker_state_{}'.format(worker_num)))
    os.remove(os.path.join(WORKER_STATE_DIR, 'worker_state_{}.lock'.format(worker_num)))
    sys.exit()

# Runs the commands for each worker. Takes in a list of lists of strings, where the strings are commands and the lists correspond to each worker
def run_commands(commands):
    for i, worker_commands in enumerate(commands, start=1):
        write_commands(worker_commands, i)
        write_state(START, i)
    for command in commands[0]:
        print("Running command: {}".format(command))
        os.system(command)
    for i in range(1, int(os.environ['NUMBER_OF_WORKERS'])):
        state = read_state(i)
        while state != IDLE:
            wait_for_changes(os.path.join(WORKER_STATE_DIR, 'worker_state_{}'.format(i)))
            state = read_state(i)

# Sets the state of the followers to EXIT and exits from the leader
def exit_worker():
    for i in range(1, int(os.environ['NUMBER_OF_WORKERS'])):
        write_state(EXIT, i)
    sys.exit()

# Helper function that checks for filesystem events to see when the command/state/number files are updated
def wait_for_changes(path):
    i = Inotify()
    i.add_watch(path)
    for event in i.event_gen(yield_nones=False):
        if event[1][0] == "IN_MODIFY":
            return event

# Distributes worker numbers to each worker.
def assign_worker_num():
    with NUM_SYNC_LOCK.acquire():
        try:
            with open(NUM_SYNC_PATH, 'x') as f:
                f.write('1')
            worker_num = 0 
        except FileExistsError:
            with open(NUM_SYNC_PATH, 'r+') as f:
                worker_num = int(f.read().strip())
                f.seek(0)
                f.write(str(worker_num+1))
                f.truncate()
    if worker_num+1 == int(os.environ['NUMBER_OF_WORKERS']):
        os.remove(NUM_SYNC_PATH)
        os.remove(NUM_SYNC_PATH+".lock")
    return worker_num

def read_state(worker_num):
    path = os.path.join(WORKER_STATE_DIR, 'worker_state_{}'.format(worker_num))
    lock = FileLock(path+'.lock')
    with lock.acquire():
        with open(path, 'r') as f:
            state = int(f.read().strip())
    return state

def write_state(state, worker_num):
    path = os.path.join(WORKER_STATE_DIR, 'worker_state_{}'.format(worker_num))
    lock = FileLock(path+'.lock')
    with lock.acquire():
        with open(path, 'w') as f:
            f.write(str(state))

def read_commands(worker_num):
    path = os.path.join(WORKER_COMMAND_DIR, 'worker_command_{}'.format(worker_num))
    lock = FileLock(path+'.lock')
    with lock.acquire():
        with open(path, 'r') as f:
            commands = f.readlines()
    return commands

def write_commands(commands, worker_num):
    path = os.path.join(WORKER_COMMAND_DIR, 'worker_command_{}'.format(worker_num))
    lock = FileLock(path+'.lock')
    with lock.acquire():
        with open(path, 'w') as f:
            f.write('\n'.join(commands))
