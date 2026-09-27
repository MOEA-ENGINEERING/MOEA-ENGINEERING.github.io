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
    __y = []; # signal series
    __t = []; # time series
    __A = []; # Amplitudes of signal components
    __phi = []; # signal phase angles in rad
    __T = None; # Total signal length in seconds
    __Fs = None; # Sample Rate in Seconds
    __dt = None; # timestep dt
    __Fq = None; # Signal Comonent Frequencies in Hz
    __avgNoise = 0; # Mean Gaussian Noise
    __stdNoise = 0; # Standard Deviation Noise

   
    def __init__(self, T, FS, A, Freq, phi):
        self.__T = T; # Total Time in Seconds
        self.__Fs = FS; # Sample Rate in Sampels/s
        self.__dt = 1/self.__Fs; # timestep dt in s
        self.__t = np.linspace(0, self.__T,num=(self.__Fs*self.__T)); # time series
        self.__A = A; # signal components Amplitudes
        self.__Fq = Freq; # signal components Frequencies in Hz
        self.__phi = phi; # signal components phase shifts
        self.__y = np.zeros(self.__Fs*self.__T); 
        
    def compute_Signal(self):
        if len(self.__A) == len(self.__phi) & len(self.__A) == len(self.__Fq):
            for i in range(len(self.__A)):
                for j in range(len(self.__t)):
                    self.__y[j] = self.__y[j] + self.__A[i]*m.cos(self.__t[j]*(2*m.pi)*self.__Fq[i]+self.__phi[i]);
        
    def compute_Square_Signal(self):
        if len(self.__A) == len(self.__phi) & len(self.__A) == len(self.__Fq):
            for i in range(len(self.__A)):
                self.__y = self.__y + self.__A[i]*ss.square(2*m.pi*self.__Fq[i]*self.__t+self.__phi[i]);
            
    def compute_Sawtooth_Signal(self):
        if len(self.__A) == len(self.__phi) & len(self.__A) == len(self.__Fq):
            for i in range(len(self.__A)):
                self.__y = self.__y + self.__A[i]*ss.sawtooth(2*m.pi*self.__Fq[i]*self.__t+self.__phi[i]);
    
    def add_Gaussian_Noise(self, mean, std):
        self.__avgNoise = mean;
        self.__stdNoise = std;
        self.__y = self.__y + np.random.normal(self.__avgNoise, self.__stdNoise, len(self.__t));
        
    def add_White_Noise(self, mean, std):
        self.__avgNoise = mean;
        self.__stdNoise = std;
        self.__y = self.__y + np.random.uniform(self.__avgNoise, self.__stdNoise, len(self.__t));
        
    def add_Brownian_Noise(self, mean, std):
        self.__avgNoise = mean;
        self.__stdNoise = std;
        self.__y = self.__y + np.cumsum(np.random.normal(self.__avgNoise, self.__stdNoise, len(self.__t)));
        
    def  plot_Signal(self,label):
        plt.figure
        plt.plot(self.__t, self.__y)
        plt.xlabel("Time [s]")
        plt.ylabel("Signal [-]")
        plt.show
        plt.savefig("./OUTPUT/"+label)
    
    def get_Signal(self):
        # Return time and signal series
        return [self.__t, self.__y] 