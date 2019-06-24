# pl-slideshow
An example plugin to demonstrate CHRiS' parallelization capabilities and to provide a framework for building your own parallelized CHRiS plugin

## How does it work?
1. The code for your parallelized plugin is run by multiple workers, which all (eventually) run the `init_worker` function.
2. Each worker is assigned a worker number. The worker with worker number 0 becomes the leader worker, and the rest become followers.
3. The follower workers enter the `run_follower` function, where they will wait for communications from the leader worker.
4. The plugin calculates what commands should be sent to each worker based on the number of workers. Note that only the leader worker runs this code, as the other workers are still waiting in the `run_follower` loop.
5. The plugin sends commands to each worker with the `run_commands` function. Commands are passed in a list of lists of strings, where each sub-list corresponds to the commands that worker should execute. For example, if I wanted worker 0 to run `touch foo` and `mv foo bar` and I wanted worker 1 to run `touch foo2` and `mv foo2 bar2`, my commands list would look like `[["touch foo", "mv foo bar], ["touch foo2", "mv foo2 bar2"]]`.
6. `run_commands` can be run subsequent times if you need new commands that depend on the results of previous commands.
7. `exit_worker` sends an exit signal to all of the workers once all processing is complete.

## What does this plugin do in particular?
The example plugin takes a set of images and makes them into a slideshow video. Each image is resized in parallel to fit in the video.
Syntax:
```
    python slideshow.py
        [-v <level>] [--verbosity <level>]
        [--version]
        [--man]
        [--meta]
        [--resolution <resolution>]
        <inputDir>
        <outputDir>
```
