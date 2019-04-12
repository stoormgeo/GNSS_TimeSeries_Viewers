# How does a regional M6.6 compare to Tohoku? 

# Main tasks: 
# Read catalog
# Collect data
# Write data


import numpy as np
import matplotlib.pyplot as plt
from obspy import UTCDateTime, read
from obspy.clients.fdsn import Client
import collections
import sys
import haversine

EQcat = collections.namedtuple('EQcat', ["time","lat","lon","mag","name"]);

def configure():
	input_file = "many_eqs/data/global_catalog.txt";
	station="KMR";
	client = Client("NCEDC");
	station_coords=(40.2022, -123.7086); # kmr
	num_minutes=90.0;
	data_dir="many_eqs/data/";
	return [input_file, station, station_coords, client, num_minutes, data_dir];

def read_input_file(input_file):
	ifile=open(input_file,'r');
	times=[]; lats=[]; lons=[]; mags=[]; names=[];
	for line in ifile:
		temp=line.split();
		if temp[0]=="#":
			continue;
		else:
			times.append(temp[0]);
			lats.append(float(temp[1]));
			lons.append(float(temp[2]));
			mags.append(float(temp[3]));
			names.append(temp[-1]);
	ifile.close();
	catalog=EQcat(time=times, lat=lats, lon=lons, mag=mags, name=names);
	return catalog; 

def write_obspy_data(catalog, station, client, num_minutes, data_dir):
	for i in range(len(catalog.time)):
		# Get the data
		print(catalog.time[i]);
		print("Getting %s data for %s" % (station, catalog.name[i]) );
		t = UTCDateTime(catalog.time[i])
		st = client.get_waveforms("NC", station, "*", "HH*", t, t + num_minutes * 60, attach_response=True);
		st.remove_response(output="VEL");
		st.write(data_dir+station+"_"+catalog.name[i]+".mseed", format="MSEED");
	return;

def read_obspy_data(catalog, station, data_dir):
	st_total = [];
	for i in range(len(catalog.time)):
		st = read(data_dir+station+"_"+catalog.name[i]+".mseed");
		st_total.append(st);
	return st_total;

def plot_many_eqs(st_total, catalog):
	num_eqs=len(st_total);
	num_plot_rows=int(np.ceil(num_eqs/2));

	f, axarr = plt.subplots(num_plot_rows,2,sharex=True, figsize=(15,15));
	for i in range(len(st_total)):
		vert_index=np.mod(i,num_plot_rows);
		horiz_index=int(np.round(i/num_eqs));		
		st=st_total[i];
		tr=st[0];  # the first trace
		df=tr.stats.sampling_rate;
		npts=tr.stats.npts;
		x=np.arange(0,npts/df,1.0/df);

		st.filter("bandpass", freqmin=0.1, freqmax=1.5);

		h1=axarr[vert_index, horiz_index].plot(x,st[0],label='E');
		h2=axarr[vert_index, horiz_index].plot(x,st[1],label='N');
		h3=axarr[vert_index, horiz_index].plot(x,st[2],label='U');
		axarr[vert_index, horiz_index].set_ylim([-0.005, 0.005]);
		axarr[vert_index, horiz_index].set_ylabel('Vel (m/s)');
		axarr[vert_index, horiz_index].text(4000,0,catalog.name[i],fontsize=16);
		
	# axarr[vert_index, horiz_index].set_xlabel('Time (s)');
	axarr[0, 0].set_title(station+' Records ' ,fontsize=20);
	plt.savefig("many_eqs/waveforms_vel.png");
	return;


def plot_many_spectrograms(st_total, catalog):
	# This will eventually be a spectrogram for each earthquake. 
	num_eqs=len(st_total);
	num_plot_rows=int(np.ceil(num_eqs/2));
	f, axarr = plt.subplots(num_plot_rows,2,sharex=True, figsize=(15,15));  # a 2xn grid of plots
	for i in range(len(st_total)):
		vert_index=np.mod(i,num_plot_rows);
		horiz_index=int(np.round(i/num_eqs));
		st=st_total[i];
		tr=st[0];  # the first trace
		df=tr.stats.sampling_rate;
		npts=tr.stats.npts;
		x=np.arange(0,npts/df,1.0/df);
		# st.filter("bandpass", freqmin=0.5, freqmax=1.0);
		h1=axarr[vert_index,horiz_index].plot(x,st[0],label='E');
		axarr[vert_index, horiz_index].text(0,0,catalog.name[i],fontsize=16);
		axarr[vert_index, horiz_index].set_ylim([-0.005, 0.005]);
	axarr[0,0].set_title(station+' Records ' ,fontsize=20);
	plt.savefig("many_eqs/spectra.png");
	return;	


if __name__=="__main__":
	[input_file, station, station_coords, client, num_minutes, data_dir] = configure();
	catalog = read_input_file(input_file);
	# write_obspy_data(catalog, station, client, num_minutes, data_dir);
	st_total = read_obspy_data(catalog, station, data_dir);
	# plot_many_eqs(st_total, catalog);
	plot_many_spectrograms(st_total, catalog);



