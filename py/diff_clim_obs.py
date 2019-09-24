"""
Created on Mon Apr 29 13:09:10 2019

@author: leizhao
"""
import json
import sys
import numpy as np
from datetime import datetime,timedelta
import os
import conda
conda_file_dir = conda.__file__
conda_dir = conda_file_dir.split('lib')[0]
proj_lib = os.path.join(os.path.join(conda_dir, 'share'), 'proj')
os.environ["PROJ_LIB"] = proj_lib
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import zlconversions as zl
import time
import pandas as pd
import folium

#import numpy as np # linear algebra
#def check_time(df,start_time,end_time,time_header='time'):
#    '''input dataframe, the interval of start time and end time
#        return a new dataframe ,inside, the time between start time and end time'''
#    for i in range(len(df)):
#        if type(df[time_header][i])==str:
#            df[time_header][i]=datetime.strptime(df[time_header][i],'%Y-%m-%d %H:%M:%S')
#        if start_time<=df[time_header][i]<=end_time:
#            continue
#        else:
#            df=df.drop(i)
#    df.index=range(len(df))
#    return df
def check_time(df,time_header,start_time,end_time):
    '''keep the type of time is datetime
    input start time and end time, return the data between start time and end time'''
    for i in df.index:
        if type(df[time_header][i])==str:
            df[time_header][i]=datetime.strptime(df[time_header][i],'%Y-%m-%d %H:%M:%S')
        if start_time<=df[time_header][i]<=end_time:
            continue
        else:
            df=df.drop(i)
    df=df.dropna()
    df.index=range(len(df))
    return df
def diff(tele_df,M_df):
    """input the dataframe of observation and module
        return:
            the standard different temperature
            the average different temperature
            the average observed temperature 
            the average temperature of modules
    """
    diff=[]
    for j in M_df.index:
        diff.append(tele_df['temp'][j]-M_df['temp'][j])
    stdT=np.std(diff)
    mean_T_diff=np.mean(diff)
    mean_T=np.mean(M_df['temp'][j])
    mean_lat=np.mean(M_df['lat'])
    mean_lon=np.mean(M_df['lon'])
    return [stdT,mean_T_diff,mean_T,mean_lat,mean_lon]



def avg_time(times):
    """this function use to calculate the mean time, the format of time is datetime.datetime
    times: the format is DataFrame"""
    start_time=datetime(2018,1,1,0,0,0)
    avg=timedelta(days=0)
    for elem in times:
        if type(elem)==str:
            elem=datetime.strptime(elem,'%Y-%m-%d %H:%M:%S')
        avg+=(elem-start_time)
    avg=avg/len(times)
    avg_time=start_time+avg
    return avg_time
        
def read_telemetrystatus(path_name):
    """
    input the path of telemetry status file
    read the telementry_status,
    then return the useful data"""
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
    
def month(num):
    '''input the number of month
        output the letter of month'''
    month_list=[['January'],['February'],['March'],['April'],['May'],['June'],['July'],['August'],['September'],['October'],['November'],['December']]
    df=pd.DataFrame(data=month_list,columns=['month'],index=range(1,13))
    return df['month'][num]

def C2F(T):
    '''Celcius convert to Fahrenheit'''
    return 32+1.8*T

def all_boat_map(df,path_save,telemetrystatus_df):
    '''input a dataframe,below must be have this information in dataframe:
        name, time,lon,lat,observation temperature, climate temperature, the number of files in interval
        output a html map, below is the informat in this map.
        every name has a icon, there will have some informations when we button this icon, include vessel number,
        interval, file number, observed temperature and historical average temperature
    '''
    #set the map background
    map = folium.Map(location=[np.mean(df['lat']), np.mean(df['lon'])],zoom_start = 7,width='98%',left='1%',height='85%',control_scale=True,
                   detect_retina=True,tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}',
                          attr= 'Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri')
    
#    map.add_tile_layer( name='Esri_OceanBasemap',
#                     tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}',
#                          attr= 'Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri',
#                          
#                          ) 
#    map.add_tile_layer(                   name='NatGeo_World_Map',
#                   #tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}/',
#                   #tiles='http://services.arcgisonline.com/ArcGIS/rest/services/Specialty/World_Navigation_Charts/MapServer/tile/{z}/{y}/{x}',
#                   tiles='http://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
#                   attr= 'Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC',)
#    folium.LayerControl().add_to(map)
    for i in df.index:  #maker the location
        start_t,end_t=week_start_end(df['time'][i])
        if df['obstemp'][i]>df['climtemp'][i]:
            mark_color='red'
        else:
            mark_color='blue'
            
        try:
            vessel=telemetrystatus_df['Vessel#'][str(df['name'][i])]
        except:
            vesselname=str(df['name'][i])
            if vesselname=='Finlander I ':
                vesselname='Finlander_I '
            else:
                vesselname=str(df['name'][i]).replace(' ','_') 
            vessel=telemetrystatus_df['Vessel#'][vesselname]
        
                                          
        popups='<h3> Vessel_'+str(vessel)+'</h3><br><body>Average for '+month(int(start_t.strftime('%m')))+' '+str(start_t.strftime('%d'))\
                                                     +' to '+month(int(end_t.strftime('%m')))+' '+str(end_t.strftime('%d'))+'&nbsp;'+df['time'][i].strftime('%Y')+'<br>Observed temperature:'+\
                                                     str(round(C2F(df['obstemp'][i]),1))+'°F ('+str(round(df['obstemp'][i],1))+'°C)'+'<br>Historical temperature:'+\
                                                     str(round(C2F(df['climtemp'][i]),1))+'°F ('+str(round(df['climtemp'][i],1))+'°C)'+'<br>N='+str(round(df['number'][i],2))+'<body>'
        folium.Marker([df['lat'][i], df['lon'][i]],popup=popups,icon=folium.Icon(color=mark_color,icon='ad')).add_to(map)
    psave=os.path.join(path_save,start_t.strftime('%Y%m')+'icon')
    if not os.path.exists(psave):
        os.makedirs(psave)       
    map.save(os.path.join(psave,'weekly.html'))
    with open(os.path.join(psave,'weekly.html'),'a') as file:  #add the explaintion in html
        file.write('''        <body>
            <div id="header"><br>
                <h3>&nbsp;&nbsp;&nbsp;&nbsp&nbsp;Average position and bottom temperature for each boat reporting in the past week (click icons for data)</h3>  
                <ul>
                <li>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Red icon means warmer than historical records
                <li>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Blue icon means colder than historical records
                <li>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Each icon represents a different vessel and appears in the average position for the week.
                <li>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Many more icons should appear in subsequent weeks.
                </ul>
            </div>   
        </body>''')
    file.close()
def per_boat_map(df,path_save,dpi=300):
    '''plot per month, per vessel map
    oupput a map: below is the information in map:
        the mean temperature in historical
        the mean temperature of observation,
        the number is the Standard deviation in Parentheses
        the time period'''
    start_t,end_t=week_start_end(df['time'])
    fig=plt.figure(figsize=(8,10))
    size=min(fig.get_size_inches())
    fig.suptitle('F/V '+df['name'],fontsize=3*size, fontweight='bold')
    ax=fig.add_axes([0.03,0.2,0.85,0.68])
    ax.set_title(start_t.strftime('%Y/%m/%d')+'-'+end_t.strftime('%Y/%m/%d'))
    ax.axes.title.set_size(2*size)
    
    while(not zl.isConnected()):#check the internet is good or not
        time.sleep(120)   #if no internet, sleep 2 minates try again
    try:

        service = 'Ocean_Basemap'
        xpixels = 5000 
        #Build a map background
        map=Basemap(projection='mill',llcrnrlat=df['lat']-1,urcrnrlat=df['lat']+1,llcrnrlon=df['lon']-1,urcrnrlon=df['lon']+1,\
                resolution='f',lat_0=df['lat'],lon_0=df['lon'],epsg = 4269)
        map.arcgisimage(service=service, xpixels = xpixels, verbose=False)
        # draw parallels.
        parallels = np.arange(0.,90.0,0.5)
        map.drawparallels(parallels,labels=[0,1,0,0],fontsize=size,linewidth=0.0)
        # draw meridians
        meridians = np.arange(180.,360.,0.5)
        map.drawmeridians(meridians,labels=[0,0,0,1],fontsize=size,linewidth=0.0)
        #Draw a scatter plot
        tele_lat,tele_lon=df['lat'],df['lon']
        x,y=map(tele_lon,tele_lat)
        s='HT:'+str(df['climtemp'])+'\nOBS:'+str(round(df['obstemp'],4))+'('+str(round(df['Stdtemp'],2))+')'
        ax.plot(x, y,'b*',markersize=2*size, alpha=0.5)
        ax.text(x+0.05,y-0.05,s,fontsize =2*size)
        xlabel='\nHT:the mean temperature in historical\nOBS:the mean temperature of observation,the number is the Standard deviation in Parentheses'
        ax.set_xlabel(xlabel,position=(0., 1e6),horizontalalignment='left',fontsize =size)
#        if the path of the picture save is not there, creat the folder
        if not os.path.exists(path_save+'/picture'+df['time'].strftime('%Y-%m')+'/'):
            os.makedirs(path_save+'/picture'+df['time'].strftime('%Y-%m')+'/')
        #save the map
        plt.savefig(path_save+'/picture'+df['time'].strftime('%Y-%m')+'/'+df['name']+'_map'+'_'+end_t.strftime('%Y-%m-%d')+'.ps',dpi=dpi) #save picture
        print(df['name']+' finished draw!')
    except KeyboardInterrupt:
        sys.exit()
    except:
        print(df['name']+' need redraw!')
    
def month_start_end(dtime,interval=1):
    '''input a time
    return the first day(0:00:00) of this month,and next month first day (0:00:00)
    for example: input datetime.datetime(2019,1,12,1,12,11), return datetime.datetime(2019,1,1,0,0,0) and datetime.datetime(2019,2,1,0,0,0)'''
    #the interval must be the int and 1 means one month
    y=dtime.year
    m=dtime.month
    start_time=datetime(y,m,1,0,0)
    for i in range(interval):
        if m<12:
            m+=1
        else:
            m=1
            y+=1
    end_time=datetime(y,m,1,0,0)
    return start_time, end_time
def week_start_end(dtime,interval=0):
    '''input a time, 
    if the interval is 0, return this week monday 0:00:00 and next week monday 0:00:00
    if the interval is 1,return  last week monday 0:00:00 and this week monday 0:00:00'''
    delta=dtime-datetime(2003,1,1,0,0)-timedelta(weeks=interval)
    count=int(delta/timedelta(weeks=1))
    start_time=datetime(2003,1,1,0,0)+timedelta(weeks=count)
    end_time=datetime(2003,1,1,0,0)+timedelta(weeks=count+1)   
    return start_time,end_time    

#def main():
a=1
if a==1:
    #hardcode
    filepathread='/home/jmanning/leizhao/programe/aqmain/dictionary/dictionary.json'
    path_save='/home/jmanning/leizhao/programe/diff_modules/result/differentmap/'
    telemetry_status='/home/jmanning/leizhao/programe/diff_modules/parameter/telemetry_status.csv'
    end_time=datetime.now()

    start_time,end_time=week_start_end(end_time,interval=1) #the interval=1, menas the week is the last week of this time.
    ####
    try:
        with open(filepathread,'r') as fp:
            dictt=json.load(fp)
#        with open(filepathread,'rb') as fp:
#            dictt = pickle.load(fp)
    except KeyboardInterrupt:
        sys.exit()
    except:
        print('diff_clim_obs: check the file of dict_obsdpogmf0529.p')
    telemetrystatus_df=read_telemetrystatus(telemetry_status)
    telemetrystatus_df.index=telemetrystatus_df['Boat']

    mlist=[]
    for name in dictt.keys():
        if name=='end_time':
            continue
#        tele_df=check_time(dictt['tele_dict'][i],start_time,end_time,time_header='time')
#        CrmClim_df=check_time(dictt['CrmClim'][i],start_time,end_time,time_header='time').dropna()
        
        df=pd.DataFrame.from_dict(dictt[name])
        df['time']=df.index
        tele_df=df[['time','lat','lon','observation_T', 'observation_H']]
        tele_df.rename(columns={'observation_T':'temp','observation_H':'depth'},inplace=True)
        df['time']=df.index
        CrmClim_df=df[['time','lat','lon','Clim_T', 'NGDC_H']]
        CrmClim_df.rename(columns={'Clim_T':'temp','NGDC_H':'depth'},inplace=True)
        
        if len(tele_df)==0:  
            print(name+': no valuable data')
            continue
        tele_df=check_time(df=tele_df,time_header='time',start_time=start_time,end_time=end_time)
        CrmClim_df=check_time(df=CrmClim_df,time_header='time',start_time=start_time,end_time=end_time)
        if len(tele_df)==0:  
            print(name+': no valuable data')
            continue
        if len(CrmClim_df)==0:
            continue
        tele_list=[name,avg_time(tele_df['time']),np.mean(tele_df['lon']),np.mean(tele_df['lat']),np.mean(tele_df['temp'])]
        if len(CrmClim_df)!=0:
            CrmClim_diff= diff(tele_df,CrmClim_df)        
            mlist.append(tele_list+CrmClim_diff+[len(CrmClim_df)])
    df=pd.DataFrame(data=mlist,columns=['name','time','lon','lat','obstemp','Stdtemp','temp_diff','climtemp','Clat','Clon','number'])
    if len(df)!=0:
        #df=df.dropna()
        df.index=range(len(df))
        all_boat_map(df,path_save,telemetrystatus_df) 
        #    for i in df.index:
        #        per_boat_map(df.iloc[i],path_save,dpi=300) 
                
        
