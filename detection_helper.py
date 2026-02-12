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
from numpy.linalg import LinAlgError

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

def hough_angle(times_arr, freq_log, freq_change=14718120.082815735, time_duration=2699.503105590062):
    # times in second
    # times_arr in UTC
    target_freq = max(freq_log) - freq_change
    target_freq_index = 0
    while target_freq_index < len(freq_log) and freq_log[target_freq_index] < target_freq:
        target_freq_index += 1
    target_freq_index_reverse = len(freq_log) - target_freq_index

    times_arr_UNX = UTC_to_UNX(times_arr)
    target_time = times_arr_UNX[1] + time_duration
    target_time_index = 0
    while target_time_index < len(times_arr_UNX) and times_arr_UNX[target_time_index] < target_time:
        target_time_index += 1

    angle_rad = math.atan2(-target_freq_index_reverse, target_time_index)
    angle_deg = math.degrees(angle_rad) + 90

    return target_freq_index_reverse, target_time_index, angle_deg

def plot_bmap(times_arr, freq_log_exp, bmap, lines=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    p = ax.pcolormesh(times_arr, freq_log_exp, 1-bmap.T, shading="auto", cmap="gray")
    plt.colorbar(p, ax=ax, label="Binary")

    if lines:
        for (x0, y0), (x1, y1) in lines:
            t0, t1 = times_arr[y0], times_arr[y1]
            f0, f1 = freq_log_exp[x0], freq_log_exp[x1]
            ax.plot([t0, t1], [f0, f1], color='red')
    
    plt.xlabel("Time")
    plt.ylabel("Frequency [Hz]")
    # plt.yscale('log')
    plt.title("Grouped Bursts")
    # plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_spectrum(times_arr, freq_log_exp, data_arr_log, lines=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    p = ax.pcolormesh(times_arr, freq_log_exp, data_arr_log.T, norm=LogNorm())
    plt.colorbar(p, ax=ax, label="Power")

    if lines:
        for (x0, y0), (x1, y1) in lines:
            t0, t1 = times_arr[y0], times_arr[y1]
            f0, f1 = freq_log_exp[x0], freq_log_exp[x1]
            ax.plot([t0, t1], [f0, f1], color='red')
    
    plt.xlabel("Time")
    plt.ylabel("Frequency [Hz]")
    # plt.yscale('log')
    plt.title("Grouped Bursts")
    # plt.grid(True)
    plt.tight_layout()
    plt.show()

def longest_line(lines):
    longest_line = None
    longest_length_sqr = 0

    for line in lines:
        (x0, y0), (x1, y1) = line
        dx = x1 - x0
        dy = y1 - y0
        length_sqr = dx*dx + dy*dy
        if length_sqr > longest_length_sqr:
            longest_length_sqr = length_sqr
            longest_line = line

    longest_length = math.sqrt(longest_length_sqr) 
    return longest_line, longest_length_sqr


def left_pts(lines, times_arr, freq_arr):
    pts_idx = []
    pts_val = []
    seen_x = set()

    for (x0, y0), (x1, y1) in lines:
        # right most
        # xL, yL = x0, y0
        # left most
        x_left, y_left = x1, y1

        if x_left in seen_x:
            continue
        seen_x.add(x_left)

        pts_idx.append((x_left, y_left))
        pts_val.append((times_arr[y_left], freq_arr[x_left]))

    pts_idx = np.array(pts_idx, dtype=int)
    pts_val = np.array(pts_val, dtype=object)

    order = np.argsort(pts_val[:, 1].astype(float))[::-1]

    return pts_idx[order], pts_val[order]

def right_pts(lines, times_arr, freq_arr):
    pts_idx = []
    pts_val = []
    seen_x = set()

    for (x0, y0), (x1, y1) in lines:
        # right most
        x_right, y_right = x0, y0
        # left most
        # x_left, y_left = x1, y1

        if x_right in seen_x:
            continue
        seen_x.add(x_right)

        pts_idx.append((x_right, y_right))
        pts_val.append((times_arr[y_right], freq_arr[x_right]))

    pts_idx = np.array(pts_idx, dtype=int)
    pts_val = np.array(pts_val, dtype=object)

    order = np.argsort(pts_val[:, 1].astype(float))[::-1]

    return pts_idx[order], pts_val[order]

def plot_boundary_pts(times_arr, freq_log_exp, bmap, pts_val_left, pts_val_right):
    fig, ax = plt.subplots(figsize=(10, 6))    
    p = ax.pcolormesh(times_arr, freq_log_exp, 1-bmap.T, shading="auto", cmap="gray")
    plt.colorbar(p, ax=ax, label="Binary")
    
    ax.scatter(pts_val_left[:,0], pts_val_left[:,1], s=10)
    ax.scatter(pts_val_right[:,0], pts_val_right[:,1], s=10)
    
    plt.xlabel("Time")
    plt.ylabel("Frequency [Hz]")
    # plt.yscale('log')
    plt.title("Grouped Bursts")
    # plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_line_slice(bmap, times_arr, freq_log_exp, data_arr_log, x_slice=[0,800], y_slice=60, plot=True):
    # y_slice is the index that seperate high and low
    
    x_slice_start = x_slice[0]
    x_slice_stop = x_slice[1]
    bmap_slice = bmap[x_slice_start:x_slice_stop]
    times_arr_slice = times_arr[x_slice_start:x_slice_stop]
    data_arr_log_slice = data_arr_log[x_slice_start:x_slice_stop]
    
    # theta=np.deg2rad(np.linspace(39, 40, 120))
    # line_gap=40
    theta=np.deg2rad(np.linspace(30, 40, 2000))
    lines_high = hough_detect(bmap_slice[:, y_slice:], data_arr_log_slice, threshold=1, line_gap=30, line_length=80, theta=theta)
    longest_line_high, longtest_line_length_high = longest_line(lines_high)
    
    # theta=np.deg2rad(np.linspace(4, 5, 120))
    theta=np.deg2rad(np.linspace(3, 6, 2000))
    lines_low = hough_detect(bmap_slice[:, :y_slice], data_arr_log_slice, threshold=1, line_gap=30, line_length=80, theta=theta)
    longest_line_low, longtest_line_length_low = longest_line(lines_low)

    if (longest_line_high is not None) and (longest_line_low is not None):
        (x1, y1), (x2, y2) = longest_line_high
        longest_line_high = ((x1 + y_slice, y1), (x2 + y_slice, y2))
    
        (x1, y1), (x2, y2) = longest_line_low
        longest_line_low = ((x1, y1), (x2, y2))
        
        if plot == True:
            plot_bmap(times_arr_slice, freq_log_exp, bmap_slice, [longest_line_low, longest_line_high])
        return longest_line_low, longest_line_high
    else:
        return None, None

def all_lines_day(bmap, times_arr, freq_log_exp, data_arr_log):
    i = 0
    lines = []
    while i < (len(times_arr)-501):
        longest_line_low, longest_line_high = plot_line_slice(bmap, times_arr, freq_log_exp, data_arr_log, x_slice = [0+i,800+i], plot=False)
        if (longest_line_high is not None) and (longest_line_low is not None):
            (x1, y1), (x2, y2) = longest_line_high
            longest_line_high = ((x1, y1+i), (x2, y2+i))
            
            (x1, y1), (x2, y2) = longest_line_low
            longest_line_low = ((x1, y1+i), (x2, y2+i))
            lines.append(longest_line_high)
            lines.append(longest_line_low)
        i = i + 250
    return lines