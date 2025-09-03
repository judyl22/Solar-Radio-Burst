import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from adjustText import adjust_text

# for psp and stereo
def calc_drift_rate(bursts):
    bursts.columns = [col.strip() for col in bursts.columns]
    freq_change = bursts["High frequency (Hz)"] - bursts["Low frequency (Hz)"]
    bursts["Frequency Change"] = freq_change
    
    bursts['Start time'] = pd.to_datetime(bursts['Start time'], format='%Y-%m-%dT%H:%M', errors='coerce')
    bursts['End time'] = pd.to_datetime(bursts['End time'], format='%Y-%m-%dT%H:%M', errors='coerce')
    bursts['Duration (seconds)'] = (bursts['End time'] - bursts['Start time']).dt.total_seconds()
    
    drift_rate = bursts["Frequency Change"] / bursts["Duration (seconds)"]
    bursts["Drift Rate (Hz/s)"] = drift_rate
    return bursts

# for maven
def calc_drift_rate_energy(bursts):
    bursts.columns = [col.strip() for col in bursts.columns]

    bursts['Start Time (UTC)'] = pd.to_datetime(bursts['Start Time (UTC)'], errors='coerce')
    bursts['End Time (UTC)'] = pd.to_datetime(bursts['End Time (UTC)'], errors='coerce')

    bursts['Duration (seconds)'] = (bursts['End Time (UTC)'] - bursts['Start Time (UTC)']).dt.total_seconds()
    bursts['Energy Change (keV)'] = bursts['Start Energy (keV)'] - bursts['End Energy (keV)']
    return bursts

def make_csv(filepath, file_name):
    file = filepath.to_csv(f'{file_name}_added.csv', index=False)
    return file

def merge_common_date(dataset1, dataset2, dataset3, label1, label2, label3):
    dataset1['Date'] = dataset1['Start time'].dt.date
    dataset2['Date'] = dataset2['Start time'].dt.date
    dataset3['Date'] = dataset3['Start Time (UTC)'].dt.date

    common_dates = set(dataset1['Date']) & set(dataset2['Date']) & set(dataset3['Date'])

    dataset1_common = dataset1[dataset1['Date'].isin(common_dates)]
    dataset2_common = dataset2[dataset2['Date'].isin(common_dates)]
    dataset3_common = dataset3[dataset3['Date'].isin(common_dates)]

    # Add source label
    dataset1_common['Source'] = label1
    dataset2_common['Source'] = label2
    dataset3_common['Source'] = label3

    merged = dataset1_common.merge(dataset2_common, on='Date', suffixes=('_stereo', '_psp'))
    merged = merged.merge(dataset3_common, on='Date')
    return merged

def plot_energy_change_vs_duration(df, label):
    plt.figure(figsize=(10, 6))
    plt.scatter(df["Energy Change (keV)"], df["Duration (seconds)"], alpha=0.7, label=label, color="blue")

    df["Start Date"] = pd.to_datetime(df["Start Time (UTC)"]).dt.date

    texts = []
    for i, txt in enumerate(df["Start Date"]):
        texts.append(plt.text(df["Energy Change (keV)"].iloc[i], df["Duration (seconds)"].iloc[i], str(txt),
                          fontsize=8, alpha=0.75, color='blue'))

    plt.xscale("log")
    # plt.yscale("log")

    plt.xlabel("Energy Change (keV) (log scale)")
    plt.ylabel("Duration (seconds) (log scale)")
    plt.title(f"Log–Log Scatter Plot of Duration vs Energy Change {label}")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()
    # plt.show()

def plot_freq_change_vs_energy_change(df, label1, label2):
    plt.figure(figsize=(10, 6))
    plt.scatter(df["Energy Change (keV)"], df["Frequency Change_stereo"], alpha=0.7, label=label1, color="blue")
    plt.scatter(df["Energy Change (keV)"], df["Frequency Change_psp"], alpha=0.7, label=label2, color="red")

    texts = []
    for i, txt in enumerate(df["Date"]):
        texts.append(plt.text(df["Energy Change (keV)"].iloc[i], df["Frequency Change_stereo"].iloc[i], str(txt),
                              fontsize=8, alpha=0.75, color='blue'))
    for i, txt in enumerate(df["Date"]):
        texts.append(plt.text(df["Energy Change (keV)"].iloc[i], df["Frequency Change_psp"].iloc[i], str(txt),
                              fontsize=8, alpha=0.75, color='red'))
    
    plt.xscale("log")
    plt.yscale("log")
    
    plt.xlabel("Energy Change (keV) (log scale)")
    plt.ylabel("Frequench Change (Hz) (log scale)")
    plt.title(f"Log–Log Scatter Plot of Freq Change ({label1} & {label2}) vs Energy Change (Maven)")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.show()
    input("Hit enter to continue:")

def plot_power_fit(plt, df, label, num):
    color_array = ['blue', 'red', 'black', 'green']
    plt.scatter(df["Energy Change (keV)"], df[f"Frequency Change_{label}"], alpha=0.7, label=f"Maven vs {label}", color=color_array[num])

    x = df["Energy Change (keV)"].values
    y = df[f"Frequency Change_{label}"].values
    
    log_x = np.log10(x).reshape(-1, 1)
    log_y = np.log10(y)
    model = LinearRegression()
    model.fit(log_x, log_y)
    
    # Generate x range and corresponding fitted y
    x_fit = np.logspace(np.log10(x.min()), np.log10(x.max()), 200)
    y_fit = 10 ** (model.intercept_ + model.coef_[0] * np.log10(x_fit))
    
    plt.plot(x_fit, y_fit, color=color_array[num+2], linestyle='--', label=f'Best Fit ({label})')
    
    slope = model.coef_[0]
    intercept = model.intercept_

    # .3e is scientific notation with 3 decimal places
    # .3f is 3 digits after the decimal point
    print(f"Power law model for {label}: y = {10**intercept:.3e} * x^{slope:.3f}")
    
    texts = []
    for i, txt in enumerate(df["Date"]):
        texts.append(plt.text(df["Energy Change (keV)"].iloc[i], df[f"Frequency Change_{label}"].iloc[i], str(txt),
                              fontsize=8, alpha=0.75, color=color_array[num]))

    plt.xscale("log")
    plt.yscale("log")
    
    plt.xlabel("Energy Change (keV) (log scale)")
    plt.ylabel("Frequench Change (Hz) (log scale)")
    plt.title("Power Fit: Frequency Change vs Energy Change")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()

def plot_cubic_fit(plt, df, label, num):
    color_array = ['blue', 'red', 'black', 'green']
    
    x = df["Energy Change (keV)"].values.reshape(-1, 1)
    y = df[f"Frequency Change_{label}"].values

    poly = PolynomialFeatures(degree=3, include_bias=False)
    x_poly = poly.fit_transform(x)

    # Fit the cubic model
    model = LinearRegression()
    model.fit(x_poly, y)

    x_fit = np.linspace(x.min(), x.max(), 200).reshape(-1, 1)
    x_fit_poly = poly.transform(x_fit)
    y_fit = model.predict(x_fit_poly)

    plt.scatter(x, y, alpha=0.7, label=f"Maven vs {label}", color=color_array[num])
    plt.plot(x_fit, y_fit, color=color_array[num + 2], linestyle='--', label=f'Cubic Fit ({label})')

    coef = model.coef_
    intercept = model.intercept_
    print(f"Cubic model for {label}: y = {intercept:.2e} + {coef[0]:.2e}*x + {coef[1]:.2e}*x² + {coef[2]:.2e}*x³")

    texts = []
    for i, txt in enumerate(df["Date"]):
        texts.append(plt.text(df["Energy Change (keV)"].iloc[i], df[f"Frequency Change_{label}"].iloc[i], str(txt),
                              fontsize=8, alpha=0.75, color=color_array[num]))

    plt.xscale("log")
    plt.yscale("log")
    
    plt.xlabel("Energy Change (keV)")
    plt.ylabel("Frequency Change (Hz)")
    plt.title("Cubic Fit: Frequency Change vs Energy Change")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()