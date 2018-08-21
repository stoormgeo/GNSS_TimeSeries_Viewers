#   Goal: Develop tools for removing seasonals by...
#    fit: fits seasonals and linear trend by least squares inversion.
#   noel: uses noel's fits of inter-SSE velocities and seasonal terms.
#  notch: removes the 1-year and 6-month components by notch filter.
#  grace: uses GRACE loading model interpolated between monthly points where available, and linear inversion where not available.
#    stl: not supported yet. 

import numpy as np
import matplotlib.pyplot as plt 
import collections
import datetime as dt 
from scipy import signal
import gps_io_functions
import gps_ts_functions

# For reference of how this gets returned from the read functions.
Timeseries = collections.namedtuple("Timeseries",['name','coords','dtarray','dN', 'dE','dU','Sn','Se','Su','EQtimes']);  # in mm
Parameters = collections.namedtuple("Parameters",['station','filename','outliers_remove', 'outliers_def',
	'earthquakes_remove','earthquakes_dir','offsets_remove','offsets_dir','reference_frame','fit_table', 'grace_dir']);


def compare_single_seasonals(station_name, offsets_remove=1, earthquakes_remove=0, outliers_remove=0):
	MyParams=configure(station_name, offsets_remove, earthquakes_remove, outliers_remove);
	[myData]=gps_io_functions.read_pbo_pos_file(MyParams.filename);
	[updatedData, lssq_fit, noel_fit, notch_filt, grace_filt]=compute(myData,MyParams);
	single_ts_plot(updatedData,lssq_fit,noel_fit,notch_filt,grace_filt,MyParams);


# -------------- CONFIGURE ------------ # 
def configure(station, offsets_remove, earthquakes_remove, outliers_remove):
	filename="../../GPS_POS_DATA/PBO_Data/"+station+".pbo.final_nam08.pos"
	earthquakes_dir="../../GPS_POS_DATA/PBO_Event_Files/"
	offsets_dir="../../GPS_POS_DATA/Offsets/"
	fit_table="../../GPS_POS_DATA/Velocity_Files/Bartlow_interETSvels.txt"
	grace_dir="../../GPS_POS_DATA/GRACE_loading_model/"
	outliers_def       = 15.0;  # mm away from average. 
	reference_frame    = 0;
	MyParams=Parameters(station=station,filename=filename, outliers_remove=outliers_remove, outliers_def=outliers_def, 
		earthquakes_remove=earthquakes_remove, earthquakes_dir=earthquakes_dir, offsets_remove=offsets_remove, offsets_dir=offsets_dir, 
		reference_frame=reference_frame, fit_table=fit_table, grace_dir=grace_dir);
	print("------- %s --------" %(station));
	print("Viewing station %s, earthquakes_remove=%d, outliers_remove=%d " % (station, earthquakes_remove, outliers_remove) );
	return MyParams;


# -------------- COMPUTE ------------ # 
def compute(myData, MyParams):
	newData=myData; 
	if MyParams.offsets_remove==1:  # First step: remove offsets and earthquakes
		newData=gps_ts_functions.remove_offsets(newData, MyParams.offsets_dir);
	if MyParams.outliers_remove==1:  # Second step: remove outliers
		newData=gps_ts_functions.remove_outliers(newData, MyParams.outliers_def);
	if MyParams.earthquakes_remove==1:
		newData=gps_ts_functions.remove_earthquakes(newData, MyParams.earthquakes_dir);

	# A few different types of seasonal removal. 
	notrend=gps_ts_functions.make_detrended_option(newData, 0, 'fit', MyParams.fit_table, MyParams.grace_dir);
	lssq_fit=gps_ts_functions.make_detrended_option(newData, 1, 'fit', MyParams.fit_table, MyParams.grace_dir);
	noel_fit=gps_ts_functions.make_detrended_option(newData, 1, 'noel', MyParams.fit_table, MyParams.grace_dir);
	notch_filt=gps_ts_functions.make_detrended_option(newData, 1, 'notch', MyParams.fit_table, MyParams.grace_dir);
	grace_filt=gps_ts_functions.make_detrended_option(newData, 1, 'grace', MyParams.fit_table, MyParams.grace_dir);

	return [notrend, lssq_fit, noel_fit, notch_filt, grace_filt];


# -------------- OUTPUTS ------------ # 
def single_ts_plot(ts_obj, lssq_fit, noel_fit, notch_filt, grace_filt, MyParams):
	# The major figure
	dpival=100;
	offset_val=15;
	text_val=3;
	labeldate=dt.datetime.strptime("20070101", "%Y%m%d");

	plt.figure(figsize=(15,15),dpi=dpival);
	plt.plot_date(ts_obj.dtarray, ts_obj.dE+0*offset_val,color='blue',markeredgecolor='black',markersize=1.5);
	plt.plot_date(lssq_fit.dtarray, lssq_fit.dE+1*offset_val,marker='D',markersize=1.0,color='red');
	plt.plot_date(noel_fit.dtarray, noel_fit.dE+2*offset_val,marker='D',markersize=1.0,color='blue');
	plt.plot_date(notch_filt.dtarray, notch_filt.dE+3*offset_val,marker='D',markersize=1.0,color='green');
	plt.plot_date(grace_filt.dtarray, grace_filt.dE+4*offset_val,marker='D',markersize=1.0,color='magenta');
	plt.grid(linestyle='--',linewidth=0.5);	
	plt.text(labeldate,0*offset_val+text_val,'Uncorrected',fontsize=22,color='black');
	plt.text(labeldate,1*offset_val+text_val,'LsSq Fit',fontsize=22,color='red');
	plt.text(labeldate,2*offset_val+text_val,'Inter-SSE',fontsize=22,color='blue');
	plt.text(labeldate,3*offset_val+text_val,'Notch filter',fontsize=22,color='green');
	plt.text(labeldate,4*offset_val+text_val,'GRACE load model',fontsize=22,color='magenta');
	plt.ylabel('detrended east (mm)',fontsize=22)
	plt.gca().tick_params(labelsize=22);
	title_name=ts_obj.name+" Seasonal Corrections - East";
	plt.title(title_name,fontsize=24);
	savename="single_plots/seasonal_"+ts_obj.name;
	savename=savename+"_east.jpg"
	plt.savefig(savename,dpi=dpival);

	plt.figure(figsize=(15,15),dpi=dpival);
	plt.plot_date(ts_obj.dtarray, ts_obj.dN+0*offset_val,color='blue',markeredgecolor='black',markersize=1.5);
	plt.plot_date(lssq_fit.dtarray, lssq_fit.dN+1*offset_val,marker='D',markersize=1.5,color='red');
	plt.plot_date(noel_fit.dtarray, noel_fit.dN+2*offset_val,marker='D',markersize=1.5,color='blue');
	plt.plot_date(notch_filt.dtarray, notch_filt.dN+3*offset_val,marker='D',markersize=1.5,color='green');
	plt.plot_date(grace_filt.dtarray, grace_filt.dN+4*offset_val,marker='D',markersize=1.0,color='magenta');
	plt.grid(linestyle='--',linewidth=0.5);	
	plt.text(labeldate,0*offset_val+text_val,'Uncorrected',fontsize=22,color='black');
	plt.text(labeldate,1*offset_val+text_val,'LsSq Fit',fontsize=22,color='red');
	plt.text(labeldate,2*offset_val+text_val,'Inter-SSE',fontsize=22,color='blue');
	plt.text(labeldate,3*offset_val+text_val,'Notch filter',fontsize=22,color='green');	
	plt.text(labeldate,4*offset_val+text_val,'GRACE load model',fontsize=22,color='magenta');
	plt.ylabel('detrended north (mm)',fontsize=22)
	plt.gca().tick_params(labelsize=22);
	title_name=ts_obj.name+" Seasonal Corrections - North";
	plt.title(title_name,fontsize=24);
	savename="single_plots/seasonal_"+ts_obj.name;
	savename=savename+"_north.jpg"
	plt.savefig(savename,dpi=dpival);

	plt.figure(figsize=(15,15),dpi=dpival);
	plt.plot_date(ts_obj.dtarray, ts_obj.dU+0*offset_val,color='blue',markeredgecolor='black',markersize=1.5);
	plt.plot_date(lssq_fit.dtarray, lssq_fit.dU+2*offset_val,marker='D',markersize=1.5,color='red');
	plt.plot_date(noel_fit.dtarray, noel_fit.dU+4*offset_val,marker='D',markersize=1.5,color='blue');
	plt.plot_date(notch_filt.dtarray, notch_filt.dU+6*offset_val,marker='D',markersize=1.5,color='green');
	plt.plot_date(grace_filt.dtarray, grace_filt.dU+8*offset_val,marker='D',markersize=1.0,color='magenta');	
	plt.grid(linestyle='--',linewidth=0.5);	
	plt.text(labeldate,0*offset_val+text_val,'Uncorrected',fontsize=22,color='black');
	plt.text(labeldate,2*offset_val+text_val,'LsSq Fit',fontsize=22,color='red');
	plt.text(labeldate,4*offset_val+text_val,'Inter-SSE',fontsize=22,color='blue');
	plt.text(labeldate,6*offset_val+text_val,'Notch filter',fontsize=22,color='green');	
	plt.text(labeldate,8*offset_val+text_val,'GRACE load model',fontsize=22,color='magenta');
	plt.ylabel('detrended vertical (mm)',fontsize=22)
	plt.gca().tick_params(labelsize=22);
	title_name=ts_obj.name+" Seasonal Corrections - Vertical";
	plt.title(title_name,fontsize=24);
	savename="single_plots/seasonal_"+ts_obj.name;
	savename=savename+"_vert.jpg"
	plt.savefig(savename,dpi=dpival);
	return;
