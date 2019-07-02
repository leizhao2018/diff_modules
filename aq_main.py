# -*- coding: utf-8 -*-
'''
Routine to map the realtime eMOLT bottom temps using Leaflets
Created on Wed Sep  6 13:37:50 2017
@author: hxu

This program include 4 basic applications
1. Download raw csv files which have been uploaded by 'wifi.py' to studentdrifters.org
2. Look for good csv files and makes plot a graph for each good one
3. Create "telemetry.html"
4. Upload this html and the pngs to the new studentdrifters ftp location


Notes:
1. in the past we would organize and upload csv and graph files to google drive of 'huanxin.data@gmail.com'
2. in the future we may want to send email to notice the people who need these data files
3. there is another routine that needs to be run on the new SD machine to move html & pngs to httpdocs
4. If linux , change hard code system value to 'pc'

Modified by Huanxin 9 Oct 2018 to make temperature read degF
Modified by Lei Zhao in June 2019 to add models and climatology

###############################################
NOTICE: The PATHS YOU HAVE TO CHANGE TO MAKE THEM CORRECT
if you want chang the path and name, please go to the function of main()
###############################################
'''
import ftplib
import os
import datetime
import glob
from folium.plugins import MarkerCluster
import folium
import random
from matplotlib.dates import date2num
import pandas as pd 
import numpy as np
import json
import pytz

#############################################################
def get_moudules_value(filepathname,vessel_name,dtime): 
    #filepathread='/home/jmanning/leizhao/programe/diff_modules/result/data_dict/dict_obsdpogmf0529.p'
    dic={}
    with open(filepathname,'r') as fp:
        dictionary = json.load(fp)
    try:
        dic['Doppio']=dictionary[vessel_name]['Doppio_T'][str(dtime)]
        dic['GoMOLFs']=dictionary[vessel_name]['GoMOLFs_T'][str(dtime)]
        dic['FVCOM']=dictionary[vessel_name]['FVCOM_T'][str(dtime)]
        dic['CrmClim']=dictionary[vessel_name]['Clim_T'][str(dtime)]
    except:
        try:
            vessel_name=vessel_name.replace('_',' ')
            dic['Doppio']=dictionary[vessel_name]['Doppio_T'][str(dtime)]
            dic['GoMOLFs']=dictionary[vessel_name]['GoMOLFs_T'][str(dtime)]
            dic['FVCOM']=dictionary[vessel_name]['FVCOM_T'][str(dtime)]
            dic['CrmClim']=dictionary[vessel_name]['Clim_T'][str(dtime)]
        except:
            vessel_name=vessel_name.replace(' ','_')
            dic['Doppio']=dictionary[vessel_name]['Doppio_T'][str(dtime)]
            dic['GoMOLFs']=dictionary[vessel_name]['GoMOLFs_T'][str(dtime)]
            dic['FVCOM']=dictionary[vessel_name]['FVCOM_T'][str(dtime)]
            dic['CrmClim']=dictionary[vessel_name]['Clim_T'][str(dtime)]
    return dic
################################

def c2f(*c):
    """
    convert Celsius to Fahrenheit
    accepts multiple values
    """
    if not c:
        c = input ('Enter Celsius value:')
        f = 1.8 * c + 32
        return f
    else:
        f = [(i * 1.8 + 32) for i in c]
        return f    


###### START FTP SESSION TO THE OLD STUDENTDRIFTERS MACHINE AND DOWNLOAD RAW CSV
def upload_raw_file(path,temporary_f_path,system):
    ftp=ftplib.FTP('66.114.154.52','huanxin','123321')
    print ('Logging in.')
    ftp.cwd('/Matdata')
    print ('Accessing files')

    filenames_new = ftp.nlst() # get filenames within the directory OF REMOTE MACHINE
    filenames_history=glob.glob(path+'*.csv')+glob.glob(temporary_f_path+'*.csv')# GET LIST OF ALL GOOD AND BAD ON LOCAL MACHINE
    if system=='pc':
        filenames_history=[i.split('/')[1] for i in filenames_history]
    else:
        filenames_history=[i.split('\\')[1] for i in filenames_history] # list of filenames with out path
    
    # MAKE THIS A LIST OF FILENAMES
    files=list(set(filenames_new)-set(filenames_history)) # THIS FINDS THE LIST OF FILES THAT ARE NEW

    for filename in files: # DOWNLOAD ALL THE NEW FILES
        #local_filename = os.path.join(ddir+temporary_f_path, filename)    
        local_filename = os.path.join(temporary_f_path, filename)
        file = open(local_filename, 'wb')
        ftp.retrbinary('RETR '+ filename, file.write)
        #ftp.delete(filename)
        file.close()

    ftp.quit() # This is the “polite” way to close a connection
    print ('New files downloaded')


def eastern_to_gmt(filename):
    eastern = pytz.timezone('US/Eastern')
    gmt = pytz.timezone('GMT')
    if len(filename.split('_'))<8:
        times=filename.split('_')[-2]+'_'+filename.split('_')[-1][:-4] #filename likes :  'aqu_data/Logger_sn_1724-7_data_20150528_100400.csv'
    else:
        times=filename.split('_')[-3]+'_'+filename.split('_')[-2] #filename likes : 'aqu_data/Logger_sn_1724-71_data_20151117_105550_2.csv'
    #date = datetime.datetime.strptime(filename, '%a, %d %b %Y %H:%M:%S GMT')
    date = datetime.datetime.strptime(times, '%Y%m%d_%H%M%S')
    date_eastern=eastern.localize(date)
    gmtdate=date_eastern.astimezone(gmt)
    #print date
    return gmtdate



    
def make_html(path,temporary_f_path,codes_file,system,dictionaryfile,ddir):
    
    """MAKE TELEMETRY.HTML"""
    os.chdir(ddir)
    upload_raw_file(path,temporary_f_path,system)# UPDATE THE RAW FILE
    df_codes=pd.read_csv(codes_file,delim_whitespace=True,index_col=0,names = ["ap3", "depth", "boat_name", "aqu_num","form"]) #GET THE CODE INFORMATION FROME codes_temp.dat


    #### START BUILDING THE LEAFLET WEBPAGE, READ A FEW INPUT FILES, CREATE FOLIUM.MAP
    starttime=date2num(datetime.datetime.now())-30  # 31 days
    endtime=date2num(datetime.datetime.now())

    emolt='http://www.nefsc.noaa.gov/drifter/emolt.dat' # this is the output of combining getap2s.py and getap3.py
    df=pd.read_csv(emolt,delim_whitespace=True,index_col=0) # this was already defined above but kept here as a reminder
    including=list(set(df.index))

    df_codes=pd.read_csv(codes_file,delim_whitespace=True,index_col=0,names = ["ap3", "depth", "boat_name", "aqu_num","form"])

    map_1 = folium.Map(location=[41.572, -69.9072],width='88%', height='75%',left="3%", top="2%",
                   control_scale=True,
                   detect_retina=True,
                   zoom_start=8      
	)
    map_1.add_tile_layer( name='Esri_OceanBasemap',
                     tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}',
                          attr= 'Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri',                          
                          )
    map_1.add_tile_layer(                   name='NatGeo_World_Map',
                   tiles='http://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
                   attr= 'Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC',)
    colors = [
            'red',
            'blue',
            'gray',
            'darkred',
            'lightred',
            'orange',
            'beige',
            'green',
            'darkgreen',
            'lightgreen',
            'darkblue',
            'lightblue',
            'purple',
            'darkpurple',
            'pink',
            'cadetblue',
            'lightgray',
            'black'
            ]
    for x in range(int(len(df_codes)/len(colors))+2):
        colors=colors+colors
        #dictionary = zip(esn, colors)
        lat_box=[];lon_box=[]
#        route=0;lat=0;lon=0;popup=0;idn1=0;html='';lastfix=1;randomlat=1;randomlon=0;png_files=[]
        route=0;lat=0;lon=0;popup=0;html='';lastfix=1;randomlat=1;randomlon=0
        mc = MarkerCluster()  
    # CREATE ICONS ON THE MAP
    for i in range(0,len(including)): # LOOP THROUGH VESSELS note: I am skipping vessel_1 since that was just at the dock test
        print (i,route,popup,lastfix)
        if i!=route and popup!=0 and lastfix==0 and html!='': #since lastfix was set to 1 before loop, the following lines never get issued??????
                         
                                             #print 1111111111111111111111111111111111111111111111111111111
                                             iframe = folium.IFrame(html=html, width=300, height=250)
                                             popup = folium.Popup(iframe, max_width=900)
                                             folium.Marker([lat+randomlat,lon+randomlon], popup=popup,icon=folium.Icon(color=colors[route],icon='ok-sign')).add_to(map_1)  
        lastfix=1
        for line in range(len(df)): # LOOP THROUGH EACH LINE OF EMOLT.DAT
            if df.iloc[line].name==including[i]:
                id_idn1=including[i]
                yr1=int(df.iloc[line][15])
                mth1=int(df.iloc[line][1])
                day1=int(df.iloc[line][2])
                hr1=int(df.iloc[line][3])
                mn1=int(df.iloc[line][4])
#                yd1=float(df.iloc[line][5])
                datet=datetime.datetime(yr1,mth1,day1,hr1,mn1,tzinfo=None)
                #atet=str(int())
                if starttime<=date2num(datet)<=endtime and float(str(df.iloc[line][10]))>10: # What is this 2nd test about? column 10 is nan???
                    html=''
                    meandepth=str(df.iloc[line][10])
                    rangedepth=str(df.iloc[line][11])
                    len_day=df.iloc[line][12]# hours
                    mean_temp=str(df.iloc[line][13])
                    sdevia_temp=str(df.iloc[line][14])
                    lat=df.iloc[line][7]
                    lon=df.iloc[line][6]
                    try:
                        dfff=df_codes.drop_duplicates(subset=['boat_name'],keep='last')
                        dic=get_moudules_value(filepathname=dictionaryfile,vessel_name=dfff['boat_name'][including[i]],dtime=datet)
                        doppio_t,gomofs_t,FVCOM_t,clim_t=dic['Doppio'],dic['GoMOLFs'],dic['FVCOM'],dic['CrmClim']
                    except:
                        doppio_t,gomofs_t,FVCOM_t,clim_t=np.nan,np.nan,np.nan,np.nan
                          
                    if html=='':
                        html='''
                            <h1>  '''+id_idn1+'''</h1><br>
                            
                            <p>
                            <body>
                            <code>
                            '''+datet.strftime('%d-%b-%Y  %H:%M')+ '<br>meandepth(m): '+str(meandepth).rjust(10)+'<br>rangedepth(m): '+str(rangedepth).rjust(10)+\
                            '<br>haul_duration (hours): '+str(len_day).rjust(10) +'<br>meantemp: ' +str(mean_temp).rjust(4)+'degC ('+str(round(c2f(float(mean_temp))[0],2)).rjust(4)+\
                            ' degF)<br>sdevia_temp(C): '+str(sdevia_temp)+\
                            '<br>DOPPIO temperature: '+str(round(doppio_t,2)).rjust(4)+'degC ('+str(round(c2f(float(doppio_t))[0],2)).rjust(4)+'degF)'+\
                            '<br>FVCOM temperature: '+str(round(FVCOM_t,2)).rjust(4)+'degC ('+str(round(c2f(float(FVCOM_t))[0],2)).rjust(4)+'degF)'+\
                            '<br>GoMOFS temperature: '+str(round(gomofs_t,2)).rjust(4)+'degC ('+str(round(c2f(float(gomofs_t))[0],2)).rjust(4)+'degF)'+\
                            '<br>Climate History temperature: '+str(round(clim_t,2)).rjust(4)+'degC ('+str(round(c2f(clim_t)[0],2)).rjust(4)+'degF)''''
                            </code>
                            </body>
                            </p>
                            '''
                    lon_box.append(lon)
                    lat_box.append(lat)
                    iframe = folium.IFrame(html=html, width=520, height=280)
                    popup = folium.Popup(iframe, max_width=1500)
                    randomlat=random.randint(-3000, 3000)/100000. # what are these units??
                    randomlon=random.randint(-2500, 2000)/100000.
                    mk=folium.Marker([lat+randomlat,lon+randomlon], popup=popup,icon=folium.Icon(icon='star',color=colors[i]))
                    mc.add_child(mk)
                    map_1.add_child(mc)
                    lastfix=0
        route=i
    folium.LayerControl().add_to(map_1)
    #map_1.save('/home/jmanning/leizhao/py/telemetry.html')
    htmlpath=ddir[::-1].replace('py'[::-1],'html'[::-1],1)[::-1]
    map_1.save(os.path.join(htmlpath,'telemetry.html'))
    #with open('/home/jmanning/leizhao/py/telemetry.html', 'a') as file:
    with open(os.path.join(htmlpath,'telemetry.html'), 'a') as file:
        file.write('''        <body>
            <div id="header"><br>
                <h1>&nbsp;&nbsp;&nbsp;&nbsp&nbsp;Realtime bottom temperatures from fishing vessels in the past month</h1>  
                <ul>
                <li>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Checkmark icons denotes latest reports color-coded by vessel.
                <li>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Numbered icons denote multiple reports in that area color-coded by density of reports.
                <li>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Starred icons denote actual reports posted within 10 miles of actual position
                <li>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Layer symbol in upper right denotes other basemap options
                </ul>
            </div>   
        
        
        
        </body>''')
    file.close()

def main():
    #####################
    #Automatically set the file path according to the location of the installation package
    #get the path of file
    ddir=os.path.dirname(os.path.abspath(__file__))
    #set the file directory of parameters
    dictionarypath=ddir[::-1].replace('py'[::-1],'dictionary'[::-1],1)[::-1]
    parameterpath=ddir[::-1].replace('py'[::-1],'parameter'[::-1],1)[::-1]
    rawstorepath=ddir[::-1].replace('py'[::-1],'aq/aqu_data'[::-1],1)[::-1]
    temporary_f_path=ddir[::-1].replace('py'[::-1],'aq/as'[::-1],1)[::-1]
    
    #HARDCODES
    system='pc'
    codes_file=os.path.join(parameterpath,'codes_temp.dat')# the path and filename of code file
    dictionaryfile=os.path.join(dictionarypath,'dictionary.json') # dictionary with endtime,doppio,gomofs,fvcom where each model has vesselname,lat,lon,time,temp
    ##############################
    

    #make the html
    make_html(rawstorepath,temporary_f_path,codes_file,system,dictionaryfile,ddir)

#if __name__=='__main__':
#    main()

