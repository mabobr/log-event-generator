#!/usr/bin/env python3                                                                                                                                                                                            
# -*- coding: utf-8 -*-

# usage: log-event-generator.py [-v]
# -v ... verbose
# -t time_factor ... TBD
# -e events_definitions.yaml   - where format of events is defined
# -s scenarios_definition.yaml - where sequences fo events are defined
# -r scenario_to_run           - scenario to execute

import sys, getopt, traceback, os, datetime, yaml


verbose = False

# https://www.geeksforgeeks.org/getter-and-setter-in-python/
class TimeStamp:
    def __init__(self, a_ts_string):
        self.ts_string = a_ts_string

    def show(self, ts_ue = None):

        if ts_ue is None:
            return str(datetime.datetime.now().astimezone().strftime(self.ts_string))
        else:
           raise ValueError("not implemented")

    @property
    def ts_string(self):
        return self._ts_string

    @ts_string.setter
    def ts_string(self, a_ts_string):
        try:
            ts_inst = datetime.datetime.now().astimezone().strftime(a_ts_string)
        except Exception as exc:
            raise ValueError("strftime() error on input format string:"+a_ts_string)
        self._ts_string = a_ts_string



############################################################
def usage(error_text = None):

    if not( error_text is None):
        sys.stderr.write(error_text+"\n")
    
    sys.stderr.write('usage: '+__file__+" [-v] [-t time_factor] -e /path/to/events/definitions.yaml -s /path/to/scenario/definitions.yaml -r scenario_to_run\n")

############################################################
def debug(text):
    global verbose

    if verbose:
        text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+' ('+str(os.getpid())+') '+text+"\n"
        sys.stderr.write(text)

############################################################
def parse_event_definitions(evts_def_file):

    events_defs = {}
    events_defs['timestamps'] = {}
    events_defs['variables'] = {}

    debug('Preparing to parse event definition file: '+evts_def_file)
    try:
        with open(evts_def_file, "r") as stream:
            try:
                events_defs = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                sys.stderr.write(str(exc)+"\n")
                return None
    except FileNotFoundError as exc:
        return None
        
    debug('YAML syntax of '+evts_def_file+' is OK, semantics check follow')

    # check for timestamps
    try:
        if not( isinstance(events_defs['timestamps'],dict)):
            sys.stderr.write('timestamps in YAML file:'+evts_def_file+' must be structure/object, not:'+str(type(events_defs['timestamps']))+"\n")
            return None
    except KeyError:
        debug('No timestamps present in YAML file:'+evts_def_file)
    else:
        for a_ts in events_defs['timestamps']:
            if not( isinstance(events_defs['timestamps'][a_ts],str)):
                sys.stderr.write('In timestamps, in YAML file:'+evts_def_file+' TS='+a_ts+" must be string, not:"+str(type(events_defs['timestamps'][a_ts]))+"\n")
                return None

            o_ts = TimeStamp(events_defs['timestamps'][a_ts])
            debug('OK timestamp: '+a_ts+' Def='+events_defs['timestamps'][a_ts]+' Example='+o_ts.show())
            events_defs['timestamps'][a_ts] = o_ts
              
    # check for variables
    try:
        if not( isinstance(events_defs['variables'],dict)):
            sys.stderr.write('variables in YAML file:'+evts_def_file+' must be structure/object, not:'+str(type(events_defs['timestamps']))+"\n")
            return None
    except KeyError:
        debug('No variables present in YAML file:'+evts_def_file)
    else:
        for a_var_group in events_defs['variables']:
            if not( isinstance(events_defs['variables'][a_var_groups],list)):
                sys.stderr.write('variable group '+a_var_group+' in YAML file:'+evts_def_file+' must be list, not:'+str(type(events_defs['timestamps']))+"\n")
                return None

            # vyrobit clsaa pre variables a init pre tento zoznam

    debug('Syntax and semantics of file '+evts_def_file+' is OK, continue')
    return events_defs

############################################################
def main():
    global verbose

    events_defs = None

    try:
        opts, args = getopt.getopt(sys.argv[1:],"vdhe:")
    except Exception as err:
        usage(str(err))
        return 1
    else:
        for o, a in opts:
            if o == "-d" or o == "-v":
                verbose=True
                debug('verbose='+str(verbose))
            elif o == '-h':
                usage()
                return 1
            elif o == '-e':
                events_defs = parse_event_definitions(a)
            else:
                usage('Internal, unhandled option:'+o)
                return 1

    if events_defs is None:
        usage('Parameter -e is missing, or YAML file is not correct')
        return 1

    return 0
            
############################################################                                                                                                                                                      
# MAIN                                                                                                                                                                                                            
if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as err:
        sys.stderr.write(str(err)+"\n")
        sys.stderr.write(traceback.format_exc())
        sys.exit(1)

