import pyspedas
from pytplot import tplot, tplot_names, options, get_data
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

trange = ['2023-05-01/00:00', '2023-05-01/23:59']
no_update = False
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_hfr', level='l3', no_update=no_update)
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_lfr', level='l3', no_update=no_update)

options('psp_fld_l3_rfs_hfr_auto_averages_ch0_V1V2', 'yrange', [1e6, 2*1e7])
options('psp_fld_l3_rfs_lfr_auto_averages_ch0_V1V2', 'yrange', [1e4, 1e6])

tplot(['psp_fld_l3_rfs_hfr_auto_averages_ch0_V1V2',
       'psp_fld_l3_rfs_lfr_auto_averages_ch0_V1V2'
      ])