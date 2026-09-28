#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 21:32:32 2026

@author: apollo
"""

class MPOINT:
    __rProbe = None; # Radial Traverse Coordinate
    __thProbe = None; # Circumferential Traverse Coordinate
    __rCoord = None; # Radial Rig coordinate
    __thCoord = None; # Circumferential Rig Coordinate
    __rEngine = None; # Radial Engine Coordiante
    __thEngine = None; # Circumferential Engine Coordinate
    
    __nSigChannels = None; # Number of Signal Channels
    __tRawSig = []; # Raw Signal time series
    __yRawSig = []; # Raw Signal Series
    __trRawSig = []; # Raw Trigger Signal
    
    
    def __init__(self):
        