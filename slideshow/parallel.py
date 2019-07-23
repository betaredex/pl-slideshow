import os
import sys
import time
from filelock import FileLock
from inotify.adapters import Inotify

NUM_SYNC_PATH = '/tmp/num_sync'
NUM_SYNC_LOCK = FileLock(NUM_SYNC_PATH+'.lock')
WORKER_STATE_DIR = '/tmp/worker_state'
WORKER_NUM_TIME_LIMIT = 60

IDLE = 0
START = 1
EXIT = 2

# The entrypoint function. "commands" should be a list of lists of lists of strings which contain commands. See the documentation for an in-depth explanation of how the commands should be passed.
def run_commands(commands):
    if not os.path.exists(WORKER_STATE_DIR):
        os.mkdir(WORKER_STATE_DIR)
    worker_num = assign_worker_num()
    print("Got worker number: {}".format(worker_num))
    if(worker_num == 0):
        for i in range(1, int(os.environ['NUMBER_OF_WORKERS'])):
            write_state(IDLE, i)
        run_leader(commands)
    else:
        run_follower(commands, worker_num)

# The follower processing loop. Runs commands or stops the worker, depending on the state.
def run_follower(commands, worker_num):
    phase_num = -1
    try:
        state = read_state(worker_num)
    except FileNotFoundError:
        state = IDLE
    while state != EXIT:
        if state == IDLE:
            wait_for_changes(os.path.join(WORKER_STATE_DIR, 'worker_state_{}'.format(worker_num)))
            state = read_state(worker_num)
        if state == START:
            phase_num+=1
            if worker_num < len(commands[phase_num]):
                for command in commands[phase_num][worker_num]:
                    print("Running command: {}".format(command))
                    os.system(command)
            state = IDLE
            write_state(IDLE, worker_num)
    os.remove(os.path.join(WORKER_STATE_DIR, 'worker_state_{}'.format(worker_num)))
    os.remove(os.path.join(WORKER_STATE_DIR, 'worker_state_{}.lock'.format(worker_num)))

# To be run by the leader worker. Manages the states of the other workers.
def run_leader(commands):
    for phase in commands:
        for i in range(1, int(os.environ['NUMBER_OF_WORKERS'])):
            write_state(START, i)
        for command in phase[0]:
            print("Running command: {}".format(command))
            os.system(command)
        print("Done with commands")
        for i in range(1, int(os.environ['NUMBER_OF_WORKERS'])):
            state = read_state(i)
            while state != IDLE:
                wait_for_changes(os.path.join(WORKER_STATE_DIR, 'worker_state_{}'.format(i)))
                state = read_state(i)
        print("Finished this phase")
    print("Exiting")
    for i in range(1, int(os.environ['NUMBER_OF_WORKERS'])):
        write_state(EXIT, i)

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
