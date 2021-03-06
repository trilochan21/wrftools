""" Submit specified job scripts

Config comes from a file, specified as --config argument. Some configuration options (listed below) 
can also be given at the command line, where they will override the configuration file. 
See example/templater.yaml for a full list of configuration options. 


Usage:
    fill_templates.py [--config=<file>] [options]
    
Options:
    --config=<file>         yaml/json file specifying configuration options
    --start=<time>          an initial time to work with, if not specified, time will be caculated from base-time, delay and cycles
    --base-time=<time>      a base-time to calculate start time from, if not present, system time is used
    --delay=<hours>         number of hours delay to apply to base-time
    --cycles=<hours>        list of hours to restrict start times to e.g. [0,12]
    --end=<time>            an end time for the simulation blocks
    --init-interval=<hours> number of hours between initialistions
    --working-dir=<dir>     working directory specifier which may contain date and time placeholders, see below
    --template-dir=<dir>
    --template-expr=<expr>  expression in templates which indicates placeholder to be expanded (default <%s>)
    --after-job=<job>       supplied job id or job name will be given as as dependency for first job
    --dry-run               log but don't execute commands
    --log.level=<level>     log level info, debug or warn (see python logging modules)
    --log.format=<fmt>      log format code (see python logging module)
    --log.file=<file>       optional log file
    --help                  display documentation
    
The above options can all be given at the command line. Jobs must be specified inside a configuration file. See config/templater.yaml for
an example"""

LOGGER="wrftools"

import sys
import loghelper
from dateutil import rrule
import confighelper as conf
from wrftools import substitute
from wrftools import templater as tm
import json

DEFAULT_TEMPLATE_EXPR = '<%s>'   


def main():
    # merge command-line and file-specified arguments
    config = conf.config(__doc__, sys.argv[1:])

    
    logger = loghelper.create(LOGGER, log_level=config.get('log.level'), log_fmt=config.get('log.format'))
    
    if config.get('log.file'):
        log_file = config['log.file']
        logger.addHandler(loghelper.file_handler(log_file, config['log.level'], config['log.format']))
    
    dry_run = config.get('dry-run')
    
    # either the start time is exactly specified, or else we calculate it from base time, delay and cycles
    if config.get('start'):
        init_time = config['start']
    else:
        init_time = shared.get_time(base_time=config.get('base-time'), delay=config.get('delay'), round=config.get('cycles'))
        

    if config.get('end'):
        end_init = config['end']
        init_interval = config['init_interval']
        init_times = list(rrule.rrule(freq=rrule.HOURLY, interval=init_interval, dtstart=init_time, until=end_init))
    else:
        init_times = [init_time]

    for init_time in init_times:
        # one-argument function to do initial-time substitution in strings
        expand = lambda s : substitute.sub_date(str(s), init_time=init_time)
        replacements = substitute.date_replacements(init_time=init_time)
    
        jobs = config['jobs']
        # get an ordered list of all the ones which we will run
        run_jobs = [jobs[j] for j in sorted(jobs.keys()) if jobs[j]['run']==True]
        #for key, entry in config['jobs'].items():
        for entry in run_jobs:
            template = expand(entry['template'])
            target = expand(entry['target'])
            tm.fill_template(template, target, replacements)

        
if '__main__' in __name__:
    main()