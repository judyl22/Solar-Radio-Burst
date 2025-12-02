import pyspedas
import pytplot
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import matplotlib.cm as cm
# %matplotlib tk

import scipy
from scipy import interpolate,optimize
from scipy.optimize import curve_fit
from skimage.transform import probabilistic_hough_line

import helper
from helper import UTC_to_UNX
from helper import UNX_to_UTC
from helper import find_closest_index_dt

import math
from scipy.interpolate import interp1d

def return_arr(start='2023-01-03', end='2023-08-20'):
    time_clip = True
    no_update = False
    varnames_hfr = 'psp_fld_l3_rfs_hfr_auto_averages_ch0_V1V2'
    varnames_lfr = 'psp_fld_l3_rfs_lfr_auto_averages_ch0_V1V2'
    rfs_hfr_vars = pyspedas.psp.fields(trange=[start, end], datatype='rfs_hfr', level='l3', no_update=no_update, varnames=varnames_hfr)
    rfs_lfr_vars = pyspedas.psp.fields(trange=[start, end], datatype='rfs_lfr', level='l3', no_update=no_update, varnames=varnames_lfr)
    rfs_ch0_hfr = pyspedas.get('psp_fld_l3_rfs_hfr_auto_averages_ch0_V1V2')
    rfs_ch0_lfr = pyspedas.get('psp_fld_l3_rfs_lfr_auto_averages_ch0_V1V2')
    data_hfr = rfs_ch0_hfr.y
    freq_hfr = rfs_ch0_hfr.v
    times_hfr = rfs_ch0_hfr.times

    data_lfr = rfs_ch0_lfr.y
    freq_lfr = rfs_ch0_lfr.v
    times_lfr = rfs_ch0_lfr.times

    if (len(times_lfr) < len(times_hfr)):
        times_arr = times_lfr
        freq_arr = np.concatenate((freq_lfr[0], freq_hfr[0]))
        data_arr = np.concatenate((data_lfr, data_hfr[:-np.abs(len(times_hfr) - len(times_lfr))]), axis = 1)
    else:
        times_arr = times_hfr
        freq_arr = np.concatenate((freq_lfr[0], freq_hfr[0]))
        data_arr = np.concatenate((data_lfr[:-np.abs(len(times_hfr) - len(times_lfr))], data_hfr), axis = 1)

    return times_arr, freq_arr, data_arr

def convert_data_log(freq_arr, full_data): # times_arr):
    freq_log = np.logspace(np.log10(freq_arr.min()), np.log10(freq_arr.max()), len(freq_arr))
    # times_len = len(times_arr)
    # freq_log = np.logspace(np.log10(freq_arr.min()), np.log10(freq_arr.max()), times_len)
    freq_log_exp = np.log10(freq_log)
    new_full_data = full_data.copy()
    # new_full_data = np.empty((times_len, times_len))
    for i, data_col in enumerate(full_data):
        interpolate_func = interp1d(freq_arr, data_col, bounds_error=False)
        data_log = interpolate_func(freq_log)
        new_full_data[i] = data_log

    return freq_log, freq_log_exp, new_full_data

def convert_data_log_square(freq_arr, times_arr, full_data):
    mins_day = 60 * 24 # how many minutes in a day
    freq_log = np.logspace(np.log10(freq_arr.min()), np.log10(freq_arr.max()), mins_day)
    freq_log_exp = np.log10(freq_log) 

    times_arr_UNX = UTC_to_UNX(times_arr)
    new_times_arr_UNX = np.linspace(times_arr_UNX.min(), times_arr_UNX.max(), mins_day)
    new_times_arr = UNX_to_UTC(new_times_arr_UNX)

    temp_data = np.empty((len(times_arr), mins_day))
    for i, data_col in enumerate(full_data):
        interpolate_func = interp1d(freq_arr, data_col, bounds_error=False)
        data_log = interpolate_func(freq_log)
        temp_data[i] = data_log

    ret_data = np.empty((mins_day, mins_day))
    for j in range(mins_day):
        data_row = temp_data[:, j]
        interpolate_func = interp1d(times_arr_UNX, data_row, bounds_error=False)
        data = interpolate_func(new_times_arr_UNX)
        ret_data[:, j] = data

    return freq_log, freq_log_exp, new_times_arr, ret_data

def bmap_row_mean_loop_new(times_arr, full_data, ratio=0.95, min_duration=60):
    # min_duration in seconds
    # min_duration_UNX = UTC_to_UNX(f'2023-08-19T00:0{min_duration}:00') - UTC_to_UNX('2023-08-19T00:00:00') # min_duration in minutes
    freq_num = full_data.shape[1]
    bmap = np.zeros_like(full_data)

    for row in range(freq_num):
        bmap[:, row] = full_data[:, row] > np.quantile(full_data[:, row], ratio)

    # find min_length for pixel
    times_arr_UNX = UTC_to_UNX(times_arr)
    target_value = times_arr_UNX[0] + min_duration
    min_length = np.searchsorted(times_arr_UNX, target_value)
    
    bmap_new = np.zeros_like(bmap)
    # loop through each row
    for row in range(freq_num):
        # loop through each datapoint/column in each row
        for datapoint in range(bmap.shape[0] - min_length):
            if bmap[datapoint, row] == True:
                all_on = True
                for i in range(1, min_length+1):
                    if bmap[datapoint+i, row] == False:
                        all_on = False
                if all_on == True:
                    bmap_new[datapoint:datapoint+min_length+1, row] = True
    
    return bmap_new

def hough_detect(bmap,dyspec,threshold=50,line_gap=10,line_length=25,
            theta=np.linspace(np.pi/2-np.pi/8,np.pi/2-1/180*np.pi,300)):
    lines = probabilistic_hough_line(bmap, threshold=threshold,line_gap=line_gap,line_length=line_length,
                                 theta=theta)
    return lines

def line_grouping_new(times_arr, freq_log, lines, time_diff=300, freq_diff=10000):
    # freq_diff in Hz
    # time_diff in seconds

    # time_diff = UTC_to_UNX(f'2023-08-19T00:0{time_diff}:00') - UTC_to_UNX('2023-08-19T00:00:00') # time_diff in minutes
    
    lines = sorted(lines, key=lambda line: (line[1][1]))
    line_sets = []
    line_sets_actual = []
    for line in lines:
        in_group = False
        line_start_time = UTC_to_UNX(times_arr[line[1][1]])
        line_end_time = UTC_to_UNX(times_arr[line[0][1]])
        line_start_freq = freq_log[line[1][0]]
        line_end_freq = freq_log[line[0][0]]
        
        for idx, line_avg in enumerate(line_sets):
            line_avg_start_time = UTC_to_UNX(times_arr[line_avg[1][1]])
            line_avg_end_time = UTC_to_UNX(times_arr[line_avg[0][1]])
            line_avg_start_freq = freq_log[line_avg[1][0]]
            line_avg_end_freq = freq_log[line_avg[0][0]]
                                 
            start_time_diff = (abs(line_start_time - line_avg_start_time) < time_diff)
            end_time_diff = (abs(line_end_time - line_avg_end_time) < time_diff)
            start_freq_diff = (abs(line_start_freq - line_avg_start_freq) < freq_diff)
            end_freq_diff = (abs(line_end_freq - line_avg_end_freq) < freq_diff)
            if (start_time_diff and start_freq_diff and end_time_diff and end_freq_diff):
                in_group = True
                line_avg = (
                    (round((line_avg[0][0] + line[0][0]) / 2), round((line_avg[0][1] + line[0][1]) / 2)),
                    (round((line_avg[1][0] + line[1][0]) / 2), round((line_avg[1][1] + line[1][1]) / 2))
                )
                line_sets[idx] = line_avg
        if in_group == False:
            line_sets.append(line)
            line_start_time_actual = UNX_to_UTC(line_start_time)
            line_end_time_actual = UNX_to_UTC(line_end_time)
            line_actual = ((str(line_start_time_actual), line_start_freq), (str(line_end_time_actual), line_end_freq))
            line_sets_actual.append(line_actual)

    # line_sets return the idx of the lines
    # line_sets_actual return the real time & freq of the events
    return line_sets, line_sets_actual

def find_unit(freq_log_exp, times_arr):
    # return val:
    # freq_gap return how can the exponent of 10 grows for each index
    # times_gap_UNX return in seconds
    freq_gap = freq_log_exp[1] - freq_log_exp[0]
    start_time = times_arr[0]
    end_time = times_arr[1]
    times_gap_UNX = UTC_to_UNX(end_time) - UTC_to_UNX(start_time)
    # times_gap = UNX_to_UTC(times_gap_UNX).minute
    return freq_gap, times_gap_UNX