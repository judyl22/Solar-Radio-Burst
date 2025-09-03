import cdflib
import pyspedas
import pytplot
from pytplot import tplot, tplot_names, options, get_data
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm


# Time range
trange_i = ['2022-12-27', '2022-12-27']
no_update = False
time_clip = False
zrange = [1e-20, 1e-15]

# This line downloads data from the WAVES instrument on STEREO
# (also called S/WAVES or SWAVES) over the time range 'trange_i'
# with option to cut plot only down to the trange_i
# ('time_clip', set to True or False). The keyword 'no_update' will
# restrict the function to loading already-downloaded
# data. The keyword datatype can be set to 'lfr' or 'hfr' for
# low-frequency and high-frequency ranges respectively.

st_lfr = pyspedas.stereo.waves(
    trange=trange_i, time_clip=time_clip,
    datatype='lfr', no_update=no_update)

# You can make a tplot of the power spectral density (PSD)
# This is comparable to psp_fld_l2_rfs_lfr_auto_averages_ch0_V1V2,
# which is the automatically generated power spectral density
# across the V1 and V2 antenna
# pytplot.tplot(['PSD_FLUX'])

# Unfortunately, the PSD for SWAVES lfr is named the same as the PSD for SWAVES
# hfr, and will get overwritten if we just load the hfr data.
# To circumvent this, we will use store_data to copy the variable
# and rename it to 'ST_A_lfr_PSD':
pytplot.store_data('PSD_FLUX', newname='ST_A_lfr_PSD')

# Change the y axis label so it specifies this is the LFR, also set the zrange:
pytplot.options(
    'ST_A_lfr_PSD',
    opt_dict={'ytitle': 'STEREO A\nLFR PSD', 'zrange': zrange})

# Now download the hfr data:
st_hfr = pyspedas.stereo.waves(
    trange=trange_i, time_clip=time_clip,
    datatype='hfr', no_update=no_update)

# Also update the ylabel for this so it's specific, and uses the same zrange:
pytplot.options(
    'PSD_FLUX',
    opt_dict={'ytitle': 'STEREO A\nHFR PSD', 'zrange': zrange})

# Make the tplot:
pytplot.tplot(['PSD_FLUX', 'ST_A_lfr_PSD'])