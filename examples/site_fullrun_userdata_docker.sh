#!/bin/sh -f

cwd=$(pwd)

## site name from input, by default 'kougarok'
SITE=$1
if [ $SITE = '']; then
    SITE=kougarok
fi

if [ $SITE = 'kougarok']; then
    SITE_CODE=AK-K64G
elif [ $SITE = 'council']; then
    SITE_CODE=AK-CLG
elif [ $SITE = 'teller']; then
    SITE_CODE=AK-TLG
elif [ $SITE = 'beo']; then
    SITE_CODE=AK-BEOG
else
    echo "not supported site name: $SITE"
    echo "should be one of: kougarok, council, teller, beo"
    exit &?
fi

cd /tools/OLMT

if python3 ./site_fullrun.py \
      --site $SITE_CODE --sitegroup NGEEArctic --caseidprefix OLMT \
      --nyears_ad_spinup 200 --nyears_final_spinup 600 --tstep 1 \
      --machine docker --compiler gnu --mpilib openmpi \
      --cpl_bypass --gswp3 \
      --model_root /E3SM \
      --caseroot /output \
      --ccsm_input /inputdata \
      --runroot /output \
      --spinup_vars \
      --nopointdata \
      --metdir /inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v2.c180716_NGEE-Grid/cpl_bypass_$SITE-Grid \
      --domainfile /inputdata/share/domains/domain.clm/domain.lnd.1x1pt_$SITE-GRID_navy.nc \
      --surffile /inputdata/lnd/clm2/surfdata_map/surfdata_1x1pt_$SITE-GRID_simyr1850_c360x720_c171002.nc \
      --landusefile /inputdata/lnd/clm2/surfdata_map/landuse.timeseries_1x1pt_$SITE-GRID_simyr1850-2015_c180423.nc \
      & sleep 10

then
  wait

  echo "DONE docker ELM runs !"

else
  exit &?
fi

cd ${cwd}


