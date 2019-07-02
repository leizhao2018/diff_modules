# -*- coding: utf-8 -*-
"""
Created on Mon May 16 13:02:24 2016

@author: hxu
"""

import matplotlib.pyplot as plt
import matplotlib.dates as dates
import os
import pandas as pd
import numpy as np
from matplotlib.ticker import ScalarFormatter
from pandas import Timedelta
#fn='/home/jmanning/leizhao/programe/aqmain/aq/as/li_7aca_20190530_101130.csv'
#temporary_f_path='/home/jmanning/leizhao/programe/aqmain/aq/as/'
#path='/home/jmanning/leizhao/programe/aqmain/aq/aqu_pic/'
#a=plot_aq(fn,path,temporary_f_path)
def list_all_files(rootdir):
    """get all files' path and name in rootdirectory"""
    _files = []
    list = os.listdir(rootdir) #列出文件夹下所有的目录与文件
    for i in range(0,len(list)):
           path = os.path.join(rootdir,list[i])
           if os.path.isdir(path):
              _files.extend(list_all_files(path))
           if os.path.isfile(path):
              _files.append(path)
    return _files



def plot_aq(fn,path,allfilepng):
    fpath,fname=os.path.split(fn)
    pngname=fname.replace('csv','png')
    fnout=os.path.join(path,pngname)
    allfilelist=list_all_files(path)
    if fnout in allfilelist:
        return ''
    try:
        df=pd.read_csv(fn,sep=',',nrows=5)
    except:
        print ('no data1 in '+fn)
        pic_name=''
        return pic_name
    df.index=df['Probe Type']
    df_id_name=df['Lowell']['Vessel Number']
    tit='Vessel'+df_id_name 
    print ('this is fn : '+fn)
    ######################################
    def parse(datet):
        from datetime import datetime
        #dt=datetime.strptime(datet,'%m/%d/%Y %H:%M:%S PM')
#        dt=datetime.strptime(datet,'%m/%d/%Y %I:%M:%S %p')
        #dt=datetime.strptime(datet,'%H:%M:%S %m/%d/%Y')
        dt=datetime.strptime(datet,'%Y-%m-%d %H:%M:%S')
        return dt
    try: 
        df=pd.read_csv(fn,sep=',',skiprows=9,parse_dates={'datet(GMT)':[1]},index_col='datet(GMT)',date_parser=parse)#creat a new Datetimeindex
    except:
        print ('no data2 in '+fn)
        pic_name=''
        return pic_name
        #continue 
    
    
    #df.index=df.index-pd.tseries.timedeltas.to_timedelta(4, unit='h')  #, chage it to UTC time
    df['yd']=df.index.dayofyear+df.index.hour/24.+df.index.minute/60./24.+df.index.second/60/60./24.-1.0 #creates a yrday0 field
    df=df.loc[(df['Depth(m)']>0.85*np.mean(df['Depth(m)']))]  # get rid of shallow data

    df=df.loc[(df['Temperature(C)']>df.mean()['Temperature(C)']-3*np.std(df['Temperature(C)'])) & (df['Temperature(C)']<np.mean(df['Temperature(C)'])+3*np.std(df['Temperature(C)']))] # reduces time series to deep obs
    for o in list(reversed(range(len(df)))): # usually ,aquetec is collecting data every 1 minute, if the period between two collect above 30 minutes,we get rid of the previous one 
        if (df.index[o]-df.index[o-1])>=pd.Timedelta('0 days 00:30:00') or o==0: 
            df=df.iloc[o:]
            break
    fig=plt.figure(figsize=[9,6])
    ax1=fig.add_subplot(211)
    ax1.plot(df.index,df['Temperature(C)'],'red')
    ax1.set_ylabel('Temperature (Celius)')
    
    try:    
        if max(df.index)-min(df.index)>pd.Timedelta('0 days 04:00:00'):
            ax1.xaxis.set_major_locator(dates.HourLocator(interval=int((max(df.index)-min(df.index)).seconds/3600/6)))# for hourly plot
        else: 
            ax1.xaxis.set_major_locator(dates.MinuteLocator(interval=int((max(df.index)-min(df.index)).seconds/60/6)))# for minutely plot
    except:
        print (fn+'  data is too few')
        pic_name='few data'
        return pic_name
    ax1.xaxis.set_major_formatter(dates.DateFormatter('%D %H:%M'))
    ax1.set_xlabel('')
    try:
        ax1.set_xticklabels([])
    except:
        print (fn+'  data is too few')
        pic_name='few data'
        return pic_name
    ax1.grid()
    ax12=ax1.twinx()
    ax12.set_title(tit)
    ax12.set_ylabel('Fahrenheit')
    ax12.set_xlabel('')
    ax12.set_xticklabels([])
    ax12.set_ylim(np.nanmin(df['Temperature(C)'].values)*1.8+32,np.nanmax(df['Temperature(C)'].values)*1.8+32)
    
    maxtemp=str(int(round(max(df['Temperature(C)'].values),2)*100))
    if len(maxtemp)<4:
        maxtemp='0'+maxtemp
    mintemp=str(int(round(min(df['Temperature(C)'].values),2)*100))
    if len(mintemp)<4:
        mintemp='0'+mintemp
    meantemp=str(int(round(np.mean(df['Temperature(C)'].values),2)*100))
    if len(meantemp)<4:
        meantemp='0'+meantemp
    sdeviatemp=str(int(round(np.std(df['Temperature(C)'].values),2)*100))
    for k in range(4):
      if len(sdeviatemp)<4:
        sdeviatemp='0'+sdeviatemp
    
    time_len=str(int(round((df['yd'][-1]-df['yd'][0]),3)*1000))
    for k in range(3):
        if len(time_len)<3:
            time_len='0'+time_len
    #print time_len
    meandepth=str(abs(int(round(np.mean(df['Depth(m)'].values),0))))
    #print df['depth']
    rangedepth=str(abs(int(round(max(df['Depth(m)'].values-min(df['Depth(m)'].values)),0))))
    for k in range(3):
        if len(rangedepth)<3:
            rangedepth='0'+rangedepth
    #print 'rangedepth'+rangedepth
    
    for k in range(3):
        if len(meandepth)<3:
            meandepth='0'+meandepth
    #print meandepth        
    #print meantemp
    
    ax1.text(0.95, 0.9, 'mean temperature='+str(round(np.mean(df['Temperature(C)'].values*1.8+32),1))+'F',
            verticalalignment='top', horizontalalignment='right',
            transform=ax1.transAxes,
            color='green', fontsize=15)
    ax2=fig.add_subplot(212)
    #df['depth'].plot()
    ax2.plot(df.index,df['Depth(m)'].values)
    ax2.invert_yaxis()
    ax2.set_ylabel('Depth (Meters)')
    #ax2.set_xlabel(df.index[0].year)
    ax2.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
    ax2.grid()
    ax2.set_ylim(max(df['Depth(m)'].values),min(df['Depth(m)'].values))
    ax2.text(0.95, 0.9, 'mean depth='+str(round(np.mean(df['Depth(m)'].values),0))+'m',
            verticalalignment='top', horizontalalignment='right',
            transform=ax2.transAxes,
            color='green', fontsize=15)
    
    ax22=ax2.twinx()
    ax22.set_ylabel('Fathoms')
    ax22.set_ylim(min(df['Depth(m)'].values)/1.8288,max(df['Depth(m)'].values)/1.8288)
    ax22.invert_yaxis()

    if max(df.index)-min(df.index)>Timedelta('0 days 04:00:00'):
        ax1.xaxis.set_major_locator(dates.HourLocator(interval=int((max(df.index)-min(df.index)).seconds/3600/6)))# for hourly plot
    else: 
        ax1.xaxis.set_major_locator(dates.MinuteLocator(interval=int((max(df.index)-min(df.index)).seconds/60/6)))# for minutely plot

    ax2.xaxis.set_major_formatter(dates.DateFormatter('%D %H:%M'))
    plt.gcf().autofmt_xdate()    
    ax2.set_xlabel('Local TIME')
    
    
    
    plt.savefig(fnout)
    plt.savefig(fnout.replace('.png','.ps'),orientation='landscape')
    plt.close()
    pic_name= fnout+'.png'
    return pic_name
    # get file ready for ORACLE

