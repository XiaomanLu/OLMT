#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 20:07:47 2026

@author: x5l
"""

import pickle

# Indir = '/Users/x5l/ORNL Dropbox/Xiaoman Lu/Oak_Research_Materials/Project3_Urban/Codes_Urban/OLMT/pklfiles/'
Indir = '/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/OLMT/pklfiles/'

infile = Indir + '20260121_SD_ICBELMBC.pkl'
myfile = open(infile, 'rb')
mycase = pickle.load(myfile)
mycase.output






