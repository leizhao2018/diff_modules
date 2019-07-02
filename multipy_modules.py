#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 13:47:37 2019
functions get temperature from doppio,gomofs,fvcom

@author: lei
"""


import datetime
import math
import netCDF4
import numpy as np
import time
import zlconversions as zl
#import glob
from datetime import datetime as dt
import pandas as pd
#import os 


def bathy_nearlonlat(lon,lat,lonp,latp): # needed for the next function get_FVCOM_bottom_temp 
    """ 
    i,min_dist=nearlonlat(lon,lat,lonp,latp) change 
    find the closest node in the array (lon,lat) to a point (lonp,latp) 
    input: 
        lon,lat - np.arrays of the grid nodes, spherical coordinates, degrees 
        lonp,latp - point on a sphere 
        output: 
            i - index of the closest node 
            min_dist - the distance to the closest node, degrees 
            For coordinates on a plane use function nearxy 
    """ 
    # approximation for small distance 
    cp=np.cos(latp*np.pi/180.) 
    dx=(lon-lonp)*cp
    dy=lat-latp 
    xi=np.argmin(abs(dx)) 
    yi=np.argmin(abs(dy))
    min_dist=111*np.sqrt(dx[xi]**2+dy[yi]**2)
    return xi,yi,min_dist 

def dm2dd(lat,lon):
    #converts lat, lon from decimal degrees,minutes to decimal degrees
    (a,b)=divmod(float(lat),100.)   
    aa=int(a)
    bb=float(b)
    lat_value=aa+bb/60.
    if float(lon)<0:
        (c,d)=divmod(abs(float(lon)),100.)
        cc=int(c)
        dd=float(d)
        lon_value=cc+(dd/60.)
        lon_value=-lon_value
    else:
        (c,d)=divmod(float(lon),100.)
        cc=int(c)
        dd=float(d)
        lon_value=cc+(dd/60.)
    return lat_value, -lon_value

def doppio_coordinnate(lat,lon):
    '''use to check the coordinnate whether out of range'''
    f1=-0.8777722604596849*lat-lon-23.507489034447012>=0
    f2=-1.072648270137022*lat-40.60872567829448-lon<=0
    f3=1.752828434063416*lat-131.70051451008493-lon>=0
    f4=1.6986954871237598*lat-lon-144.67649951783605<=0
    if f1 and f2 and f3 and f4:
        return True
    else:
        return False


def fitting(point,lat,lon):
#represent the value of matrix
    ISum = 0.0
    X1Sum = 0.0
    X2Sum = 0.0
    X1_2Sum = 0.0
    X1X2Sum = 0.0
    X2_2Sum = 0.0
    YSum = 0.0
    X1YSum = 0.0
    X2YSum = 0.0

    for i in range(0,len(point)):
        x1i=point[i][0]
        x2i=point[i][1]
        yi=point[i][2]

        ISum = ISum+1
        X1Sum = X1Sum+x1i
        X2Sum = X2Sum+x2i
        X1_2Sum = X1_2Sum+x1i**2
        X1X2Sum = X1X2Sum+x1i*x2i
        X2_2Sum = X2_2Sum+x2i**2
        YSum = YSum+yi
        X1YSum = X1YSum+x1i*yi
        X2YSum = X2YSum+x2i*yi

    #  matrix operations
    # _mat1 is the mat1 inverse matrix
    m1=[[ISum,X1Sum,X2Sum],[X1Sum,X1_2Sum,X1X2Sum],[X2Sum,X1X2Sum,X2_2Sum]]
    mat1 = np.matrix(m1)
    m2=[[YSum],[X1YSum],[X2YSum]]
    mat2 = np.matrix(m2)
    _mat1 =mat1.getI()
    mat3 = _mat1*mat2
    # use list to get the matrix data
    m3=mat3.tolist()
    a0 = m3[0][0]
    a1 = m3[1][0]
    a2 = m3[2][0]
    y = a0+a1*lat+a2*lon
    return y


def getclim(lat1,lon1,dtime=dt.now(),var='Bottom_Temperature/BT_'): 
    # gets climatology of Bottom_Temperature, Surface_Temperature, Bottom_Salinity, or Surface_Salinity
    # as calculated by Chris Melrose from 30+ years of NEFSC CTD data on the NE Shelf provided to JiM in May 2018 
    # where "lat1", "lon1", and "yrday" are the position and yearday of interest (defaulting to today)
    # where "var" is the variable of interest (defaulting to Bottom_Temperature) 
    # inputdir='/net/data5/jmanning/clim/' # hardcoded directory name where you need to explode the "Data for Manning.zip"
    # assumes an indidividual file is stored in the "<inputdir>/<var>" directory for each yearday
    yrday=str(int(dtime.strftime('%j')))
#    inputdir_csv='/home/pi/Desktop/towifi/'
    inputdir='/home/jmanning/leizhao/py/clim/' # hardcoded directory name
    dflat=pd.read_csv(inputdir+'LatGrid.csv',header=None)
    dflon=pd.read_csv(inputdir+'LonGrid.csv',header=None)
    lat=np.array(dflat[0])   # gets the first col (35 to 45)
    lon=np.array(dflon.ix[0])# gets the first row (-75 to -65)
    clim=pd.read_csv(inputdir+var+yrday+'.csv',header=None) # gets bottom temp for this day of year
#    files=(glob.glob(inputdir_csv+'*.csv'))
#    files.sort(key=os.path.getmtime) # gets all the csv files in the towfi directory
#    dfcsv=pd.read_csv(files[-1],sep=',',skiprows=8)
#    [lat1,lon1]=dm2dd(float(dfcsv['lat'][0]),float(dfcsv['lon'][0]))
    idlat = np.abs(lat - lat1).argmin() # finds the neareast lat to input lat1
    idlon = np.abs(lon - lon1).argmin() # finds the neareast lon to input lon1
    return clim[idlon][idlat]

def get_depth_bathy(loni,lati,mindist_allowed=10):
    
    url1='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol1.nc'
    url2='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol2.nc'
    url3='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol3.nc'
    url4='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol4.nc'
    url5='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol5.nc'
    url6='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol6.nc'
    url7='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol7.nc'
    url8='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol8.nc'
    url9='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol9.nc'
    url10='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_vol10.nc'
    
    if 230.00000003>=loni>= 170.0 and 66.5 >=lati>=48.5:
        urlak='https://www.ngdc.noaa.gov/thredds/dodsC/crm/crm_southak.nc'
        nc = netCDF4.Dataset(urlak).variables 
        lon=nc['lon'][:]
        lat=nc['lat'][:]
        xi,yi,min_dist= bathy_nearlonlat(lon,lat,loni,lati) 
        if min_dist<mindist_allowed:
            return float(nc['z'][yi,xi])
    elif -64.0>=loni>=-80.0 and 48.0>=lati>=40.0:
        urls=[url1]
    elif -68.0>=loni>=-85.0 and 40.0>=lati>=31.0:
        urls=[url2,url3]
    elif -78.0>=loni>=-87.0 and 35.0>=lati>=24.0:
        urls=[url3]
    elif -87.0>=loni>= -94.0 and 36.0 >=lati>=24.0:
        urls=[url4]
    elif -94.0>=loni>= -108.0 and 38.0>=lati>= 24.0:
        urls=[url5]
    elif -114.0>=loni>= -126.0 and 37.0>=lati>= 32.0:
        urls=[url6]
    elif -117.0>=loni>= -128.0 and 44.0>=lati>= 37.0:
        urls=[url7]
    elif -116.0>=loni>= -128.0 and 49.0 >=lati>=44.0:
        urls=[url8]
    elif -64.0>=loni>= -68.0 and 20.0 >=lati>=16.0:
        urls=[url9]
    elif -152.0>=loni>= -162.0 and 24.0>=lati>= 18.0:
        urls=[url10]  
    else:
        return np.nan
    for url in urls:
        nc = netCDF4.Dataset(url).variables 
        lon=nc['x'][:]
        lat=nc['y'][:]
        xi,yi,min_dist= bathy_nearlonlat(lon,lat,loni,lati) 
        if min_dist<mindist_allowed:
            return float(nc['z'][yi,xi])

def get_gomofs_url(date):
    """
    the format of date is:datetime.datetime(2019, 2, 27, 11, 56, 51, 666857)
    input date and return the url of data
    """
#    print('start calculate the url!') 
    date=date+datetime.timedelta(hours=4.5)
    date_str=date.strftime('%Y%m%d%H%M%S')
    hours=int(date_str[8:10])+int(date_str[10:12])/60.+int(date_str[12:14])/3600.
    tn=int(math.floor((hours)/6.0)*6)  ## for examole: t12z the number is 12
    if len(str(tn))==1:
        tstr='t0'+str(tn)+'z'   # tstr in url represent hour string :t00z
    else:
        tstr='t'+str(tn)+'z'
    if round((hours)/3.0-1.5,0)==tn/3:
        nstr='n006'       # nstr in url represent nowcast string: n003 or n006
    else:
        nstr='n003'
    url='http://opendap.co-ops.nos.noaa.gov/thredds/dodsC/NOAA/GOMOFS/MODELS/'\
    +date_str[:6]+'/nos.gomofs.fields.'+nstr+'.'+date_str[:8]+'.'+tstr+'.nc'
    return url

def get_gomofs_url_forcast(date,forcastdate=True):
    """
    the date use to choose file
    the format of date is GMT TIME:datetime.datetime(2019, 2, 27, 11, 56, 51, 666857)
    forcastdate like date or True
    input date and return the url of data
    """
    if forcastdate==True:  #if forcastdate is True: default the forcast date equal to the time of choose file.
        forcastdate=date
    date=date-datetime.timedelta(hours=1.5)  #the parameter of calculate txx(eg:t00,t06 and so on)
    tn=int(math.floor(date.hour/6.0)*6)  #the numer of hours in time index: eg: t12, the number is 12
    ymdh=date.strftime('%Y%m%d%H%M%S')[:10]  #for example:2019011112(YYYYmmddHH)
    if len(str(tn))==1:
        tstr='t0'+str(tn)+'z'  #tstr: for example: t12
    else:
        tstr='t'+str(tn)+'z'
    fnstr=str(3+3*math.floor((forcastdate-datetime.timedelta(hours=1.5+tn)-datetime.datetime.strptime(ymdh[:8],'%Y%m%d')).seconds/3600./3.))#fnstr:the number in forcast index, for example f006 the number is 6
    if len(fnstr)==1:   
        fstr='f00'+fnstr  #fstr: forcast index:for example: f006
    else:
        fstr='f0'+fnstr
    url='http://opendap.co-ops.nos.noaa.gov/thredds/dodsC/NOAA/GOMOFS/MODELS/'\
    +ymdh[:6]+'/nos.gomofs.fields.'+fstr+'.'+ymdh[:8]+'.'+tstr+'.nc'
    return url

def get_gomofs(dtime,latp,lonp,depth='bottom',mindistance=20,autocheck=True,fortype='temperature'):
    """
    the format time(GMT) is: datetime.datetime(2019, 2, 27, 11, 56, 51, 666857)
    lat and lon use decimal degrees
    if the depth is under the water, please must add the marker of '-'
    input time,lat,lon,depth return the temperature of specify location (or return temperature,nc,rho_index,ocean_time_index)
    the unit is mile of distance
    return the temperature of specify location
    """
    
    if not gomofs_coordinaterange(latp,lonp):
        print('latp and lonp out of range in gomofs')
        return np.nan
        
    if dtime<datetime.datetime.strptime('2018-07-01 00:00:00','%Y-%m-%d %H:%M:%S'):
        print('Time out of range, time start :2018-07-01 00:00:00z')
        return np.nan
    if dtime>datetime.datetime.now()+datetime.timedelta(days=3): #forecast time under 3 days
        print('forecast time under 3 days')
        return np.nan
   
    #start download data
    forecastdate=dtime  #forecast time equal input date_time
    changefile,filecheck=1,1  #changefile means whether we need to change the file to get data, filecheck means check the file exist or not.
    while(changefile==1):  
        count=1
        while(filecheck==1):  #download the data
            try:
                if forecastdate==dtime:   #the forcastdate is input date_time, if the date_time changed yet,we will use the forecast data
                    url=get_gomofs_url(dtime)
                    nc=netCDF4.Dataset(str(url))
                    print('download nowcast data.')
                else:
                    url=get_gomofs_url_forcast(dtime,forecastdate)
                    nc=netCDF4.Dataset(str(url))
                    print('download forecast data.')
                filecheck,readcheck=0,1      # if the file is there, filecheck=0,readcheck use to check the file whether read successfully               
            except OSError:
                try:
                    url=get_gomofs_url_forcast(dtime,forecastdate)
                    nc=netCDF4.Dataset(str(url))
                    print('download forecast data.')
                    filecheck,readcheck=0,1  
                except OSError:
                    dtime=dtime-datetime.timedelta(hours=6)
                    if (forecastdate-dtime)>datetime.timedelta(days=3):  #every file only have 3 days data.
                        print('please check the website or file is exist!')
                        return np.nan
                except:
                    return np.nan
            except:
                return np.nan
        while(readcheck==1):  #read data,  if readcheck==1 start loop
            try:
                while True:
                    #print('connecting the web.')
                    if zl.isConnected(address=url):
                        break
                    print('check the website is well or internet is connected?')
                    time.sleep(5)
                gomofs_lons=nc.variables['lon_rho'][:]
                gomofs_lats=nc.variables['lat_rho'][:]
                readcheck,changefile=0,0   #if read data successfully, we do not need to loop
            except RuntimeError: 
                count=count+1
                if count>8:
                    if autocheck==True:
                        return np.nan
                    while True:
                        print('it will return nan, if you do not need read again.')
                        cmd = input("whether need read again(y/n)?：")
                        if cmd.lower() == "y":
                            count=1
                            break
                        elif cmd.lower() == "n":
                            cmd2 = input("whether need change file(y/n)?：")
                            if cmd2.lower()=="y":
                                dtime=dtime-datetime.timedelta(hours=6)
                                readcheck,filecheck=0,1
                                break
                            else:
                                print('interrupt read data.')
                                return np.nan
                        else:
                            break
                time.sleep(20)   #every time to reread data need stop 20s
                print('the '+str(int(count))+' times to read data.')
            except:
                return np.nan
    #caculate the index of the nearest four points    
    target_distance=2*zl.dist(lat1=gomofs_lats[0,0],lon1=gomofs_lons[0,0],lat2=gomofs_lats[0,1],lon2=gomofs_lons[0,1])
    eta_rho,xi_rho=find_nd(target=target_distance,lat=latp,lon=lonp,lats=gomofs_lats,lons=gomofs_lons)
    
    if zl.dist(lat1=latp,lon1=lonp,lat2=gomofs_lats[eta_rho][xi_rho],lon2=gomofs_lons[eta_rho][xi_rho])>mindistance:
        print('THE location is out of range')
        return np.nan
    # estimate the bottom depth of point location 
    if eta_rho==0:
        eta_rho=1
    if eta_rho==len(gomofs_lats)-1:
        eta_rho=len(gomofs_lats)-2
    if xi_rho==len(gomofs_lats[0])-1:
        eta_rho=len(gomofs_lats[0])-2
    while True:
        gomofs_rho=nc.variables['s_rho']
        gomofs_h=nc.variables['h']
        gomofs_temp=nc.variables['temp']
        break
   #print('start caculate the bottom depth of point location!') 
    points_h=[[gomofs_lats[eta_rho][xi_rho],gomofs_lons[eta_rho][xi_rho],gomofs_h[eta_rho,xi_rho]],
             [gomofs_lats[eta_rho,(xi_rho-1)],gomofs_lons[eta_rho,(xi_rho-1)],gomofs_h[eta_rho,(xi_rho-1)]],
             [gomofs_lats[eta_rho,(xi_rho+1)],gomofs_lons[eta_rho,(xi_rho+1)],gomofs_h[eta_rho,(xi_rho+1)]],
             [gomofs_lats[(eta_rho-1),xi_rho],gomofs_lons[(eta_rho-1),xi_rho],gomofs_h[(eta_rho-1),xi_rho]],
             [gomofs_lats[(eta_rho+1),xi_rho],gomofs_lons[(eta_rho+1),xi_rho],gomofs_h[(eta_rho+1),xi_rho]]]
    point_h=zl.fitting(points_h,latp,lonp) 
    # caculate the rho index
    if depth=='bottom':
        rho_index=0
    else:
        distance_h=abs(gomofs_rho[:]*point_h+abs(depth))
        rho_index=np.argmin(distance_h)
        
    #estimate the temperature of point location
    points_temp=[[gomofs_lats[eta_rho,xi_rho],gomofs_lons[eta_rho,xi_rho],gomofs_temp[0,rho_index,eta_rho,xi_rho]],
             [gomofs_lats[eta_rho,(xi_rho-1)],gomofs_lons[eta_rho,(xi_rho-1)],gomofs_temp[0,rho_index,eta_rho,(xi_rho-1)]],
             [gomofs_lats[eta_rho,(xi_rho+1)],gomofs_lons[eta_rho,(xi_rho+1)],gomofs_temp[0,rho_index,eta_rho,(xi_rho+1)]],
             [gomofs_lats[(eta_rho-1),xi_rho],gomofs_lons[(eta_rho-1),xi_rho],gomofs_temp[0,rho_index,(eta_rho-1),xi_rho]],
             [gomofs_lats[(eta_rho-1),xi_rho],gomofs_lons[(eta_rho-1),xi_rho],gomofs_temp[0,rho_index,(eta_rho-1),xi_rho]]]
    temperature=zl.fitting(points_temp,latp,lonp)
    # if input depth out of the bottom, print the prompt message
#    if depth!='bottom':
#        if abs(point_h)<abs(depth):
#            print ("the depth is out of the bottom:"+str(point_h))
#    if rho_index!=0:
#        point_h=depth
    if fortype=='tempdepth':
        return temperature,point_h
    else:
        return temperature


def get_FVCOM_temp(latp,lonp,dtime,depth='bottom',mindistance=2,fortype='temperature'): # gets modeled temp using GOM3 forecast 
    ''' 
    fortype list ['tempdepth','temperature']
    the unite of the mindistance is mile
    Taken primarily from Rich's blog at: http://rsignell-usgs.github.io/blog/blog/2014/01/08/fvcom/ on July 30, 2018 
    where lati and loni are the position of interest, dtime is the datetime, and layer is "-1" for bottom 
    ''' 
    m2k_factor = 0.62137119 #mile to kilometers parameter
    #urlfvcom = 'http://www.smast.umassd.edu:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3' 
    #urlfvcom = 'http://www.smast.umassd.edu:8080/thredds/dodsC/FVCOM/NECOFS/Forecasts/NECOFS_FVCOM_OCEAN_MASSBAY_FORECAST.nc' 
    urlfvcom = 'http://www.smast.umassd.edu:8080/thredds/dodsC/FVCOM/NECOFS/Forecasts/NECOFS_GOM3_FORECAST.nc' 
    nc = netCDF4.Dataset(urlfvcom).variables 
    #first find the index of the grid  
    lat = nc['lat'][:] 
    lon = nc['lon'][:] 
    inode,dist= nearlonlat(lon,lat,lonp,latp) 
    if dist>mindistance/m2k_factor/111:
        return np.nan,np.nan
    #second find the index of time 
    time_var = nc['time'] 
    itime = netCDF4.date2index(dtime,time_var,select='nearest')# where startime in datetime 
    if depth=='bottom':
        layer=-1
    else:
        depth_distance=abs(nc['siglay'][:,inode]*nc['h'][inode]+depth)
        layer=np.argmin(depth_distance)
    
#    if layer==39:    
#        point_h=nc['h'][inode]
#    else:
#        point_h=depth
    if fortype=='temperature':
        return nc['temp'][itime,layer,inode]
    elif fortype=='tempdepth':    
        return nc['temp'][itime,layer,inode],nc['h'][inode]
    else:
        return 'please input write fortype'
    

    
def get_doppio(latp=0,lonp=0,depth='bottom',dtime=datetime.datetime.now(),fortype='temperature',hour_allowed=1):
    """
    notice:
        the format of time is like "%Y-%m-%d %H:%M:%S" this time is utctime or the type of time is datetime.datetime
        the depth is under the bottom depth
    the module only output the temperature of point location
    """
    if not doppio_coordinnate(latp,lonp):
        print('the lat and lon out of range in doppio')
        return np.nan,np.nan
    if type(dtime)==str:
        date_time=datetime.datetime.strptime(dtime,'%Y-%m-%d %H:%M:%S') # transform time format
    else:
        date_time=dtime
    for m in range(0,7):
        try:
            url_time=(date_time-datetime.timedelta(days=m)).strftime('%Y-%m-%d')
            url=zl.get_doppio_url(url_time)
            #get the data 
            nc=netCDF4.Dataset(url)
            lons=nc.variables['lon_rho'][:]
            lats=nc.variables['lat_rho'][:]
            doppio_time=nc.variables['time']
            doppio_rho=nc.variables['s_rho']
            doppio_temp=nc.variables['temp']
            doppio_h=nc.variables['h']
        except:
            continue
        #calculate the index of the minimum timedelta
        parameter=(datetime.datetime(2017,11,1,0,0,0)-date_time).days*24+(datetime.datetime(2017,11,1,0,0,0)-date_time).seconds/3600.
        time_delta=abs(doppio_time[:]+parameter)
        min_diff_index=np.argmin(time_delta)
        #calculate the min distance and index
        target_distance=2*zl.dist(lat1=lats[0,0],lon1=lons[0,0],lat2=lats[0,1],lon2=lons[0,1])
        index_1,index_2=find_nd(target=target_distance,lat=latp,lon=lonp,lats=lats,lons=lons)
        #calculate the optimal layer index
        if depth=='bottom':
            layer_index=0  #specify the initial layer index
        else:
            h_distance=abs(doppio_rho[:]*doppio_h[index_1,index_2]+abs(depth))
            layer_index=np.argmin(h_distance)
#        fitting the data through the 5 points
        if index_1==0:
            index_1=1
        if index_1==len(lats)-1:
            index_1=len(lats)-2
        if index_2==0:
            index_2=1
        if index_2==len(lats[0])-1:
            index_2=len(lats[0])-2
        while True:
            point=[[lats[index_1][index_2],lons[index_1][index_2],doppio_temp[min_diff_index,layer_index,index_1,index_2]],\
            [lats[index_1-1][index_2],lons[index_1-1][index_2],doppio_temp[min_diff_index,layer_index,(index_1-1),index_2]],\
            [lats[index_1+1][index_2],lons[index_1+1][index_2],doppio_temp[min_diff_index,layer_index,(index_1+1),index_2]],\
            [lats[index_1][index_2-1],lons[index_1][index_2-1],doppio_temp[min_diff_index,layer_index,index_1,(index_2-1)]],\
            [lats[index_1][index_2+1],lons[index_1][index_2+1],doppio_temp[min_diff_index,layer_index,index_1,(index_2+1)]]]
            break
        point_temp=fitting(point,latp,lonp)
        while True:
            points_h=[[lats[index_1][index_2],lons[index_1][index_2],doppio_h[index_1,index_2]],\
            [lats[index_1-1][index_2],lons[index_1-1][index_2],doppio_h[(index_1-1),index_2]],\
            [lats[index_1+1][index_2],lons[index_1+1][index_2],doppio_h[(index_1+1),index_2]],\
            [lats[index_1][index_2-1],lons[index_1][index_2-1],doppio_h[index_1,(index_2-1)]],\
            [lats[index_1][index_2+1],lons[index_1][index_2+1],doppio_h[index_1,(index_2+1)]]]
            break
        point_temp=fitting(point,latp,lonp)
#        point_temp=doppio_temp[min_diff_index,layer_index,index_1,index_2]
        point_h=fitting(points_h,latp,lonp)
        if np.isnan(point_temp):
            continue
        if time_delta[min_diff_index]<hour_allowed:
            break        
    if fortype=='tempdepth':
#        if layer_index!=0:
#            point_h=depth
#        return point_temp,doppio_h[index_1,index_2]
        return point_temp, point_h
    else:
        return point_temp
#    
    
def find_ndg(target,lat,lon,lats,lons):
    
    """ Bisection method:find the index of nearest distance"""
    row=0
    maxrow=len(lats)-1
    col=len(lats[0][:])-1
    while col>=0 and row<=maxrow:
        distance=zl.dist(lat1=lats[row,col],lat2=lat,lon1=lons[row,col],lon2=lon)
        if distance<=target:
            break
        elif abs(lats[row,col]-lat)<abs(lons[row,col]-lon):
            col-=1
        else:
            row+=1
    distance=zl.dist(lat1=lats[row,col],lat2=lat,lon1=lons[row,col],lon2=lon)
    row_md,col_md=row,col  #row_md the row of minimum distance
    #avoid row,col out of range in next step
    if row<3:
        row=3
    if col<3:
        col=3
    if row>maxrow-3:
        row=maxrow-3
    if col>len(lats[0])-4:
        col=len(lats[0])-4
    for i in range(row-3,row+3,1):
        for j in range(col-3,col+3,1):
            distance_c=zl.dist(lat1=lats[i,j],lat2=lat,lon1=lons[i,j],lon2=lon)
            if distance_c<=distance:
                distance=distance_c
                row_md,col_md=i,j
    return row_md,col_md
    
    
    
def find_nd(target,lat,lon,lats,lons):
    
    """ Bisection method:find the index of nearest distance"""
    row=0
    maxrow=len(lats)-1
    col=len(lats[0])-1
    while col>=0 and row<=maxrow:
        distance=zl.dist(lat1=lats[row,col],lat2=lat,lon1=lons[row,col],lon2=lon)
        if distance<=target:
            break
        elif abs(lats[row,col]-lat)<abs(lons[row,col]-lon):
            col-=1
        else:
            row+=1
    distance=zl.dist(lat1=lats[row,col],lat2=lat,lon1=lons[row,col],lon2=lon)
    row_md,col_md=row,col  #row_md the row of minimum distance
    #avoid row,col out of range in next step
    if row<3:
        row=3
    if col<3:
        col=3
    if row>maxrow-3:
        row=maxrow-3
    if col>len(lats[0])-4:
        col=len(lats[0])-4
    for i in range(row-3,row+3,1):
        for j in range(col-3,col+3,1):
            distance_c=zl.dist(lat1=lats[i,j],lat2=lat,lon1=lons[i,j],lon2=lon)
            if distance_c<=distance:
                distance=distance_c
                row_md,col_md=i,j
    return row_md,col_md

def gomofs_coordinaterange(lat,lon):
    """check the coordinate whether out of the range in gomofs module"""
    f1=-0.7490553378867058*lat-lon-40.98355685763821<=0
    f2=-0.5967392371008197*lat-lon-36.300860518805024>=0
    f3=2.695505391925802*lat-lon-188.76889647321198<=0
    f4=2.689125428655328*lat-lon-173.5017523298927>=0
    if f1 and f2 and f3 and f4:
        return True
    else:
        return False
    
def nearlonlat(lon,lat,lonp,latp): # needed for the next function get_FVCOM_bottom_temp 
    """ 
    i,min_dist=nearlonlat(lon,lat,lonp,latp) change 
    find the closest node in the array (lon,lat) to a point (lonp,latp) 
    input: 
        lon,lat - np.arrays of the grid nodes, spherical coordinates, degrees 
        lonp,latp - point on a sphere 
    output: 
        i - index of the closest node 
        min_dist - the distance to the closest node, degrees 
        For coordinates on a plane use function nearxy 
        Vitalii Sheremet, FATE Project   
    """ 
    cp=np.cos(latp*np.pi/180.) 
    # approximation for small distance 
    dx=(lon-lonp)*cp 
    dy=lat-latp 
    dist2=dx*dx+dy*dy 
    # dist1=np.abs(dx)+np.abs(dy) 
    i=np.argmin(dist2) 
    min_dist=np.sqrt(dist2[i]) 
    return i,min_dist  
#t1=datetime.datetime.now()
#lat,lon=41.869601, -70.376114
#date_time=t1
#print(get_doppio(latp=lat,lonp=lon,depth=20,dtime=t1,fortype='temperature'))
#print(get_gomofs(dtime=date_time,latp=lat,lonp=lon,depth=20,fortype='tempdepth'))
##get_FVCOM_temp(lati,loni,dtime,depthi,mindistance=2,fortype='temperature')
#print(get_FVCOM_temp(latp=lat,lonp=lon,dtime=date_time,depth=20,mindistance=2,fortype='tempdepth'))
##t2=datetime.datetime.now()
##print(t2-t1)