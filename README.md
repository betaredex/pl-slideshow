# pl-slideshow
An example plugin to demonstrate ChRIS' parallelization capabilities and to provide a framework for building your own parallelized ChRIS plugin

## How do I use it?
This plugin contains both a framework for creating your own parallelized plugins, and an example of a parallelized plugin using this framework. All of the framework logic is contained in `parallel.py`, so as a plugin writer, you only need to import that and pass the commands you want each worker to run through the `run_commands` function. Commands are run in phases to provide sequentiality. For instance, this slideshow plugin has a phase for resizing the images to the intended resolution of the video, and then a separate phase to stitch them together into the video. The video cannot be created until the resizing is complete, so it's a separate phase. Each phase is represented by a list of what command(s) each worker should run. For example, if I wanted worker 0 to run `mkdir foo` and `touch foo/bar` and worker 1 to run `mkdir beep` and `touch beep/boop` in the first phase, and then I wanted worker 0 to run `mkdir blah`, `mv foo/bar blah/` and `mv beep/boop blah/` in the second phase, this is what I'd pass to `run_commands`:
`[[["mkdir foo", "touch foo/bar"], ["mkdir beep", "touch beep/boop"]], [["mkdir blah", "mv foo/bar blah/", "mv beep/boop blah/"]]]`

## How does it work?
1. The code for your parallelized plugin is run by multiple workers, which all (eventually) run the `run_commands` function.
2. Each worker is assigned a worker number. The worker with worker number 0 becomes the leader worker, and the rest become followers. Worker numbers are used to organize the workers and communicate between them.
3. The follower workers enter the `run_follower` function, where they will wait for communications from the leader worker.
4. Once the leader worker sends the start signal, the followers will execute their commands and then return to idle.
5. The leader worker will then give the start signal again to move on to the next phase, or if there are no more commands to run, it will send the exit signal to all of the workers.

## What does this plugin do in particular?
The example plugin takes a set of images and makes them into a slideshow video. Each image is resized in parallel to fit in the video. All of the logic for this plugin is contained in `slideshow.py`, and all the logic for handling parallelization is contained in `parallel.py`.
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
