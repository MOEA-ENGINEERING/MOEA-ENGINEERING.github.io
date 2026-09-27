#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 27 16:24:25 2026

@author: apollo
"""
import numpy as np
import math as m;


import SIGGEN;
# SIGNAL  GENERATOR / DATA READ
sig = SIGGEN.SIGGEN(4, 250000, [1,2,1.5],[400,3200,6400],[0,m.pi/2,m.pi/5]);
sig.compute_Signal();



print("Hello World!")