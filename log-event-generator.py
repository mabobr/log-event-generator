#!/usr/bin/env python3                                                                                                                                                                                            
# -*- coding: utf-8 -*-

# usage: log-event-generator.py [-v] -e /path/2/events/defs.yaml -s /path/2/scenarios/defs.yamp -r scenrio2run [-t time_factor][-c clock_iso_init]
# -v ... verbose
# -t time_factor ... TBD
# -e events_definitions.yaml   - where format of events is defined
# -s scenarios_definition.yaml - where sequences fo events are defined
# -r scenario_to_run           - scenario to execute
# -c clock init time           - e.g. -c "2023-01-22 13:14:15"

import sys, getopt, traceback, os, datetime, yaml, random, re


verbose = False
re_to_nextvar       = re.compile('^(.*?)\$\{(.+?)\}(.*)')
re_idenitifier_ok   = re.compile('^[\w\d\_]+$')
re_seconds          = re.compile('^\s*(\d+)\s*s?\s*$')
re_miliseconds      = re.compile('^\s*(\d+)\s*ms\s*$')
re_number           = re.compile('^\d+$')
re_float            = re.compile('[+-]?\d+(\.\d+)?$')

# https://www.geeksforgeeks.org/getter-and-setter-in-python/
class TimeStamp:
    def __init__(self, a_ts_string):
        self._ts_string = a_ts_string

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

#############################################################
class variableList:
    def __init__(self, varList):
        self._varList = varList

    def show(self, ts_ue = None):
        return random.choice(self._varList)

#############################################################
class aString:
    def __init__(self, a_string):
        self._a_string = a_string

    def show(self, ts_ue = None):
        return self.string

    @property
    def string(self):
        return self._a_string

#############################################################
class anEvent:
    def __init__(self, a_string, events_defs):
        self._a_string = a_string
        self._token_list = []

        string_rest = a_string
        while True:
            re = re_to_nextvar.search(string_rest)
            if re:
                # if group(1) ends with backslash \ and group(2) starts with $ - we have escape
                #debug('GR1='+re.group(1)+':')
                if re.group(1)[-1] == '\\':
                    debug('Escape detected, GR1='+re.group(1)+':')
                    # adding $ to the end
                    head = re.group(1)+'${'
                    obj = aString(head)
                    debug("Event parsing adding string, site 3:"+head)

                    #debug('GR2='+re.group(2))
                    # skipping $ which was added above
                    string_rest =re.group(2)+'}'+re.group(3)
                    #debug('REST='+string_rest)
                    continue

                obj = aString(re.group(1))
                self._token_list.append(obj)
                debug("Event parsing adding string, site 1:"+re.group(1))

                a_var = re.group(2)
                if a_var in events_defs:
                    obj = events_defs[a_var]
                    self._token_list.append(obj)
                    debug("Event parsing adding variable, site 1:"+re.group(2))
                else:
                    raise ValueError("Variable/timestamp used in event is not defined:"+a_var)

                string_rest = re.group(3)
            else:
                obj = aString(string_rest)
                self._token_list.append(obj)
                debug("Event parsing adding string, site 2:"+string_rest)
                break

    # here a show() function must be added

##############################################################
class theClock:
    def __init__(self, init_ue: int = None, timeFactor:float = 1 ):

            if init_ue is None:
                self._current_time = int(datetime.datetime.now().timestamp())
            else:
                self._current_time = init_ue
            if timeFactor is None:
                timeFactor = 1

            self._timefactor = timeFactor

            debug('Clock initialized, NOW='+str(self._current_time)+' ('+ datetime.datetime.fromtimestamp(self._current_time).strftime("%Y-%m-%d %H:%M:%S")+') time factor='+str(self._timefactor))

#############################################################
class scenarioStep:
    def __init__(self, stepName, stepType, stepPtr = None, value = None):
        
        self._name          = stepName
        self._type          = stepType
        self._ptr           = stepPtr
        self._static_vars   = []
        self._wait_in_ms    = 1000
        self._loop_init     = value

        if self._type == 1:
            debug('Scenario step (event) added:'+self._name)
        elif self._type == 2:
            if not(value is None):
                self._wait_in_ms = value
            debug('Scenario step (wait) added: '+str(self._wait_in_ms)+' miliseconds')
        elif self._type == 3:
            self._loop_init = value
            debug('Scenario step (loop) added, loop count= '+str(self._loop_init))
        else:
            raise ValueError("Unimplemented scenarioStep:"+str(self._type))

    def add_static_var( self, varName):
        self._static_vars.append(varName)
        debug('Scenario: added staic variable:'+varName+' to event:'+self._name)
                

############################################################
def is_id_valid(text):

    if re_idenitifier_ok.match(text):
        return True
    return False
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

    if evts_def_file is None:
        return None

    events_defs = {}
    
    debug('Preparing to parse event definition file: '+evts_def_file)
    try:
        with open(evts_def_file, "r") as stream:
            try:
                events_config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                sys.stderr.write(str(exc)+"\n")
                return None
    except FileNotFoundError as exc:
        return None
        
    debug('YAML syntax of '+evts_def_file+' is OK, semantics check follow')

    # check for timestamps
    try:
        if not( isinstance(events_config['timestamps'],dict)):
            sys.stderr.write('timestamps in YAML file:'+evts_def_file+' must be structure/object, not:'+str(type(events_config['timestamps']))+"\n")
            return None
    except KeyError:
        debug('No timestamps present in YAML file:'+evts_def_file)
    else:
        for a_ts in events_config['timestamps']:
            if not is_id_valid(a_ts):
                sys.stderr.write('timestamp '+a_ts+' in YAML file:'+evts_def_file+" not allowed characters in identifier\n")
                return None

            # no dupplicate check - safe_load() fixed YAML problems, but any ID must be unique
            if a_ts in events_defs.keys():
                sys.stderr.write('Dupplicate identfier '+a_ts+' in file:'+evts_def_file)
                return None 

            if not( isinstance(events_config['timestamps'][a_ts],str)):
                sys.stderr.write('In timestamps, in YAML file:'+evts_def_file+' TS='+a_ts+" must be string, not:"+str(type(events_config['timestamps'][a_ts]))+"\n")
                return None

            o_ts = TimeStamp(events_config['timestamps'][a_ts])
            debug('OK timestamp: '+a_ts+' Def='+events_config['timestamps'][a_ts]+' Example='+o_ts.show())
            events_defs[a_ts] = o_ts
              
    # check for variables
    try:
        if not( isinstance(events_config['variables'],dict)):
            sys.stderr.write('variables in YAML file:'+evts_def_file+' must be structure/object, not:'+str(type(events_config['timestamps']))+"\n")
            return None
    except KeyError:
        debug('No variables present in YAML file:'+evts_def_file)
    else:
        for a_var_group in events_config['variables']:
            if not is_id_valid(a_var_group):
                sys.stderr.write('variable group '+a_var_group+' in YAML file:'+evts_def_file+" not allowed characters in identifier\n")
                return None

            # no dupplicate check - safe_load() fixed YAML problems, but any ID must be unique
            if a_var_group in events_defs.keys():
                sys.stderr.write('Dupplicate identfier '+a_var_group+' in file:'+evts_def_file)
                return None
         
            if not( isinstance(events_config['variables'][a_var_group],list)):
                sys.stderr.write('variable group '+a_var_group+' in YAML file:'+evts_def_file+' must be list, not:'+str(type(events_config['timestamps']))+"\n")
                return None

            o_vl = variableList(events_config['variables'][a_var_group])
            events_defs[a_var_group] = o_vl
            debug('OK variable list: '+a_var_group+' Example='+o_vl.show())

    # check events
    try:
        if not( isinstance(events_config['events'],dict)):
            sys.stderr.write('events in YAML file:'+evts_def_file+' must be structure/object, not:'+str(type(events_config['timestamps']))+"\n")
            return None
    except KeyError:
        sys.stderr.write("At least one event in events section must be present in file:"+evts_def_file)   
        return None
    else:
        for an_event in events_config['events']:
            if not is_id_valid(an_event):
                sys.stderr.write('The event '+an_event+' in YAML file:'+evts_def_file+" not allowed characters in identifier\n")
                return None

            # no dupplicate check - safe_load() fixed YAML problems, but any ID must be unique
            if an_event in events_defs.keys():
                sys.stderr.write('Dupplicate identfier '+an_event+' in file:'+evts_def_file)
                return None

            o_evt = anEvent(events_config['events'][an_event], events_defs)
            events_defs[an_event] = o_evt
            debug('OK event: '+an_event)

    debug('Syntax and semantics of file '+evts_def_file+' is OK, continue')
    return events_defs

############################################################
def parse_scenarios( scenario_yaml_file, scenario2run, events_defs):

    if scenario_yaml_file is None:
        return None

    scenarios_defs = {}
    
    debug('Preparing to parse scenario definition file: '+scenario_yaml_file)
    try:
        with open(scenario_yaml_file, "r") as stream:
            try:
                scenarios_config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                sys.stderr.write(str(exc)+"\n")
                return None
    except FileNotFoundError as exc:
        return None
        
    debug('YAML syntax of '+scenario_yaml_file+' is OK, semantics check follow, scenario 2 run='+scenario2run)

    if not is_id_valid(scenario2run):
        sys.stderr.write('The scenario '+scenario2run+' in YAML file:'+scenario_yaml_file+" not allowed characters in identifier\n")
        return None

    if not(scenario2run in scenarios_config.keys()):
        sys.stderr.write('The scenario to run '+scenario2run+' not found in YAML file:'+scenario_yaml_file+" , check -r parameter\n")
        return None

    scenario_l = parse_scenarios_rec( scenarios_config[scenario2run], events_defs, [] )
    if scenario_l is None:
        return None

    debug('OK scenario:'+scenario2run)
    return scenario_l

############################################################
def parse_scenarios_rec( a_scenario_cfg, events_defs, scenario_l ):
    
    # a scenario is just list of events waitlables and loops
    if not(isinstance(a_scenario_cfg,list)):
        sys.stderr.write('A scenario to run must be list, check scenarios in -s parameter file, type is:'+str(type(a_scenario_cfg))+"\n")
        return None

    for scenario_step in a_scenario_cfg:
        if isinstance(scenario_step, str):          
            debug('The scenario step: simple event: '+scenario_step)
            if not(scenario_step in events_defs):
                sys.stderr.write('The event '+scenario_step+' is not defined anywhere, check content of -e YAML file'+"\n")
                return None
            scenario_l.append(scenarioStep(scenario_step, 1, events_defs[scenario_step]))
            
        elif isinstance(scenario_step, dict):
            for scenario_dict_entry in scenario_step.keys():
                if isinstance(scenario_dict_entry, int) or re_number.match(scenario_dict_entry):
                    # number found, it is considered as a list
                    loop_value = int(scenario_dict_entry)
                    loop_l = scenario_step[scenario_dict_entry]
                    if isinstance(loop_l, list):
                        debug('LOOP list, cnt='+str(loop_value))

                        list_o = parse_scenarios_rec(loop_l, events_defs, [])
                        scenario_l.append( scenarioStep('LOOP:'+str(loop_value), 3, list_o, loop_value) )
                    else:
                        sys.stderr.write("Problem with LOOP, LOOPs must be lists, check in -s YAML file\n")
                        return None

                elif scenario_dict_entry == 'wait':
                    wait_value = scenario_step[scenario_dict_entry]
                    re = re_seconds.match(wait_value)
                    if re:
                        wait_ms = 1000 * int(re.group(1))
                    else:
                        re = re_miliseconds.match(wait_value)
                        if re:
                            wait_ms = int(re.group(1))
                        else:
                            sys.stderr.write('Problem with wait value:'+wait_value+', check content of -s YAML file'+"\n")
                            return None

                    scenario_l.append( scenarioStep(None, 2, None, wait_ms) )    
                else:
                    # this must be an event
                    if not(scenario_dict_entry in events_defs):
                        sys.stderr.write('The event '+scenario_dict_entry+' is not defined anywhere, check content of -e YAML file'+"\n")
                        return None
                    if isinstance(scenario_step[scenario_dict_entry], list):
                        # the event has list of "static" variables
                        obj = scenarioStep(scenario_dict_entry, 1, events_defs[scenario_dict_entry])
                        for a_static_var in scenario_step[scenario_dict_entry]:
                            if a_static_var in events_defs:
                                obj.add_static_var(a_static_var)
                            else:
                                sys.stderr.write('The variable '+a_static_var+' is not defined anywhere, check content of -e YAML file'+"\n")
                                return None
                        scenario_l.append(obj)
                    else:
                        sys.stderr.write('For the event '+scenario_dict_entry+' only list is expected, it is list of static variables')
                        return None

                    debug('Scenario: OK added event:'+scenario_dict_entry)

        else:
            sys.stderr.write('Only strinf or dictionaries/object are alloved as lit member for scenarios, check item '+scenario_step+' in -s file'+"\n")

    return scenario_l
        

############################################################
def main():
    global verbose

    events_defs         = None
    events_defs_file    = None
    scenario_defs       = None
    scenario_defs_file  = None
    scenario2run        = None
    timeFactor          = "1"
    clock_init_ue       = None

    try:
        opts, args = getopt.getopt(sys.argv[1:],"vdhe:s:r:t:c:")
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
                events_defs_file = a        
            elif o == '-s':
                scenario_defs_file = a
            elif o == '-r':
                scenario2run = a
            elif o == '-t':
                timeFactor = a
            elif o == '-c':
                clock_init_ue = a
            else:
                usage('Internal, unhandled option:'+o)
                return 1

    if scenario2run is None:
        usage('Parameter -r is missing')
        return 1

    events_defs = parse_event_definitions(events_defs_file)
    if events_defs is None:
        usage('Parameter -e is missing, or YAML file is not correct')
        return 1

    scenario_defs = parse_scenarios( scenario_defs_file, scenario2run, events_defs)
    if scenario_defs is None:
        usage('Parameter -s is missing, or scenario definition YAML file is not correct')
        return 1

    re = re_float.match(timeFactor)
    if not(clock_init_ue is None):
        # conversion from YYYY-MM-DD HH:MM:SS to UE
        try:
            date_object = datetime.datetime.strptime(clock_init_ue, "%Y-%m-%d %H:%M:%S")
        except Exception as err:
            sys.stderr.write(str(err)+"\n")
            sys.stderr.write(traceback.format_exc())
            usage('Parameter -c expects QUOTED date-time in form YYYY-MM-DD HH:MM:SS  e.g. -s "2023-01-23 12:14:15"')
            return 1
        clock_init_ue = int(date_object.timestamp())

    runtimeClock = theClock(clock_init_ue, timeFactor)

    # running scenario - CONTINUE HERE
    raise ValueError("Here to continue with coding")

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

