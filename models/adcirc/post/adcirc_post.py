__author__ = "Saeed Moghimi"
__copyright__ = "Copyright 2015, Portland State University"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "moghimis@gmail.com"


import netCDF4
import netcdftime

import matplotlib.pyplot as plt
import numpy as np
import os,sys
from   pynmd.plotting.vars_param import *
import pynmd.plotting.plot_settings as ps
import datetime
import matplotlib.tri as Tri

import cartopy.crs as ccrs
from cartopy.io import shapereader
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

import cartopy.crs as ccrs
from cartopy.mpl.gridliner import (LONGITUDE_FORMATTER,
                                   LATITUDE_FORMATTER)

#import seaborn as sns
#plt.style.use('seaborn-white')


### Funcs
def ReadDates(DirName):
    fname =  os.path.abspath(DirName + 'fort.63.nc')  
    #print fname
    nc  = netCDF4.Dataset(fname)
    ncv = nc.variables
    t_var   = nc.variables['time'] 
    dates = netCDF4.num2date(t_var[:],t_var.units)
    nc.close()
    return dates


def ReadElev(DirName, tind):
    """
    fname: fort.63.nc file
    tind: time index
    """
    fname =  os.path.abspath(DirName + 'fort.63.nc') 
    nc  = netCDF4.Dataset(fname)
    ncv  = nc.variables
    t_var= nc.variables['time'] 
    date = netCDF4.num2date(t_var[tind],t_var.units)
    elev = nc.variables['zeta'][tind].squeeze()
    nc.close()
    return {'ncv':ncv,'date':date,'elev':elev}    

def ReadUV(DirName, tind):
    """
    fname: fort.64.nc file
    tind: time index
    """
    fname =  os.path.abspath(DirName + 'fort.64.nc' ) 
    nc  = netCDF4.Dataset(fname)
    ncv = nc.variables
    t_var= nc.variables['time'] 
    date = netCDF4.num2date(t_var[tind],t_var.units)
    u    = nc.variables['u-vel'][tind].squeeze()
    v    = nc.variables['v-vel'][tind].squeeze()
    uv   = np.sqrt(u*u + v*v)
    nc.close()

    return {'ncv':ncv,'date':date,'u':u,'v':v,'uv':uv}   

def ReadVar(fname='',varname='',time_name=None , tind = None):
    """
    fname: ncfile name
    varname:
    """
    out = {}
    fn  = os.path.abspath(fname)
    #print fn
    nc  = netCDF4.Dataset(fn)
    ncv = nc.variables
    try:
        if time_name is not None:
            tname = time_name
        else:
            tname =   'time' 
        t_var= nc.variables[tname] 
        if tind is None:
           date = netCDF4.num2date(t_var[:],t_var.units)
        else:
           date = netCDF4.num2date(t_var[tind],t_var.units)
        
        out.update({'date':date})
    
    except:
        pass

    if tind is None:
        var = nc.variables[varname][:].squeeze()
    else:
        var = nc.variables[varname][tind].squeeze()

    # x   = nc.variables['longitude'][:]
    # y   = nc.variables['latitude'][:]
    # read connectivity array
    # el  = nc.variables['tri'][:] - 1
    # create a triangulation object, specifying the triangle connectivity array
    # tri = Tri.Triangulation(x,y, triangles=el)
    nc.close()
    out.update({'ncv':ncv,varname:var}) 
    return out   

def maskTri(Tri,zmask):
    """
    Inputs: 
    tri object
    mask array of vertex
    
    Returned: maksed tri object
    """
    
    print '[info:] Mask Tri ... '
    mask = np.ones(len(Tri.triangles), dtype=bool)
    count = 0
    for t in Tri.triangles:
        count+=1
        ind = t
        if np.any(zmask[ind-1]):
            mask[count-1] = False    
    Tri.set_mask = mask
    return Tri

def maskTri_v2 (Tri,mask):
    m = np.all(mask[Tri.triangles],axis=1) 
    Tri.set_mask = m
    return Tri

def ReadTri_v1(DirName):

    """
    fname: one of fort.*.nc file
    tind: time index
    """ 
    fname =  os.path.abspath(DirName + 'fort.63.nc'  )
    nc  = netCDF4.Dataset(fname)
    ncv = nc.variables
    x   = nc.variables['x'][:]
    y   = nc.variables['y'][:]
    # read connectivity array
    el  = nc.variables['element'][:] - 1
    # create a triangulation object, specifying the triangle connectivity array
    print '[info:] Generate Mask ...'
    tri  = Tri.Triangulation(x,y, triangles=el)
    try:
        zeta = nc.variables['zeta'][0].squeeze()
        #zeta = np.ma.masked_where(np.isnan(zeta),zeta)
        tri = tri_mask(tri,zeta.mask)
    except:
        print ' Tri mask did not applied !'
        pass
    nc.close()
    return x,y,tri


def ReadTri(DirName):

    """
    fname: one of fort.*.nc file
    tind: time index
    """ 
    fname =  os.path.abspath(DirName + '/maxele.63.nc'  )
    nc  = netCDF4.Dataset(fname)
    ncv = nc.variables
    x   = nc.variables['x'][:]
    y   = nc.variables['y'][:]
    # read connectivity array
    el  = nc.variables['element'][:] - 1
    # create a triangulation object, specifying the triangle connectivity array
    print '[info:] Generate Tri ...'
    tri  = Tri.Triangulation(x,y, triangles=el)
    if False:
        try:
            zeta = nc.variables['zeta_max'][:].squeeze()
            zeta = np.ma.masked_where(np.isnan(zeta),zeta)
            tri = tri_mask(tri,zeta.mask)
            print '[info:] Generate Tri.mask ...'

        except:
            print ' Tri mask did not applied !'
            pass
    nc.close()
    return x,y,tri


def ReadFort80(dir):
    """
    Read fort.80 file for domain decomposition information
    
    return a dictionary including:
    IMAP_EL_LG
    IMAP_NOD_LG
    IMAP_NOD_GL (negative values for not owned elements)
   
    """
    fdata = open( dir + '/fort.80' ,  'r')
    while True:
    #for  line in fdata.readlines():
        line = fdata.readline()
        if 'Number of processors'     in line: nproc = int(line.split()[0]) 
        if 'Total # elements & nodes' in line: 
            nelem = int(line.split()[0])
            nnode = int(line.split()[1])          
        if 'NWLON, NWLAT'             in line:
            print line
            break

    #allocate
    IMAP_NOD_LG  = []
    IMAP_NOD_GL   = np.zeros((nnode,3),dtype=np.int)
    IMAP_EL_LG   = []
    #IMAP_STAE_LG = []
    #IMAP_STAV_LG = []
    #IMAP_STAC_LG = []
    #IMAP_STAM_LG = []
    pe_all        = []
    print '[info:] read nodes local2global'
    for inp in  range( nproc ):
        line1       = fdata.readline()
        #print line1
        pe          = int(line1.split()[0])
        nnodp       = int(line1.split()[1])                
        nod_res_tot = int(line1.split()[2])                
        pe_all.append(pe)
        tmpa = np.array([])
        proc_read = True
        while proc_read:
           line1 = fdata.readline()
           tmp = np.array([int(v) for v in line1.split()])
           tmpa = np.r_[tmpa,tmp]
           if len(tmpa) == nnodp:
               IMAP_NOD_LG.append(tmpa)
               proc_read = False
      
    print '[info:] read nodes local2global'
    line1       = fdata.readline()
    #print line1
    for il in range(nnode):
        line1       = fdata.readline()
        node_globa = int(line1.split()[0])
        pe         = int(line1.split()[1])                
        node_local = int(line1.split()[2]) 
        IMAP_NOD_GL[il,:] = node_globa , pe ,  node_local

    print '[info:] read elements local2global'
    for inp in  range( nproc ):
        line1       = fdata.readline()
        #print line1
        pe          = int(line1.split()[0])   # pe number
        nelmp       = int(line1.split()[1])   # element on pe             

        pe_all.append(pe)
        tmpa = np.array([])
        proc_read = True
        while proc_read:
           line1 = fdata.readline()
           tmp = np.array([int(v) for v in line1.split()])
           tmpa = np.r_[tmpa,tmp]
           if len(tmpa) == nelmp:
               IMAP_EL_LG.append(tmpa)
               proc_read = False
           
    fdata.close() 
    return (dict (nproc = nproc, nelem = nelem, nnode = nnode ,
                  IMAP_EL_LG  = np.array(IMAP_EL_LG) ,
                  IMAP_NOD_LG = np.array(IMAP_NOD_LG),
                  IMAP_NOD_GL = np.array(IMAP_NOD_GL) )) 


def make_map(projection=ccrs.PlateCarree(), bg='m'):
    
    """
    Generate fig and ax using cartopy
    input: projection
    output: fig and ax
    """


    subplot_kw = dict(projection=projection)
    fig, ax = plt.subplots(figsize=(9, 13),
                           subplot_kw=subplot_kw)
    gl = ax.gridlines(draw_labels=True)
    gl.xlabels_top = gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    
    
    if bg is not None:
        if res == 'm':
            ax.background_img(name='BM', resolution='high')   # from local hdd you need to > import pynmd.plotting
        else:
            ax.background_img(name='BMH', resolution='high')   # from local hdd you need to > import pynmd.plotting

    return fig, ax

def maskDryElements(grid):
    dry_masked = np.ma.masked_where(grid['depth']<=0., grid['depth'])
    return np.all(dry_masked.mask[grid['Elements']-1],axis=1)

def maskTri(tri,mask):
    return np.all(mask[tri.triangles],axis=1)

def maskTolExceed(OldGrid,NewGrid,tol=0.1):
    diff = OldGrid['depth'] - NewGrid['depth']
    diffm = np.ma.masked_where(np.abs(diff) <= tol*np.abs(OldGrid['depth']), diff)
    return np.all(diffm.mask[NewGrid['Elements']-1],axis=1)


def readTrack ( atcfFile ):
    """
    Reads ATCF-formatted file
    Args:
        'atcfFile': (str) - full path to the ATCF file
    Returns:
        dict: 'lat', 'lon', 'vmax', 'mslp','dates'
    """
    lines = open(atcfFile).readlines()
        
    myOcn  = []
    myCy   = []
    myDate = []
    myLat  = []
    myLon  = []
    myVmax = []
    myMSLP = []
    for line in lines:
        r = line.rstrip().split(',')
        myOcn.append  (r[0])
        myCy.append   (int(r[1]))
        myDate.append (datetime.strptime(r[2].strip(),'%Y%m%d%H'))
        latSign = -1.0
        if 'N' in r[6]:
            latSign = 1.0     
        myLat.append  (latSign*0.1*float(r[6][:-1]))
        lonSign = -1.0
        if 'E' in r[7]:
            lonSign = 1.0
        myLon.append  (lonSign*0.1*float(r[7][:-1]))
        myVmax.append (float(r[8]))
        myMSLP.append (float(r[9]))
    
    return { 
            'basin' : myOcn,    'cy' : myCy, 'dates' : myDate, 
            'lat'   : myLat,   'lon' : myLon,
            'vmax'  : myVmax, 'mslp' : myMSLP }


def read_track(ax,path,date):
    ike_track_file = '/scratch4/COASTAL/coastal/save/Saeed.Moghimi/models/NEMS/NEMS_inps/data/tracks/ike_bal092008.dat'
    track = readTrack(ike_track_file)
    keys = ['dates', 'lon', 'vmax', 'lat']
    for key in keys:
        tmp   = pd.DataFrame(track[key],columns=[key])

        #dfh   = df
        if 'trc' not in globals():
            trc = tmp
        else:
            trc  = pd.concat([trc,tmp],axis=1,join_axes=[trc.index])    
    
    
    
    trc = trc.drop_duplicates(subset='dates',keep='first')
    trc = trc.set_index (trc.dates)
    trc = trc.resample('H').interpolate()
    trc.drop('dates',axis=1,inplace=True)
    
    dates = datetime64todatetime(trc.index)
    
    return dates,trc.lon.values, trc.lat.values
    

def plot_track(ax,track,date=None):
    
    if date is not None:
        dates = np.array(track['dates'])
        ind = np.array(np.where((dates==date))).squeeze().item()
        ax.scatter(lon[ind],lat[ind],s=50,c='r',alpha=50)
    ax.plot(track['lon'],track['lat'],lw=2,c='r')
  
##### end of Funcs
