#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 10:26:09 2019

@author: jmanning
"""

import create_modules_dictionary as cmdd
import aq_main as aq
import os
from datetime import datetime,timedelta

if __name__=='__main__':
    end_time=datetime.now()
    start_time=end_time-timedelta(days=31)
    
    ddir=os.path.dirname(os.path.abspath(__file__))
    dictionarypath=ddir[::-1].replace('py'[::-1],'dictionary'[::-1],1)[::-1]
    parameterpath=ddir[::-1].replace('py'[::-1],'parameter'[::-1],1)[::-1]
    rawstorepath=ddir[::-1].replace('py'[::-1],'aq/aqu_data'[::-1],1)[::-1]
    temporary_f_path=ddir[::-1].replace('py'[::-1],'aq/as'[::-1],1)[::-1]
    
    telemetry_status=os.path.join(parameterpath,'telemetry_status.csv')  
    # download from web:'https://docs.google.com/spreadsheets/d/1uLhG_q09136lfbFZppU2DU9lzfYh0fJYsxDHUgMB1FM/edit?ts=5ba8fe2b#gid=0' 
    codes_file=os.path.join(parameterpath,'codes_temp.dat')# the path and filename of code file
    system='pc'
    # dictionary with endtime,doppio,gomofs,fvcom where each model has vesselname,lat,lon,time,temp
    dictionaryfile=os.path.join(dictionarypath,'dictionary.json') #filepath and filename of old dictionary 
    cmdd.update_dictionary(telemetry_status,start_time,end_time,dictionaryfile)
    aq.make_html(rawstorepath,temporary_f_path,codes_file,system,dictionaryfile,ddir)
