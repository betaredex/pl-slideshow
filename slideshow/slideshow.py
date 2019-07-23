#!/usr/bin/env python                                            
#
# slideshow ds ChRIS plugin app
#
# (c) 2016-2019 Fetal-Neonatal Neuroimaging & Developmental Science Center
#                   Boston Children's Hospital
#
#              http://childrenshospital.org/FNNDSC/
#                        dev@babyMRI.org
#


import os
from os.path import isfile, join # Just to make some lines shorter
import sys
import shutil
sys.path.append(os.path.dirname(__file__))

# import the Chris app superclass
from chrisapp.base import ChrisApp

import parallel

Gstr_title = """

Generate a title from 
http://patorjk.com/software/taag/#p=display&f=Doom&t=slideshow

"""

Gstr_synopsis = """

(Edit this in-line help for app specifics. At a minimum, the 
flags below are supported -- in the case of DS apps, both
positional arguments <inputDir> and <outputDir>; for FS apps
only <outputDir> -- and similarly for <in> <out> directories
where necessary.)

    NAME

       slideshow.py 

    SYNOPSIS

        python slideshow.py                                         \\
            [-h] [--help]                                               \\
            [--json]                                                    \\
            [--man]                                                     \\
            [--meta]                                                    \\
            [--savejson <DIR>]                                          \\
            [-v <level>] [--verbosity <level>]                          \\
            [--version]                                                 \\
            <inputDir>                                                  \\
            <outputDir> 

    BRIEF EXAMPLE

        * Bare bones execution

            mkdir in out && chmod 777 out
            python slideshow.py   \\
                                in    out

    DESCRIPTION

        `slideshow.py` ...

    ARGS

        [-h] [--help]
        If specified, show help message and exit.
        
        [--json]
        If specified, show json representation of app and exit.
        
        [--man]
        If specified, print (this) man page and exit.

        [--meta]
        If specified, print plugin meta data and exit.
        
        [--savejson <DIR>] 
        If specified, save json representation file to DIR and exit. 
        
        [-v <level>] [--verbosity <level>]
        Verbosity level for app. Not used currently.
        
        [--version]
        If specified, print version number and exit. 

"""


class Slideshow(ChrisApp):
    """
    An app to ....
    """
    AUTHORS                 = 'betaredex (ebrock@redhat.com)'
    SELFPATH                = os.path.dirname(os.path.abspath(__file__))
    SELFEXEC                = os.path.basename(__file__)
    EXECSHELL               = 'python3'
    TITLE                   = 'Slideshow example app'
    CATEGORY                = ''
    TYPE                    = 'ds'
    DESCRIPTION             = 'An app to ...'
    DOCUMENTATION           = 'http://wiki'
    VERSION                 = '0.1'
    ICON                    = '' # url of an icon image
    LICENSE                 = 'Opensource (MIT)'
    MAX_NUMBER_OF_WORKERS   = 10  # Override with integer value
    MIN_NUMBER_OF_WORKERS   = 1 # Override with integer value
    MAX_CPU_LIMIT           = '2000m' # Override with millicore value as string, e.g. '2000m'
    MIN_CPU_LIMIT           = '3000m' # Override with millicore value as string, e.g. '2000m'
    MAX_MEMORY_LIMIT        = '2000Mi' # Override with string, e.g. '1Gi', '2000Mi'
    MIN_MEMORY_LIMIT        = '3000Mi' # Override with string, e.g. '1Gi', '2000Mi'
    MIN_GPU_LIMIT           = 1  # Override with the minimum number of GPUs, as an integer, for your plugin
    MAX_GPU_LIMIT           = 1  # Override with the maximum number of GPUs, as an integer, for your plugin

    # Use this dictionary structure to provide key-value output descriptive information
    # that may be useful for the next downstream plugin. For example:
    #
    # {
    #   "finalOutputFile":  "final/file.out",
    #   "viewer":           "genericTextViewer",
    # }
    #
    # The above dictionary is saved when plugin is called with a ``--saveoutputmeta``
    # flag. Note also that all file paths are relative to the system specified
    # output directory.
    OUTPUT_META_DICT = {}

    def define_parameters(self):
        """
        Define the CLI arguments accepted by this plugin app.
        Use self.add_argument to specify a new app argument.
        """
        self.add_argument('-r', dest='resolution', type=str, optional=False, help='The desired resolution of the slideshow', default='1280x720')

    def run(self, options):
        """
        Define the code to be run by this plugin app.
        """
        print(Gstr_title)
        print('Version: %s' % self.get_version())

        TMP_IMAGE_PATH = "/tmp/resized-images"

        # Make the directory for the resized images if it doesn't already exist
        if not os.path.exists(TMP_IMAGE_PATH):
            os.mkdir(TMP_IMAGE_PATH)

        # Divide the commands among the workers equally
        commands = [[]]
        num_workers = int(os.environ['NUMBER_OF_WORKERS'])
        files = [f for f in os.listdir(options.inputdir) if isfile(join(options.inputdir, f))]
        files_per_worker = int(len(files)/num_workers)
        remainder = len(files) % num_workers
        i = 0
        for j, f in enumerate(files):
            if len(commands[i]) >= files_per_worker:
                i += 1
                commands.append([])
                if i == num_workers - remainder:
                    files_per_worker += 1
            commands[i].append("convert {} -thumbnail {} -background black -gravity center -extent {} {}.png".format(join(options.inputdir, f), options.resolution, options.resolution, join(TMP_IMAGE_PATH, str(j))))
        print(commands)

        # Start the workers and run the commands.The commands should be passed as a list of lists of lists of strings. See the documentation for a more in-depth explanation of how commands should be passed.
        try:
            parallel.run_commands([commands, [["cat {} | ffmpeg -y -f image2pipe -r 1 -i - -vcodec libx264 {}/out.mp4".format(join(TMP_IMAGE_PATH, "*"), options.outputdir)]]])
        except:
            print("An error occurred")
        finally:
            if os.path.exists(TMP_IMAGE_PATH):
                shutil.rmtree(TMP_IMAGE_PATH)
        
    def show_man_page(self):
        """
        Print the app's man page.
        """
        print(Gstr_synopsis)


# ENTRYPOINT
if __name__ == "__main__":
    chris_app = Slideshow()
    chris_app.launch()
