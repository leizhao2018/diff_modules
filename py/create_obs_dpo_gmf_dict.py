#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 15 13:09:10 2019
output file.p,inthere have subdictionary to save every modules data in file.p
@author: leizhao
"""
import pandas as pd
from datetime import datetime
import time
import multipy_modules as mm
import numpy as np
try:
    import cPickle as pickle
except ImportError:
    import pickle
import sys
    
def read_telemetrystatus(path_name):
    """read the telementry_status, then return the useful data"""
    data=pd.read_csv(path_name)
    #find the data lines number in the file('telemetry_status.csv')
    for i in range(len(data['vessel (use underscores)'])):
        if data['vessel (use underscores)'].isnull()[i]:
            data_line_number=i
            break
    #read the data about "telemetry_status.csv"
    telemetrystatus_df=pd.read_csv(path_name,nrows=data_line_number)
    as_list=telemetrystatus_df.columns.tolist()
    idex=as_list.index('vessel (use underscores)')
    as_list[idex]='Boat'
    telemetrystatus_df.columns=as_list
    for i in range(len(telemetrystatus_df)):
        telemetrystatus_df['Boat'][i]=telemetrystatus_df['Boat'][i].replace("'","")
        if not telemetrystatus_df['Lowell-SN'].isnull()[i]:
            telemetrystatus_df['Lowell-SN'][i]=telemetrystatus_df['Lowell-SN'][i].replace('，',',')
        if not telemetrystatus_df['logger_change'].isnull()[i]:
            telemetrystatus_df['logger_change'][i]=telemetrystatus_df['logger_change'][i].replace('，',',')
    return telemetrystatus_df

def read_telemetry(path='https://www.nefsc.noaa.gov/drifter/emolt.dat',endtime=datetime.now()):
    """read the telemetered data and fix a standard format, the return the standard data"""
    while True:
        tele_df=pd.read_csv(path,sep='\s+',names=['vessel_n','esn','month','day','Hours','minutes','fracyrday',\
                                          'lon','lat','dum1','dum2','depth','rangedepth','timerange','temp','stdtemp','year'])
        if int(tele_df['year'][len(tele_df)-2])==endtime.year:
            break
        else:
            print('check the web:https://www.nefsc.noaa.gov/drifter/emolt.dat.')
            time.sleep(600)
    return tele_df

def classify_by_boat(telemetry_status,start_time,end_time,dict):
    """function: get the Doppio, GoMOLFs, FVCOM, Climate values
    input telemetry status path and filename"""
    try:
        tele_dict=dict['tele_dict']#obervation dictionary, there have every vessel data. 
        Doppio_dict=dict['Doppio']#Doppio dictionary use to store doppio data
        GoMOLFs_dict=dict['GoMOLFs']#GoMOLFs dictionary use to store Gomolfs data 
        FVCOM_dict=dict['FVCOM']  #FVCOM dictionary use to store FVCOM data
        start_time=dict['end_time']  # if dict['end_time'] is wrong, please comment this code
        CrmClim_dict=dict['CrmClim']#CrmClim dictionary use to store climate history data and 
    except KeyboardInterrupt:
        sys.exit()
    except:# if input dictionary is empty, we need creat a new dictionary 
        dict={}
        tele_dict={}
        Doppio_dict={}
        GoMOLFs_dict={}
        FVCOM_dict={}
        CrmClim_dict={}
    telemetrystatus_df=read_telemetrystatus(telemetry_status)# read the telemetry status data
    #download the data of telementry
    tele_df=read_telemetry()   #tele_df means telemeterd data, this data from website 'https://www.nefsc.noaa.gov/drifter/emolt.dat',we should avoid the update time when we use this function
    #screen out the data of telemetry in interval
    valuable_tele_df=pd.DataFrame(data=None,columns=['vessel_n','esn','time','lon','lat','depth','temp'])#use to save the data from start time to end time
    for i in range(len(tele_df)):
        tele_time_str=str(tele_df['year'].iloc[i])+'-'+str(tele_df['month'].iloc[i])+'-'+str(tele_df['day'].iloc[i])+' '+\
                                         str(tele_df['Hours'].iloc[i])+':'+str(tele_df['minutes'].iloc[i])+':'+'00'# the string of observation time
        tele_time=datetime.strptime(tele_time_str,'%Y-%m-%d %H:%M:%S') #chang the observation time format as datetime.datetime. it is convenient to compare with start time and end time.
        if start_time<tele_time<=end_time:# grab the data that time between start time and end time
            valuable_tele_df=valuable_tele_df.append(pd.DataFrame(data=[[tele_df['vessel_n'][i],tele_df['esn'][i],tele_time,tele_df['lon'][i],\
                                                                         tele_df['lat'][i],tele_df['depth'][i],tele_df['temp'][i]]],\
                                                                       columns=['vessel_n','esn','time','lon','lat','depth','temp']))
    #clean the index of valuable telementry data
    if len(valuable_tele_df)>0:
        valuable_tele_df.index=range(len(valuable_tele_df)) 
        dict['end_time']=valuable_tele_df['time'][len(valuable_tele_df)-1]
    for j in range(len(telemetrystatus_df)):# loop boat name, If the name is new, then you need to create a new dataframe for the new name.
        if telemetrystatus_df['Boat'][j] not in tele_dict.keys():
            tele_dict[telemetrystatus_df['Boat'][j]]=pd.DataFrame(data=None,columns=['time','temp','depth','lat','lon'])
        if telemetrystatus_df['Boat'][j] not in Doppio_dict.keys():
            Doppio_dict[telemetrystatus_df['Boat'][j]]=pd.DataFrame(data=None,columns=['time','temp','depth','lat','lon'])
        if telemetrystatus_df['Boat'][j] not in GoMOLFs_dict.keys():
            GoMOLFs_dict[telemetrystatus_df['Boat'][j]]=pd.DataFrame(data=None,columns=['time','temp','depth','lat','lon'])
        if telemetrystatus_df['Boat'][j] not in FVCOM_dict.keys():
            FVCOM_dict[telemetrystatus_df['Boat'][j]]=pd.DataFrame(data=None,columns=['time','temp','depth','lat','lon'])
        if telemetrystatus_df['Boat'][j] not in CrmClim_dict.keys():
            CrmClim_dict[telemetrystatus_df['Boat'][j]]=pd.DataFrame(data=None,columns=['time','temp','depth','lat','lon'])
        dop_nu,gmf_nu,tele_nu,fvc_nu,crmclim_nu=[],[],[],[],[] # creat multiple list use to store data('time','temp','depth','lat','lon')
        for i in valuable_tele_df.index:  #valuable_tele_df is the valuable telemetry data during start time and end time 
            if int(valuable_tele_df['vessel_n'][i].split('_')[1])==telemetrystatus_df['Vessel#'][j]:
                ptime=valuable_tele_df['time'][i] # the observation time
                latpt=float(valuable_tele_df['lat'][i]) # the lat of observation
                lonpt=float(valuable_tele_df['lon'][i]) #the lon of observation
                depthpt=float(valuable_tele_df['depth'][i]) #the depth of observation
                tele_nu.append([ptime,latpt,lonpt,float(valuable_tele_df['temp'][i]),depthpt]) #store the data of observation
                try:     #try to get doppio data in the same location
                    dpo_temp,dpo_depth=mm.get_doppio(latp=latpt,lonp=lonpt,depth=depthpt,dtime=ptime,fortype='tempdepth') 
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    dpo_temp,dpo_depth=np.nan,np.nan
                dop_nu.append([ptime,latpt,lonpt,dpo_temp,dpo_depth]) #store the data of doppio
                try:    #try to get the gomofs data in the same location
                    gmf_temp,gmf_depth=mm.get_gomofs(dtime=ptime,latp=latpt,lonp=lonpt,depth=depthpt,fortype='tempdepth')
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    gmf_temp,gmf_depth=np.nan,np.nan
                gmf_nu.append([ptime,latpt,lonpt,gmf_temp,gmf_depth]) #store the data of GoMOLFs
                try:
                    FV_temp,FV_depth=mm.get_FVCOM_temp(latp=latpt,lonp=lonpt,dtime=ptime,depth=depthpt,fortype='tempdepth')
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    FV_temp,FV_depth=np.nan,np.nan
                fvc_nu.append([ptime,latpt,lonpt,FV_temp,FV_depth]) # store the data of FVCOM
                try:
                    crm_depth=mm.get_depth_bathy(loni=lonpt,lati=latpt)
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    crm_depth=np.nan   
                try:
                    climtemp=mm.getclim(lat1=latpt,lon1=lonpt,dtime=ptime)
                except KeyboardInterrupt:
                    sys.exit()
                except:
                    climtemp=np.nan
                crmclim_nu.append([ptime,latpt,lonpt,climtemp,crm_depth]) #store the data of climate history and ngdc

                valuable_tele_df=valuable_tele_df.drop(i)  #if this line has been classify, delete this line
        #addthe data to the dataframe accroding every list
        if len(dop_nu)>0:
            Doppio_dict[telemetrystatus_df['Boat'][j]]=Doppio_dict[telemetrystatus_df['Boat'][j]].append(pd.DataFrame(data=dop_nu,\
                            columns=['time','lat','lon','temp','depth']),ignore_index=True)
        if len(gmf_nu)>0:
            GoMOLFs_dict[telemetrystatus_df['Boat'][j]]=GoMOLFs_dict[telemetrystatus_df['Boat'][j]].append(pd.DataFrame(data=gmf_nu,\
                            columns=['time','lat','lon','temp','depth']),ignore_index=True)
        if len(tele_nu)>0:
            tele_dict[telemetrystatus_df['Boat'][j]]=tele_dict[telemetrystatus_df['Boat'][j]].append(pd.DataFrame(data=tele_nu,\
                            columns=['time','lat','lon','temp','depth']),ignore_index=True)
        if len(fvc_nu)>0:
            FVCOM_dict[telemetrystatus_df['Boat'][j]]=FVCOM_dict[telemetrystatus_df['Boat'][j]].append(pd.DataFrame(data=fvc_nu,\
                            columns=['time','lat','lon','temp','depth']),ignore_index=True)
        if len(crmclim_nu)>0:
            CrmClim_dict[telemetrystatus_df['Boat'][j]]=CrmClim_dict[telemetrystatus_df['Boat'][j]].append(pd.DataFrame(data=crmclim_nu,\
                            columns=['time','lat','lon','temp','depth']),ignore_index=True)
    # add every module's data to the dicitonary        
    dict['tele_dict']=tele_dict
    dict['Doppio']=Doppio_dict
    dict['GoMOLFs']=GoMOLFs_dict
    dict['FVCOM']=FVCOM_dict
    dict['CrmClim']=CrmClim_dict
    obsdpogmf=dict
    for i in obsdpogmf['tele_dict'].keys():  # check the data, whether there have some repeat, if there have keep the last one.
        if len(obsdpogmf['tele_dict'][i])>0:
            obsdpogmf['tele_dict'][i].drop_duplicates(subset=['time'],keep='last',inplace=True)
            obsdpogmf['tele_dict'][i].index=range(len(obsdpogmf['tele_dict'][i]))
            obsdpogmf['Doppio'][i].drop_duplicates(subset=['time'],keep='last',inplace=True)
            obsdpogmf['Doppio'][i].index=range(len(obsdpogmf['Doppio'][i]))
            obsdpogmf['GoMOLFs'][i].drop_duplicates(subset=['time'],keep='last',inplace=True)
            obsdpogmf['GoMOLFs'][i].index=range(len(obsdpogmf['GoMOLFs'][i]))
            obsdpogmf['FVCOM'][i].drop_duplicates(subset=['time'],keep='last',inplace=True)
            obsdpogmf['FVCOM'][i].index=range(len(obsdpogmf['FVCOM'][i]))
            obsdpogmf['CrmClim'][i].drop_duplicates(subset=['time'],keep='last',inplace=True)
            obsdpogmf['CrmClim'][i].index=range(len(obsdpogmf['CrmClim'][i]))
    return obsdpogmf



def main():
    telemetry_status='/home/jmanning/leizhao/programe/diff_modules/parameter/telemetry_status.csv'  # download from web:'https://docs.google.com/spreadsheets/d/1uLhG_q09136lfbFZppU2DU9lzfYh0fJYsxDHUgMB1FM/edit?ts=5ba8fe2b#gid=0'
    start_time_str='2019-4-12'  #
    start_time=datetime.strptime(start_time_str,'%Y-%m-%d')    
    end_time=datetime.now()
    filepathread='/home/jmanning/leizhao/programe/diff_modules/result/data_dict/dict_obsdpogmf0529.p' #filepath and filename of old dictionary 
    filepathsave='/home/jmanning/leizhao/programe/diff_modules/result/data_dict/dict_obsdpogmf0529.p'# filepath and filename of dictionary
    try: #read dictionary
        with open(filepathread,'rb') as fp:
            dict = pickle.load(fp)
    except KeyboardInterrupt:
        sys.exit()
    except: 
        dict={}  
    obsdpogmf=classify_by_boat(telemetry_status,start_time,end_time,dict)
    with open(filepathsave,'wb') as fp:  #save the dictionary
        pickle.dump(obsdpogmf,fp,protocol=pickle.HIGHEST_PROTOCOL)
if __name__=='__main__':
    main()
    

