import numpy as np
import pandas as pd
from IPython.display import FileLink
from pytplot import get_data
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from sklearn.linear_model import LinearRegression
from adjustText import adjust_text

import radio_burst_analysis
from radio_burst_analysis import *
# from importlib import reload
# reload(radio_burst_analysis)

file_path = 'stereo_maven_psp_both.csv'
bursts = pd.read_csv(file_path)
stereo = bursts.iloc[:, 0:5]
psp = bursts.iloc[:, 5:10]
psp.columns = [col.replace('.1', '') for col in psp.columns]
# test
file_path = 'maven_descending_full_clean.csv'
maven = pd.read_csv(file_path)

stereo = calc_drift_rate(stereo)
psp = calc_drift_rate(psp)
maven = calc_drift_rate_energy(maven)

make_csv(stereo, 'stereo')
make_csv(psp, 'psp')
make_csv(maven, 'maven')

merged = merge_common_date(stereo, psp, maven, "STEREO", "PSP", "MAVEN")
merged = merged.drop(range(15, 21), axis=0)
merged = merged.drop(range(25, 31), axis=0)
merged = merged.drop(range(39, 47), axis=0)
merged = merged.drop(range(48, 50), axis=0)
merged.to_csv("merged.csv", index=False)

plot_energy_change_vs_duration(maven, "MAVEN")
plot_freq_change_vs_energy_change(merged, "STEREO", "PSP")

# Power law model for stereo
plt.figure(figsize=(10, 6))
plot_power_fit(plt, merged, "stereo", 0)
# plt.show()

# Power law model for psp
plt.figure(figsize=(10, 6))
plot_power_fit(plt, merged, "psp", 0)
# plt.show()

# Power law model for both overlapped
plt.figure(figsize=(10, 6))
plot_power_fit(plt, merged, "stereo", 0)
plot_power_fit(plt, merged, "psp", 1)
plt.show()
input("Hit enter to continue:")

# Cubic model for stereo
plt.figure(figsize=(10, 6))
plot_cubic_fit(plt, merged, "stereo", 0)
# plt.show()

# Cubic model for psp
plt.figure(figsize=(10, 6))
plot_cubic_fit(plt, merged, "psp", 0)
# plt.show()

# Cubic model for both overlapped
plt.figure(figsize=(10, 6))
plot_cubic_fit(plt, merged, "stereo", 0)
plot_cubic_fit(plt, merged, "psp", 1)
plt.show()
input("Hit enter to continue:")