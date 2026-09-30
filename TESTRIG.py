#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 20:49:25 2026

@author: apollo
"""

class TESTRIG(COMPOSITEENTITY[MEASPLANE]):
    __test__ = False  # prevent pytest from collecting this class
    child_type = MeasurementPlane
    __nPlanes = None; # Number of measurement planes
    __nRotors = None; # Number of rotors
    
    
    
    
    def __init__(self):
        