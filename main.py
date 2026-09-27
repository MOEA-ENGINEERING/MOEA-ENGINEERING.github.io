#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 27 16:24:25 2026

@author: apollo
"""
import numpy as np
import math as m;


import SIGGEN;
###############################################################################
#################### SIGNAL  GENERATOR / DATA READ ############################
###############################################################################
sig = SIGGEN.SIGGEN(4, 1000, [3,0.3],[0.5,4],[0,0]); # Initialize Signal
sig.compute_Signal(); # Compute Signal
sig.add_Gaussian_Noise(0, 0.1); # Add Noise
sig.plot_Signal("Signal"); # Show signal

trig = SIGGEN.SIGGEN(4, 1000, [2],[2],[0]); # Initialize Trigger Signal
trig.compute_Square_Signal(); # Compute Trigger Signal
trig.add_White_Noise(0, 0.1); # Add Noise
trig.plot_Signal("Trigger_Signal"); # Show Trigger Signal


###############################################################################
############################# INITIALIZATION ##################################
###############################################################################

# MeasurementPlane -> DataMap -> MP





###############################################################################
############################# DATA PROCESSING #################################
###############################################################################







###############################################################################
############################### DATA OUTPUT ###################################
###############################################################################




print("Hello World!")