import pyspedas
from pytplot import tplot, tplot_names, options, get_data

# example of a Type III radio burst

trange = ['2019-04-02/15:30', '2019-04-02/16:00']
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_hfr', level='l3')
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_lfr', level='l3')
tplot('psp_fld_l3_rfs_?fr_PSD_FLUX')

# Jovian emission (polarized)

trange = ['2019-09-09/11:00', '2019-09-09/19:00']
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_hfr', level='l3')
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_lfr', level='l3')
tplot(['psp_fld_l3_rfs_hfr_PSD_FLUX','psp_fld_l3_rfs_hfr_STOKES_V'])


# during a rotation

trange = ['2020-08-05/12:00', '2020-08-05/20:00']
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_hfr', level='l3')
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_lfr', level='l3')

options('psp_fld_l3_rfs_hfr_auto_averages_ch0_V1V2', 'zrange', [1e-17,5e-17])
options('psp_fld_l3_rfs_lfr_auto_averages_ch0_V1V2', 'zrange', [1e-17,5e-17])

tplot(['psp_fld_l3_rfs_hfr_auto_averages_ch0_V1V2','psp_fld_l3_rfs_lfr_auto_averages_ch0_V1V2','psp_fld_l3_rfs_lfr_ch0_V1V2_J2000'])


# near perihelion

trange = ['2023-09-27/12:00', '2023-09-28/12:00']
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_hfr', level='l3')
pyspedas.psp.fields(trange=trange, time_clip=True, datatype='rfs_lfr', level='l3')

options('psp_fld_l3_rfs_hfr_auto_averages_ch0_V1V2', 'zrange', [1e-16,1e-13])
options('psp_fld_l3_rfs_lfr_auto_averages_ch0_V1V2', 'zrange', [1e-16,1e-13])

tplot(['psp_fld_l3_rfs_hfr_auto_averages_ch0_V1V2','psp_fld_l3_rfs_lfr_auto_averages_ch0_V1V2','psp_fld_l3_rfs_lfr_solar_distance'])

# List all RFS variables

tplot_names()


# get the data

dat = get_data('psp_fld_l3_rfs_hfr_auto_averages_ch0_V1V2')

print(dat)