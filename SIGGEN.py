#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 27 16:28:47 2026

@author: apollo
"""
import numpy as np;
import math as m;
# SIGNAl GENERATOR
class SIGGEN:
    y = []; # signal series
    t = []; # time series
    A = []; # Amplitudes of signal components
    phi = []; # phase angles in rad
    T = None; # Total signal length in seconds
    Fs = None; # Sample Rate in Seconds
    dt = None; # timestep dt
   
    def __init__(self, T, FS, A, Freq, phi):
        self.T = T; # Total Time in Seconds
        self.Fs = FS; # Sample Rate in Sampels/s
        self.dt = 1/self.Fs; # timestep dt
        self.t = np.linspace(0, self.T,num=self.Fs); # time series
        self.A = A; # signal components Amplitudes
        self.Fq = Freq; # signal components Frequencies in Hz
        self.phi = phi; # signal components phase shifts
        self.y = np.zeros(self.Fs*self.T); 
        
    def compute_Signal(self):
        if len(self.A) == len(self.phi) & len(self.A) == len(self.Fq):
            for i in range(len(self.A)):
                for j in range(len(self.t)):
                    self.y[j] = self.y[j] + self.A[i]*m.cos(self.t[j]*(2*m.pi)*self.Fq[i]+self.phi[i]);
                
   