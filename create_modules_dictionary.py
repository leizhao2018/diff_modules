#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 15 13:09:10 2019
output file.p,inthere have subdictionary to save every modules data in file.p
@author: leizhao
"""
import pandas as pd
from datetime import datetime,timedelta
import time
import multipy_modules as mm
import numpy as np
import json
import sys
import os
    
def read_telemetrystatus(path_name):
    """read the telementry_status, then return the useful data"""
    data=pd.read_csv(path_name)
    #find the data lines number in the file('telemetry_status.csv')
    for i in range(len(data['Unnamed: 0'])):
        if data['Unnamed: 0'].isnull()[i]:
            data_line_number=i
            break
    #read the data about "telemetry_status.csv"
    telemetrystatus_df=pd.read_csv(path_name,nrows=data_line_number)
    as_list=telemetrystatus_df.columns.tolist()
    idex=as_list.index('Unnamed: 0')
    as_list[idex]='Boat'
    telemetrystatus_df.columns=as_list
    for i in range(len(telemetrystatus_df)):
        telemetrystatus_df['Boat'][i]=telemetrystatus_df['Boat'][i].replace("'","")
        if not telemetrystatus_df['Lowell-SN'].isnull()[i]:
            telemetrystatus_df['Lowell-SN'][i]=telemetrystatus_df['Lowell-SN'][i].replace('，',',')
        if not telemetrystatus_df['logger_change'].isnull()[i]:
            telemetrystatus_df['logger_change'][i]=telemetrystatus_df['logger_change'][i].replace('，',',')
    return telemetrystatus_df




def create_storedictionary(dictionary):
    '''function: give a empty dictionary, use to create the subdictionary'''
    dictionary['lat']={}
    dictionary['lon']={}
    dictionary['observation_T']={}
    dictionary['observation_H']={}
    dictionary['Doppio_T']={}
    dictionary['Doppio_H']={}
    dictionary['GoMOLFs_T']={}
    dictionary['GoMOLFs_H']={}
    dictionary['FVCOM_T']={}
    dictionary['FVCOM_H']={}
    dictionary['Clim_T']={}
    dictionary['NGDC_H']={}
    return dictionary


def classify_by_boat(telemetry_status,start_time,end_time,dictionary):
    """function: get the Doppio, GoMOLFs, FVCOM, Climate values
    input telemetry status path and filename"""
    try:
        start_time_str=dictionary['end_time']  # if dict['end_time'] is wrong, please comment this code
        start_time=datetime.strptime(start_time_str,'%Y-%m-%d %H:%M:%S')
    except:
        start_time=start_time    
    telemetrystatus_df=read_telemetrystatus(telemetry_status)# read the telemetry status data
    emolt_df=read_emolt(start=start_time,end=end_time)   #emolt_df means emolt data, this data from website 'https://www.nefsc.noaa.gov/drifter/emolt.dat',we should avoid the update time when we use this function
    #clean the index of valuable telementry data
    if len(emolt_df)>0:
        emolt_df.index=range(len(emolt_df)) 
        dictionary['end_time']=str(emolt_df['time'][len(emolt_df)-1])
    for j in range(len(telemetrystatus_df)):# loop boat name, If the name is new, then you need to create a new dataframe for the new name.
        vessel_name=telemetrystatus_df['Boat'][j]
        if vessel_name not in dictionary.keys():
            dictionary[vessel_name]={}#create a new dictionary under dictionary
            dictionary[vessel_name]=create_storedictionary(dictionary[vessel_name])# create mutiple subdictionary under dicitonary.
        
        for i in emolt_df.index:  #valuable_tele_df is the valuable telemetry data during start time and end time 
            if int(emolt_df['vessel_n'][i].split('_')[1])==telemetrystatus_df['Vessel#'][j]:
                ptime=emolt_df['time'][i] # the observation time
                latpt=float(emolt_df['lat'][i]) # the lat of observation
                lonpt=float(emolt_df['lon'][i]) #the lon of observation
                depthpt=float(emolt_df['depth'][i]) #the depth of observation
                temppt=float(emolt_df['temp'][i])
                try:     #try to get doppio data in the same location
                    dpo_temp,dpo_depth=mm.get_doppio(latp=latpt,lonp=lonpt,depth=depthpt,dtime=ptime,fortype='tempdepth') 
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    dpo_temp,dpo_depth=np.nan,np.nan
                try:    #try to get the gomofs data in the same location
                    gmf_temp,gmf_depth=mm.get_gomofs(dtime=ptime,latp=latpt,lonp=lonpt,depth=depthpt,fortype='tempdepth')
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    gmf_temp,gmf_depth=np.nan,np.nan
                try:
                    FV_temp,FV_depth=mm.get_FVCOM_temp(latp=latpt,lonp=lonpt,dtime=ptime,depth=depthpt,fortype='tempdepth')
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    FV_temp,FV_depth=np.nan,np.nan
                try:
                    ngdc_depth=mm.get_depth_bathy(loni=lonpt,lati=latpt)
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    ngdc_depth=np.nan   
                try:
                    climtemp=mm.getclim(lat1=latpt,lon1=lonpt,dtime=ptime)#store the data of climate history and ngdc
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    climtemp=np.nan
                data_list=[latpt,lonpt,float(temppt),float(depthpt),float(dpo_temp),float(dpo_depth),float(gmf_temp),float(gmf_depth),float(FV_temp),float(FV_depth),float(climtemp),float(ngdc_depth)]
                dictionary[vessel_name]=store_data(key=str(ptime),data_list=data_list,dictionary=dictionary[vessel_name])
                emolt_df=emolt_df.drop(i)  #if this line has been classify, delete this line
    return dictionary

def store_data(key,data_list,dictionary):
    '''give a list and key, store the value in the ditionary'''
    dictionary['lat'][key]=data_list[0]
    dictionary['lon'][key]=data_list[1]
    dictionary['observation_T'][key]=data_list[2]
    dictionary['observation_H'][key]=data_list[3]
    dictionary['Doppio_T'][key]=data_list[4]
    dictionary['Doppio_H'][key]=data_list[5]
    dictionary['GoMOLFs_T'][key]=data_list[6]
    dictionary['GoMOLFs_H'][key]=data_list[7]
    dictionary['FVCOM_T'][key]=data_list[8]
    dictionary['FVCOM_H'][key]=data_list[9]
    dictionary['Clim_T'][key]=data_list[10]
    dictionary['NGDC_H'][key]=data_list[11]
    return dictionary

def read_emolt_all(path='https://www.nefsc.noaa.gov/drifter/emolt.dat',endtime=datetime.now()):
    """read the telemetered data and fix a standard format, the return the standard data"""
    while True:
        emolt_df=pd.read_csv(path,sep='\s+',names=['vessel_n','esn','month','day','Hours','minutes','fracyrday',\
                                          'lon','lat','dum1','dum2','depth','rangedepth','timerange','temp','stdtemp','year'])
        if int(emolt_df['year'][len(emolt_df)-2])==endtime.year:
            break
        else:
            print('check the web:https://www.nefsc.noaa.gov/drifter/emolt.dat.')
            time.sleep(600)
    return emolt_df
def read_emolt(start,end,path='https://www.nefsc.noaa.gov/drifter/emolt.dat'):
    '''the start and end is represent the sart time and end time, the format is datetime.datetime'''
    emolt_df=read_emolt_all(path)   #emolt_df means emolt data, this data from website 'https://www.nefsc.noaa.gov/drifter/emolt.dat',we should avoid the update time when we use this function
    #screen out the data of telemetry in interval
    valuable_emolt_df=pd.DataFrame(data=None,columns=['vessel_n','esn','time','lon','lat','depth','temp'])#use to save the data from start time to end time
    for i in range(len(emolt_df)):
        emolt_time_str=str(emolt_df['year'].iloc[i])+'-'+str(emolt_df['month'].iloc[i])+'-'+str(emolt_df['day'].iloc[i])+' '+\
                                         str(emolt_df['Hours'].iloc[i])+':'+str(emolt_df['minutes'].iloc[i])+':'+'00'# the string of observation time
        emolt_time=datetime.strptime(emolt_time_str,'%Y-%m-%d %H:%M:%S') #chang the observation time format as datetime.datetime. it is convenient to compare with start time and end time.
        if start<emolt_time<=end:# grab the data that time between start time and end time
            valuable_emolt_df=valuable_emolt_df.append(pd.DataFrame(data=[[emolt_df['vessel_n'][i],emolt_df['esn'][i],emolt_time,emolt_df['lon'][i],\
                                                                         emolt_df['lat'][i],emolt_df['depth'][i],emolt_df['temp'][i]]],\
                                                                       columns=['vessel_n','esn','time','lon','lat','depth','temp']))
    
    return valuable_emolt_df


def update_dictionary(telemetry_status,start_time,end_time,dictionarypath):
    try: #read dictionary
        with open(dictionarypath,'r') as fp:
            dictionary = json.load(fp)
    except KeyboardInterrupt:
        sys.exit()
    except: 
        dictionary={}  
    #update dictionary 
    obsdpogmf=classify_by_boat(telemetry_status,start_time,end_time,dictionary)
    #save updated dictionary
    with open(dictionarypath, 'w') as fp:
        json.dump(obsdpogmf, fp)
    
    
def main():
    end_time=datetime.now()
    start_time=end_time-timedelta(days=31)
    
    realpath=os.path.dirname(os.path.abspath(__file__))
    parameterpath=realpath[::-1].replace('py'[::-1],'parameter'[::-1],1)[::-1]
    
    telemetry_status=os.path.join(parameterpath,'telemetry_status.csv')  
    # download from web:'https://docs.google.com/spreadsheets/d/1uLhG_q09136lfbFZppU2DU9lzfYh0fJYsxDHUgMB1FM/edit?ts=5ba8fe2b#gid=0' 

    resultpath=realpath[::-1].replace('py'[::-1],'dictionary'[::-1],1)[::-1]
    dictionarypath=os.path.join(resultpath,'dictionary.json') #filepath and filename of old dictionary 
    update_dictionary(telemetry_status,start_time,end_time,dictionarypath)
    
#if __name__=='__main__':
#    main()
