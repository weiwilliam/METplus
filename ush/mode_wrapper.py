#!/usr/bin/env python

'''
Program Name: mode_wrapper.py
Contact(s): George McCabe
Abstract: Runs mode
History Log:  Initial version
Usage: 
Parameters: None
Input Files:
Output Files:
Condition codes: 0 for success, 1 for failure
'''

from __future__ import (print_function, division)

import os
import met_util as util
from compare_gridded_wrapper import CompareGriddedWrapper

class ModeWrapper(CompareGriddedWrapper):

    def __init__(self, p, logger):
        super(ModeWrapper, self).__init__(p, logger)
        self.app_path = os.path.join(self.config.getdir('MET_INSTALL_DIR'),
                                     'bin/mode')
        self.app_name = os.path.basename(self.app_path)
        self.c_dict = self.create_c_dict()

    def add_merge_config_file(self):
        if self.c_dict['MERGE_CONFIG_FILE'] != '':
            self.add_arg('-config_merge {}'.format(self.c_dict['MERGE_CONFIG_FILE']))


    def create_c_dict(self):
        c_dict = super(ModeWrapper, self).create_c_dict()

        c_dict['CONFIG_FILE'] = self.config.getstr('config', 'MODE_CONFIG')
        c_dict['OBS_INPUT_DIR'] = \
          self.config.getdir('OBS_MODE_INPUT_DIR')
        c_dict['OBS_INPUT_TEMPLATE'] = \
          self.config.getraw('filename_templates',
                               'OBS_MODE_INPUT_TEMPLATE')
        c_dict['OBS_INPUT_DATATYPE'] = \
          self.config.getstr('config', 'OBS_MODE_INPUT_DATATYPE', '')
        c_dict['FCST_INPUT_DIR'] = \
          self.config.getdir('FCST_MODE_INPUT_DIR')
        c_dict['FCST_INPUT_TEMPLATE'] = \
          self.config.getraw('filename_templates',
                               'FCST_MODE_INPUT_TEMPLATE')
        c_dict['FCST_INPUT_DATATYPE'] = \
          self.config.getstr('config', 'FCST_MODE_INPUT_DATATYPE', '')
        c_dict['OUTPUT_DIR'] = self.config.getdir('MODE_OUT_DIR')
        c_dict['ONCE_PER_FIELD'] = True
        c_dict['QUILT'] = self.config.getbool('config', 'MODE_QUILT', False)
        fcst_conv_radius, obs_conv_radius = self.handle_fcst_and_obs_field('MODE_CONV_RADIUS',
                                                                           'MODE_FCST_CONV_RADIUS',
                                                                           'MODE_OBS_CONV_RADIUS', '5')
        c_dict['FCST_CONV_RADIUS'] = fcst_conv_radius
        c_dict['OBS_CONV_RADIUS'] = obs_conv_radius

        fcst_conv_thresh, obs_conv_thresh = self.handle_fcst_and_obs_field('MODE_CONV_THRESH',
                                                                           'MODE_FCST_CONV_THRESH',
                                                                           'MODE_OBS_CONV_THRESH', '>0.5')

        c_dict['FCST_CONV_THRESH'] = fcst_conv_thresh
        c_dict['OBS_CONV_THRESH'] = obs_conv_thresh

        fcst_merge_thresh, obs_merge_thresh = self.handle_fcst_and_obs_field('MODE_MERGE_THRESH',
                                                                             'MODE_FCST_MERGE_THRESH',
                                                                             'MODE_OBS_MERGE_THRESH', '>0.45')
        c_dict['FCST_MERGE_THRESH'] = fcst_merge_thresh
        c_dict['OBS_MERGE_THRESH'] = obs_merge_thresh
        fcst_merge_flag, obs_merge_flag = self.handle_fcst_and_obs_field('MODE_MERGE_FLAG',
                                                                         'MODE_FCST_MERGE_FLAG',
                                                                         'MODE_OBS_MERGE_FLAG', 'THRESH')

        c_dict['FCST_MERGE_FLAG'] = fcst_merge_flag
        c_dict['OBS_MERGE_FLAG'] = obs_merge_flag
        c_dict['ALLOW_MULTIPLE_FILES'] = False

        c_dict['MERGE_CONFIG_FILE'] = self.config.getstr('config', 'MODE_MERGE_CONFIG_FILE', '')

        # if window begin/end is set specific to mode, override
        # OBS_WINDOW_BEGIN/END
        if self.config.has_option('config', 'OBS_MODE_WINDOW_BEGIN'):
            c_dict['OBS_WINDOW_BEGIN'] = \
              self.config.getint('config', 'OBS_MODE_WINDOW_BEGIN')
        if self.config.has_option('config', 'OBS_MODE_WINDOW_END'):
            c_dict['OBS_WINDOW_END'] = \
              self.config.getint('config', 'OBS_MODE_WINDOW_END')

        # same for FCST_WINDOW_BEGIN/END
        if self.config.has_option('config', 'FCST_MODE_WINDOW_BEGIN'):
            c_dict['FCST_WINDOW_BEGIN'] = \
              self.config.getint('config', 'FCST_MODE_WINDOW_BEGIN')
        if self.config.has_option('config', 'FCST_MODE_WINDOW_END'):
            c_dict['FCST_WINDOW_END'] = \
              self.config.getint('config', 'FCST_MODE_WINDOW_END')

        # check that values are valid
        if not util.validate_thresholds(util.getlist(c_dict['FCST_CONV_THRESH'])):
            self.logger.error('MODE_FCST_CONV_THRESH items must start with a comparison operator (>,>=,==,!=,<,<=,gt,ge,eq,ne,lt,le)')
            exit(1)
        if not util.validate_thresholds(util.getlist(c_dict['OBS_CONV_THRESH'])):
            self.logger.error('MODE_OBS_CONV_THRESH items must start with a comparison operator (>,>=,==,!=,<,<=,gt,ge,eq,ne,lt,le)')
            exit(1)
        if not util.validate_thresholds(util.getlist(c_dict['FCST_MERGE_THRESH'])):
            self.logger.error('MODE_FCST_MERGE_THRESH items must start with a comparison operator (>,>=,==,!=,<,<=,gt,ge,eq,ne,lt,le)')
            exit(1)
        if not util.validate_thresholds(util.getlist(c_dict['OBS_MERGE_THRESH'])):
            self.logger.error('MODE_OBS_MERGE_THRESH items must start with a comparison operator (>,>=,==,!=,<,<=,gt,ge,eq,ne,lt,le)')
            exit(1)

        return c_dict


    def run_at_time_one_field(self, time_info, v):
        """! Runs mode instances for a given time and forecast lead combination
              Overrides run_at_time_one_field function in compare_gridded_wrapper.py
              Args:
                @param time_info dictionary containing timing information
                @param v var_info object containing variable information
        """
        # get model to compare
        model_path = self.find_model(time_info, v)
        if model_path == None:
            self.logger.error("Could not find file in " + self.c_dict['FCST_INPUT_DIR'] +\
                              " for init time " + time_info['init_fmt'] + " f" + str(time_info['lead_hours']))
            return

        # get observation to compare
        obs_path = self.find_obs(time_info, v)
        if obs_path == None:
            self.logger.error("Could not find file in " + self.c_dict['OBS_INPUT_DIR'] +\
                              " for valid time "+time_info['valid_fmt'])
            return

        # loop over all variables and levels (and probability thresholds) and call the app for each
        self.process_fields_one_thresh(time_info, v, model_path, obs_path)


    def process_fields_one_thresh(self, time_info, v, model_path, obs_path):
        """! For each threshold, set up environment variables and run mode
              Args:
                @param time_info dictionary containing timing information
                @param v var_info object containing variable information
                @param model_path forecast file
                @param obs_path observation file
        """
        # if no thresholds are specified, run once
        fcst_thresh_list = [None]
        obs_thresh_list = [None]
        if len(v.fcst_thresh) != 0:
            fcst_thresh_list = v.fcst_thresh
            obs_thresh_list = v.obs_thresh
        elif self.c_dict['FCST_IS_PROB']:
            self.logger.error('Must specify field threshold value to process probabilistic forecast')
            return

        for fthresh, othresh in zip(fcst_thresh_list, obs_thresh_list):
            self.set_param_file(self.c_dict['CONFIG_FILE'])
            self.create_and_set_output_dir(time_info)
            self.add_input_file(model_path)
            self.add_input_file(obs_path)
            self.add_merge_config_file()

            fcst_field = self.get_one_field_info(v.fcst_name, v.fcst_level, v.fcst_extra,
                                                 fthresh, 'FCST')
            obs_field = self.get_one_field_info(v.obs_name, v.obs_level, v.obs_extra,
                                                othresh, 'OBS')

            self.add_env_var("MODEL", self.c_dict['MODEL'])
            self.add_env_var("OBTYPE", self.c_dict['OBTYPE'])
            self.add_env_var("FCST_VAR", v.fcst_name)
            self.add_env_var("OBS_VAR", v.obs_name)
            self.add_env_var("LEVEL", util.split_level(v.fcst_level)[1])
            self.add_env_var("FCST_FIELD", fcst_field)
            self.add_env_var("OBS_FIELD", obs_field)
            self.add_env_var("CONFIG_DIR", self.c_dict['CONFIG_DIR'])
            self.add_env_var("MET_VALID_HHMM", time_info['valid_fmt'][4:8])

            if self.c_dict['QUILT']:
                quilt = "TRUE"
            else:
                quilt = "FALSE"

            self.add_env_var("QUILT", quilt )
            self.add_env_var("FCST_CONV_RADIUS", self.c_dict["FCST_CONV_RADIUS"] )
            self.add_env_var("OBS_CONV_RADIUS", self.c_dict["OBS_CONV_RADIUS"] )
            self.add_env_var("FCST_CONV_THRESH", self.c_dict["FCST_CONV_THRESH"] )
            self.add_env_var("OBS_CONV_THRESH", self.c_dict["OBS_CONV_THRESH"] )
            self.add_env_var("FCST_MERGE_THRESH", self.c_dict["FCST_MERGE_THRESH"] )
            self.add_env_var("OBS_MERGE_THRESH", self.c_dict["OBS_MERGE_THRESH"] )
            self.add_env_var("FCST_MERGE_FLAG", self.c_dict["FCST_MERGE_FLAG"] )
            self.add_env_var("OBS_MERGE_FLAG", self.c_dict["OBS_MERGE_FLAG"] )

            print_list = ["MODEL", "FCST_VAR", "OBS_VAR",
                          "LEVEL", "OBTYPE", "CONFIG_DIR",
                          "FCST_FIELD", "OBS_FIELD",
                          "QUILT", "MET_VALID_HHMM",
                          "FCST_CONV_RADIUS", "FCST_CONV_THRESH",
                          "OBS_CONV_RADIUS", "OBS_CONV_THRESH",
                          "FCST_MERGE_THRESH", "FCST_MERGE_FLAG",
                          "OBS_MERGE_THRESH", "OBS_MERGE_FLAG"]

            self.logger.debug("ENVIRONMENT FOR NEXT COMMAND: ")
            self.print_user_env_items()
            for l in print_list:
                self.print_env_item(l)
            self.logger.debug("COPYABLE ENVIRONMENT FOR NEXT COMMAND: ")
            self.print_env_copy(print_list)

            cmd = self.get_command()
            if cmd is None:
                self.logger.error("Could not generate command")
                return
            self.build()
            self.clear()


    def get_one_field_info(self, v_name, v_level, v_extra, v_thresh, d_type):
        """! Builds the FCST_FIELD or OBS_FIELD items that are sent to the mode config file
              Overrides get_one_field_info in compare_gridded_wrappers.py
              Args:
                @param v_name var_info name
                @param v_level var_info level
                @param v_extra var_info extra arguments
                @param path path to file
                @param thresh probability threshold
                @param d_type type of data (FCST or OBS)
                @return returns a string with field info
        """
        level_type, level = util.split_level(v_level)
        field = ""

#        if d_type == "FCST" and self.c_dict['FCST_IS_PROB']:
        if self.c_dict[d_type+'_IS_PROB']:
            thresh_str = ""
            comparison = util.get_comparison_from_threshold(v_thresh)
            number = util.get_number_from_threshold(v_thresh)
            if comparison in ["gt", "ge", ">", ">=" ]:
                thresh_str += "thresh_lo="+str(number)+";"
            elif comparison in ["lt", "le", "<", "<=" ]:
                thresh_str += "thresh_hi="+str(number)+";"
            # TODO: add thresh??
            if self.c_dict[d_type+'_INPUT_DATATYPE'] == "NETCDF" or \
               self.c_dict[d_type+'_INPUT_DATATYPE'] == "GEMPAK":
                field = "{ name=\"" + v_name + "\"; level=\"" + \
                        level+"\"; prob=TRUE; "
            else:
                field = "{ name=\"PROB\"; level=\""+level_type + \
                          level.zfill(2) + "\"; prob={ name=\"" + \
                          v_name + "\"; " + thresh_str + "} "
        else:
            if self.config.getbool('config', d_type+'_PCP_COMBINE_RUN', False):
                field = "{ name=\""+v_name+"_"+level + \
                             "\"; level=\"(*,*)\"; "
            else:
                field = "{ name=\""+v_name + \
                             "\"; level=\""+v_level+"\"; "

        field += v_extra+" }"
        return field


if __name__ == "__main__":
    util.run_stand_alone("mode_wrapper", "Mode")
