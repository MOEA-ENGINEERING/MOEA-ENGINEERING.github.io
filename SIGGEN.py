#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 27 16:28:47 2026

@author: apollo
"""
import numpy as np;
import math as m;
import matplotlib.pyplot as plt;
from scipy import signal as ss;
# SIGNAl GENERATOR
class SIGGEN:
    # Signal data
    y = []; # signal series
    t = []; # time series
    A = []; # Amplitudes of signal components
    phi = []; # signal phase angles in rad
    T = None; # Total signal length in seconds
    Fs = None; # Sample Rate in Seconds
    dt = None; # timestep dt
    Fq = None; # Signal Comonent Frequencies in Hz
    avgNoise = 0; # Mean Gaussian Noise
    stdNoise = 0; # Standard Deviation Noise

   
    def __init__(self, T, FS, A, Freq, phi):
        self.T = T; # Total Time in Seconds
        self.Fs = FS; # Sample Rate in Sampels/s
        self.dt = 1/self.Fs; # timestep dt in s
        self.t = np.linspace(0, self.T,num=(self.Fs*self.T)); # time series
        self.A = A; # signal components Amplitudes
        self.Fq = Freq; # signal components Frequencies in Hz
        self.phi = phi; # signal components phase shifts
        self.y = np.zeros(self.Fs*self.T); 
        
    def compute_Signal(self):
        if len(self.A) == len(self.phi) & len(self.A) == len(self.Fq):
            for i in range(len(self.A)):
                for j in range(len(self.t)):
                    self.y[j] = self.y[j] + self.A[i]*m.cos(self.t[j]*(2*m.pi)*self.Fq[i]+self.phi[i]);
        
    def compute_Square_Signal(self):
        if len(self.A) == len(self.phi) & len(self.A) == len(self.Fq):
            for i in range(len(self.A)):
                self.y = self.y + self.A[i]*ss.square(2*m.pi*self.Fq[i]*self.t+self.phi[i]);
            
    def compute_Sawtooth_Signal(self):
        if len(self.A) == len(self.phi) & len(self.A) == len(self.Fq):
            for i in range(len(self.A)):
                self.y = self.y + self.A[i]*ss.sawtooth(2*m.pi*self.Fq[i]*self.t+self.phi[i]);
    
    def add_Gaussian_Noise(self, mean, std):
        self.avgNoise = mean;
        self.stdNoise = std;
        self.y = self.y + np.random.normal(self.avgNoise, self.stdNoise, len(self.t));
        
    def add_White_Noise(self, mean, std):
        self.avgNoise = mean;
        self.stdNoise = std;
        self.y = self.y + np.random.uniform(self.avgNoise, self.stdNoise, len(self.t));
        
    def add_Brownian_Noise(self, mean, std):
        self.avgNoise = mean;
        self.stdNoise = std;
        self.y = self.y + np.cumsum(np.random.normal(self.avgNoise, self.stdNoise, len(self.t)));
        
    def  plot_Signal(self,label):
        plt.figure
        plt.plot(self.t, self.y)
        plt.xlabel("Time [s]")
        plt.ylabel("Signal [-]")
        plt.show
        plt.savefig("./OUTPUT/"+label)
    
    def get_Signal(self):
        # Return time and signal series
        return [self.t, self.y] 