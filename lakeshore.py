# -*- coding: utf-8 -*-
"""
Created on Fri Jun 02 09:08:29 2017
@author: amott
"""
import sys
import os
sys.path.append((os.path.dirname(os.path.realpath(__file__)))) #I think this will work
import json
import time
import pyvisa
import visa
from pyvisa.constants import Parity
from json import dump, load
import datetime
import os.path
import platform
import threading
import datetime
import logging.config
import logging
import csv
from threading import Timer
from apscheduler.schedulers.background import BackgroundScheduler #Timer for logging
import getpass

class lakeshore325:
    def __init__(self, asrl, timeout = 2 * 1000, autodetect = False, baud = 57600):
        self.rm = pyvisa.ResourceManager()
        #auto connects to first lakeshore it finds
        """
        if autodetect:
            for res in self.rm.list_resources():
                self.rm.open_resource(res)
                self.inst.write('*IDN')
                info = self.inst.read()
                if str(info[0]).upper() == 'LSCI':
                    break
                if str(info[0]).upper() != 'LSCI':
                    continue
        else:
            self.inst = self.rm.open_resource(asrl)
        """
        self.inst = self.rm.open_resource(asrl)
        self.inst.data_bits = 7
        self.inst.parity = Parity(1)
        if baud in [9600, 19200, 38400, 57600]:
            self.inst.baud_rate = baud #Can be configured to 9600, 19200, 38400, 57600
        else:
            raise ValueError('Baud rate must be 9600, 19200, 38400, or 57600.')
        self.inst.term_chars = '\n'
        self.values = dict()
        global sched
        sched = BackgroundScheduler()
        
    def close(self):
        self.inst.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        
    def read(self):
        print self.inst.read()
        
    def clear_interface(self):
        """
        Clears the bits in the Status Byte Register and Standard Event Status Register and 
        terminates all pending operations. Clears the interface, but not the controller.
        """
        self.inst.write('*CLS')
        time.sleep(0.05)
        
    def set_ese(self, ese):
        """
        Each bit is assigned a bit weighting and represents the enable/disable mask 
        of the corresponding event flag bit in the Standard Event Status Register.
        """
        self.inst.write('*ESE ' + str(ese))
        time.sleep(0.05)
        return self.get_ese()
        
    def get_ese(self):
        self.values['ese'] = str(self.inst.query('*ESE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ese']
        
    def get_esr(self):
        self.values['esr'] = str(self.inst.query('*ESR?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['esr']

    def get_info(self):
        self.values['idn'] = str(self.inst.query('*IDN?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['idn']

    def get_number(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['number'] = str(out[2])
        return self.values['number']

    def get_model(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['model'] = str(out[1])
        return self.values['model']

    def get_manu(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['manufacturer'] = str(out[0])
        return self.values['manufacturer']

    def set_rst(self):
        """
        Sets controller parameters to power-up settings.
        """
        self.inst.write('*RST')
        time.sleep(0.05)
        return 'Controller set to power-up settings.'
        
    def set_sre(self, sre):
        """
        Each bit has a bit weighting and represents the enable/disable mask of
        the corresponding status flag bit in the Status Byte Register.
        """
        self.inst.write('*SRE ' + str(sre))
        time.sleep(0.05)
        return self.get_sre()
        
    def get_sre(self):
        self.values['sre'] = str(self.inst.query('*SRE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['sre']

    def get_stb(self):
        """
        Acts like a serial poll, but does not reset the register to all zeros. 
        The integer returned represents the sum of the bit weighting of the 
        status flag bits that are set in the Status Byte Register.
        """
        self.values['stb'] = str(self.inst.query('*STB?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['stb']

    def is_error(self):
        self.values['tst'] = str(self.inst.query('*TST?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['tst']

    def set_cmode(self, loop, mode):
        if loop == -1:
            for i in range(1,3):
                self.inst.write('CMODE ' + str(i) + ',' + str(mode))
            return self.get_cmode(-1)
        if (loop in range(1, 3)) and (mode in range(1, 7)):
            self.inst.write('CMODE ' + str(loop) + ',' + str(mode))
            time.sleep(0.05)
            return self.get_cmode(loop)
        else:
            raise ValueError('Incorrect input. Loop must be either -1, 1, 2 and mode must be between 1 and 6.')
            
    def get_cmode(self, loop):
        if loop == -1:
            self.values['both_cmodes'] = list()
            for i in range (1, 3):
                self.values['cmode_' + str(i)] = str(self.inst.query('CMODE? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_cmodes'].append(self.values['cmode_' + str(i)])
            return self.values['both_cmodes']
        if loop in range(1, 3):
            self.values['cmode_loop_' + str(loop)] = str(self.inst.query('CMODE? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['cmode_loop_' + str(loop)]
        else:
            raise ValueError('Inocorrect input. Loop must be either -1, 1, or 2.')

    def get_crdg(self, ab):
        if ab == -1:
            self.values['both_crdgs'] = list()
            for i in ['A','B']:
                self.values['crdg_'+ i.lower()] = str(self.inst.query('CRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_crdgs'].append(self.values['crdg_'+ i.lower()])
            return self.values['both_crdgs']
        if ab.upper() in ['A','B']:
            self.values['crdg_' + ab.lower()] = str(self.inst.query('CRDG? ' + str(ab).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['crdg_' + ab.lower()]
        else:
            raise ValueError('Incorrect input. Input must be A, B, or -1.')
            
    def delete_curve(self, curve):
        if curve == -1:
            for i in range(21, 36):
                self.inst.write('CRVDEL ' + str(i))
            return self.get_curve(-1)
        if curve in range(21, 36):
            self.inst.write('CRVDEL ' + str(curve))
            return self.get_curve(curve)
        else:
            raise ValueError('Incorrect input. Curve must be between 21 and 35 or be -1.')
            
    def get_curve(self, curve):
        if curve == -1:
            self.values['all_curves'] = list()
            for i in range (1, 37):
                self.values['curve_' + str(i)] = str(self.inst.query('CRVHDR? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curves'].append(self.values['curve_' + str(i)])
            return self.values['all_curves']
        if curve in range(1, 37):
            self.values['curve_' + str(curve)] = str(self.inst.query('CRVHDR? ' + str(curve))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_' + str(curve)]
        else:
            raise ValueError('Incorrect input. Curve must be between 1 and 36 or be -1.')
            
    def set_curve_header(self, curve, name, sn, frmt, lim_val, coe):
        """
        Configures the user curve header.
        """
        if (curve in range(21, 36)) and (len(name) in range (1, 16)) and (len(sn) in range(1, 11)) and (frmt in range(1,5)) and (coe in range(1, 3)):
            self.inst.write('CRVHDR ' + str(curve) + ',' + str(name) + ',' + str(sn) + ',' + str(frmt) + ',' + str(lim_val) + ',' + str(coe))
            time.sleep(0.05)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')

    def set_curve_point(self, curve, index, unit, temp):
        """
        Configures a user curve data point.
        """
        if (curve in range(21, 36)) and (index in range(1, 201)) and (len(unit) in range(1, 7)) and (temp in range(1, 7)):
            self.inst.write('CRVPT ' + str(curve) + ',' + str(index) + ',' + str(unit) + ',' + str(temp))
            time.sleep(0.05)
            return self.get_curve_point(curve, index)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_curve_point(self, curve, index):
        if (curve == -1) and (index == -1):
            self.values['all_curve_points'] = list()
            for i in range(1, 36):
                for x in range(1, 201):
                    self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(x))).replace('\r\n','')
                    time.sleep(0.05)
                    self.values['all_curve_points'].append(self.values['curve_point_at_' + str(curve) + '_' + str(index)])
            return self.values['all_curve_points']
        if (curve == -1) and (index in range(1, 201)):
            self.values['all_curve_points_for_index_' + str(index)] = list()
            for i in range(1,36):
                self.values['curve_point_at_' + str(i) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(index))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_for_index_' + str(index)].append(self.values['curve_point_at_' + str(i) + '_' + str(index)])
            return self.values['all_curve_points_for_index_' + str(index)]
        if (curve in range(1, 36)) and (index == -1):
            self.values['all_curve_points_at_curve_' + str(curve)] = list()
            for i in range(1, 201):
                self.values['curve_point_at_' + str(curve) + '_' + str(i)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_at_curve_' + str(curve)].append(self.values['curve_point_at_' + str(curve) + '_' + str(i)])
            return self.values['all_curve_points_at_curve_' + str(curve)]
        if (curve in range(1, 36)) and (index in range(1, 201)):
            self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(index))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_point_at_' + str(curve) + '_' + str(index)]
        else:
            raise ValueError('Incorrect input. Curve must be between 1 and 35 and index must be between 1 and 200.')
            
    def set_control_loop(self, loop, inp, units, power, cp):
        if (loop == -1) and (inp.upper() in ['A','B']) and (units in range(1, 4)) and (power in range(0, 2)) and (cp in range(1, 3)):
            for i in range(1, 3):
                self.inst.write('CSET ' + str(i) + ',' + str(inp).upper() + ',' + str(units) + ',' + str(power) + str(cp))
                time.sleep(0.05)
            return self.get_control_loop(-1)
        if (loop in range(1, 3)) and (inp.upper() in ['A','B']) and (units in range(1, 4)) and (power in range(0, 2)) and (cp in range(1, 3)):
            self.inst.write('CSET ' + str(loop) + ',' + str(inp).upper() + ',' + str(units) + ',' + str(power) + str(cp))
            time.sleep(0.05)
            return self.get_control_loop(loop)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_control_loop(self, loop):
        if loop == -1:
            self.values['both_control_loops'] = list()
            for i in range(1, 3):
                self.values['control_loop_' + str(i)] = str(self.inst.query('CSET? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_control_loops'].append(self.values['control_loop_' + str(i)])
            return self.values['both_control_loops']
        if loop in range(1, 3):
            self.values['control_loop_' + str(loop)] = str(self.inst.query('CSET? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['control_loop_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_default(self):
        """
        Sets all configuration values to factory defaults and resets the instrument.
        """
        self.inst.write('DFTL 99')
        time.sleep(0.05)
        return 'Configuration settings set to default values.'
        
    def set_display_field(self, field, item, source):
        if (field == -1) and (item in range(0, 5)):
             if source in range(1, 3):
                 for i in range (1, 5):
                     self.inst.write('DISPFLD ' + str(i) + ',' + str(item) + ',' + str(source))
                     time.sleep(0.05)
                 return self.get_display_field(-1)
             else:
                for i in range(1, 5):
                    self.inst.write('DISPFLD ' + str(i) + ',' + str(item))
                    time.sleep(0.05)
                return self.get_display_field(-1)
        if (field in range(1, 5)) and (item in range(0, 5)):
            if source in range(1, 3):
                self.inst.write('DISPFLD ' + str(field) + ',' + str(item) + ',' + str(source))
                time.sleep(0.05)
                return self.get_display_field(field)
            else:
                self.inst.write('DISPFLD ' + str(field) + ',' + str(item))
                time.sleep(0.05)
                return self.get_display_field(field)
        else:
            raise ValueError('Incorrect input. Field and item must be between 1 and 4 and source is between 1 and 3 if item is 1 or 2.')
            
    def get_display_field(self, field):
        if field == -1:
            self.values['all_display_fields'] = list()
            for i in range (1, 5):
                self.values['display_field_' + str(i)] = str(self.inst.query('DISPFLD? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_display_fields'].append(self.values['display_field_' + str(i)])
                time.sleep(0.05)
            return self.values['all_display_fields']
        if field in range(1, 5):
            self.values['display_field_' + str(field)] = str(self.inst.query('DISPFLD? ' + str(field))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['display_field_' + str(field)]
        else:
            raise ValueError('Incorrect input. Field must be -1 or between 1 and 4.')
            
    def set_filter(self, inp, io, points, window):
        if (inp == -1) and (io in range(0, 2)) and (points in range(2, 65)) (window in range(1, 11)):
            for i in ['A', 'B']:
                self.inst.write('FILTER ' + i + ',' + str('io') + ',' + str(points) + ',' + str(window))
                time.sleep(0.05)
            return self.get_filter(-1)
        if (inp.upper() in ['A','B']) and (io in range(0, 2)) and (points in range(2, 65)) (window in range(1, 11)):
            self.inst.write('FILTER ' + str(inp).upper() + ',' + str('io') + ',' + str(points) + ',' + str(window))
            time.sleep(0.05)
            return self.get_filter(inp)
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B, io must be 0 or 1, points must be between 2 and 64, and window must be between 1 and 10.')
            
    def get_filter(self, inp):
        if inp == -1:
            self.values['both_filters'] = list()
            for i in ['A','B']:
                self.values['filter_' + i.lower()] = str(self.inst.query('FILTER? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_filters'].append(self.values['filter_' + i.lower()])
            return self.values['both_filters']
        if inp.upper() in ['A','B']:
            self.values['filter_' + inp.lower()] = str(self.inst.query('FILTER? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['filter_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B')
            
    def get_heater_percent(self, loop):
        if loop == -1:
            self.values['both_heater_percents'] = list()
            for i in range(1, 3):
                self.values['heater_percent_' + str(i)] = str(self.inst.query('HTR? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_heater_percents'].append(self.values['heater_percent_' + str(i)])
            return self.values['both_heater_percents']
        if loop in range(1, 3):
            self.values['heater_percent_' + str(loop)] = str(self.inst.query('HTR? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['heater_percent_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be either -1, 1, or 2.')
            
    def set_heater_resistance(self, loop, res):
        if (loop == -1) and (res in range(1, 3)):
            for i in range(1, 3):
                self.inst.write('HTRRES ' + str(i) + ',' + str(res))
                time.sleep(0.05)
            return self.get_heater_resistance(-1)
        if (loop in range(1, 3)) and (res in range(1, 3)):
            self.inst.write('HTRRES ' + str(loop) + ',' + str(res))
            time.sleep(0.05)
            return self.get_heater_resistance(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2 and res must be 1 or 2.')
        
    def get_heater_resistance(self, loop):
        if loop == -1:
            self.values['both_heater_resistances'] = list()
            for i in range(1, 3):
                self.values['heater_' + str(i) + 'resistance'] = str(self.inst.query('HTRRES? 1')).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_heater_resistances'].append(self.values['heater_' + str(i) + 'resistance'])
            return self.values['both_heater_resistances']
        if loop in range(1, 3):
            self.values['heater_' + str(loop) + '_resistance'] = str(self.inst.query('HTRRES? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['heater_' + str(loop) + '_resistance']
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_ieee(self, term, eoi, addr):
        if (term in range(0, 4)) and (eoi in range(0, 2)) and (addr in range(1, 31)):
            self.inst.write('IEEE ' + str(term) + str(eoi) + str(addr))
            time.sleep(0.05)
            return self.get_ieee(term)
        else:
            raise ValueError('Incorrect input. Terminator must be 0, 1, 2, or 3, EOI must be 0 or 1, and address must be between 1 and 30.')
            
    def get_ieee(self):
        self.values['ieee'] = str(self.inst.query('IEEE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ieee']

    def set_curve_num(self, inp, num):
        if (inp == -1) and (num in range(0, 36)):
            for i in ['A', 'B']:
                self.inst.write('INCRV ' + i + ',' + str(num))
                time.sleep(0.05)
            return self.get_curve_num(-1)
        if (inp.upper() in ['A','B']) and (num in range(0, 36)):
            self.inst.write('INCRV ' + str(inp).upper() + ',' + str(num))
            time.sleep(0.05)
            return self.get_curve_num(str(inp).upper())
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B and num must be between 0 and 35.')
            
    def get_curve_num(self, inp):
        if inp == -1:
            self.values['both_curve_numbers'] = list()
            for i in ['A','B']:
                self.values['curve_number_' + i.lower()] = str(self.inst.query('INCRV? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_curve_numbers'].append(self.values['curve_number_' + i.lower()])
            return self.values['both_curve_numbers']
        if inp.upper() in ['A','B']:
            self.values['curve_number_' + inp.lower()] = str(self.inst.query('INCRV? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_number_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B')
            
    def set_intype(self, inp, sen, comp):
        if (inp == -1) and (sen in range(0, 10)) and (comp in range (0, 2)):
            for i in ['A', 'B']:
                self.inst.write('INTYPE ' + i + ',' + str(sen) + ',' + str(comp))
                time.sleep(0.05)
            return self.get_intype()
        if (inp.upper() in ['A','B']) and (sen in range(0, 10)) and (comp in range(0, 2)):
            self.inst.write('INTYPE ' + str(inp) + ',' + str(sen) + ',' + str(comp))
            time.sleep(0.05)
            return self.get_intype(str(inp).upper())
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B, sen must be between 0 and 9, and comp must be 0 or 1.')
            
    def get_intype(self, inp):
        if inp == -1:
            self.values['both_intypes'] = list()
            for i in ['A','B']:
                self.values['instype_' + i.lower()] = str(self.inst.query('INTYPE? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_intypes'].append(self.values['instype_' + i.lower()])
            return self.values['both_intypes']
        if inp.upper() in ['A','B']:
            self.values['intype_' + str(inp).lower()] = str(self.inst.query('INTYPE? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['intype_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B.')
            
    def get_last_key_press(self):
        """
        Returns a number descriptor of the last key pressed since the last KEYST?.
        Returns “21” after initial power-up. Returns “00” if no key pressed since last query.
        """
        self.values['last_key_press'] = str(self.inst.query('KEYST?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['last_key_press']

    def get_temp(self, inp):
        if inp == -1:
            self.values['both_temperatures'] = list()
            for i in ['A','B']:
                self.values['temperature_' + i.lower()] = str(self.inst.query('KRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_temperatures'].append(self.values['temperature_' + i.lower()])
            return self.values['both_temperatures']
        if inp.upper() in ['A','B']:
            self.values['temperature_' + inp.lower()] = str(self.inst.query('KRDG? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['temperature_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B.')
            
    def set_lock(self, state, code):
        if (state in range (0, 2)):
            self.inst.write('LOCK ' + str(state) + ',' + str(code))
            time.sleep(0.05)
            return self.get_lock()
        else:
            raise ValueError('Incorrect input. State must be 0 or 1 and code must be between 000 and 999.')
            
    def get_lock(self):
        self.values['lock'] = str(self.inst.query('LOCK?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['lock']

    def set_mode(self, mode):
        if mode in range(0, 3):
            self.inst.write('MODE ' + str(mode))
            time.sleep(0.05)
            return self.get_mode()
        else:
            raise ValueError('Incorrect input. Input must be 0, 1, or 2.')
            
    def get_mode(self):
        self.values['mode'] = str(self.inst.query('MODE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['mode']

    def set_mout(self, loop, val):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('MOUT ' + str(i) + ',' + str(val))
                time.sleep(0.05)
            return self.get_mout(-1)
        if loop in range(1, 3):
            self.inst.write('MOUT ' + str(loop) + str(val))
            time.sleep(0.05)
            return self.get_mout(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_mout(self, loop):
        if loop == -1:
            self.values['both_mouts'] = list()
            for i in range(1, 3):
                self.values['mout_' + str(i)] = str(self.inst.query('MOUT? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mouts'].append(self.values['mout_' + str(i)])
            return self.values['both_mouts']
        if loop in range(1, 3):
            self.values['mout_' + str(loop)] = str(self.inst.query('MOUT? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mout_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_pid(self, loop, p, i, d):
        """
        Setting resolution is less than 6 digits indicated.
        """
        if (loop == -1) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            for i in range(1, 3):
                self.inst.write('PID ' + str(i) + str(p) + ',' + str(i) + ',' + str(d))
                time.sleep(0.05)
            return self.get_pid(-1)
        if (loop in range(1,3)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            self.inst.write('PID ' + str(loop) + ',' + str(p) + ',' + str(i) + ',' + str(d))
            time.sleep(0.05)
            return self.get_pid(loop)
        else:
            raise ValueError('Incorrect input. Refer to manual for proper parameters.')
            
    def get_pid(self, loop):
        if loop == -1:
            self.values['both_pids'] = list()
            for i in range(1, 3):
                self.values['pid_' + str(i)] = str(self.inst.query('PID? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_pids'].append(self.values['pid_' + str(i)])
            return self.values['both_pids']
        if loop in range(1, 3):
            self.values['pid_' + str(loop)] = str(self.inst.query('PID? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['pid_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_ramp(self, loop, io, rate):
        if (loop == -1) and (io in range(0, 2)) and (rate <= 100 and rate >= 0):
            for i in range(1, 3):
                self.inst.write('RAMP ' + str(i) + ',' + str(io) + ',' + str(rate))
                time.sleep(0.05)
            return self.get_ramp(-1)
        if (loop in range(1, 3)) and (io in range(0, 2)) and (rate <= 100 and rate >= 0):
            self.inst.write('RAMP ' + str(loop) + ',' + str(io) + ',' + str(rate))
            time.sleep(0.05)
            return self.get_ramp(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2, io must be 1 or 2, and rate between 0 and 100.')
            
    def get_ramp(self, loop):
        if loop == -1:
            self.values['both_ramps'] = list()
            for i in range(1, 3):
                self.values['ramp_' + str(i)] = str(self.inst.query('RAMP? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ramps'].append(self.values['ramp_' + str(i)])
            return self.values['both_ramps']
        if loop in range(1, 3):
            self.values['ramp_' + str(loop)] = str(self.inst.query('RAMP? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['ramp_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_rampst(self, loop):
        if loop == -1:
            self.values['both_rampsts'] = list()
            for i in range (1, 3):
                self.values['rampst_' + str(i)] = str(self.inst.query('RAMPST? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_rampsts'].append(self.values['rampst_' + str(i)])
            return self.values['both_rampsts']
        if loop in range (1, 3):
            self.values['rampst_' + str(loop)] = str(self.inst.query('RAMPST? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['rampst_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_range(self, loop, ran):
        if (loop == -1) and (ran in range(0, 2)):
            for i in range(1, 3):
                self.inst.write('RANGE ' + str(i) + ',' + str(ran))
                time.sleep(0.05)
            return self.get_range(-1)
        if (loop == 1) and (ran in range(0, 3)):
            self.inst.write('RANGE 1,' + str(ran))
            time.sleep(0.05)
            return self.get_range(1)
        if (loop == 2) and (ran in range(0, 2)):
            self.inst.write('RANGE 2,' + str(ran))
            time.sleep(0.05)
            return self.get_range(2)
        else:
            raise ValueError('Incorrect input. Range must be 0, 1, or 2 if loop is 1 or range must be 0 or 1 if loop is 2.')
            
    def get_range(self, loop):
        if loop == -1:
            self.values['both_ranges'] = list()
            for i in range (1, 3):
                self.values['range_' + str(i)] = str(self.inst.query('RANGE? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ranges'].append(self.values['range_' + str(i)])
            return self.values['both_ranges']
        if loop in range(1, 3):
            self.values['range_' + str(loop)] = str(self.inst.query('RANGE? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['range_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_input_reading(self, inp):
        if inp == -1:
            self.values['both_input_readings'] = list()
            for i in ['A', 'B']:
                self.values['input_reading_' + i.lower()] = str(self.inst.query('RDGST? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_input_readings'].append(self.values['input_reading_' + i.lower()])
            return self.values['both_input_readings']
        if inp.upper() in ['A', 'B']:
            self.values['input_reading_' + inp.lower()] = str(self.inst.query('RDGST? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['input_reading_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')

    def gen_softcal(self, std, dest, sn, t1, u1, t2, u2, t3, u3):
        if (std in [1, 6, 7]) and (dest in range(21, 36)) and (len(sn) in range(0, 11)):
            self.inst.write('SCAL ' + str(std) + ',' + str(dest) + ',' + str(dest) + ',' + str(sn) + ',' + str(t1) + ',' + str(u1) + ',' + str(t2) + ',' + str(u2) + ',' + str(t3) + ',' + str(u3))
            time.sleep(0.05)
            return 'Set SoftCal curve.'
        else:
            raise ValueError('Incorrect input. std must be 1, 6, or 7, dest must be between 21 and 36, and sn must be of a length of 10 or less.')
            
    def set_setpoint(self, loop, value):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('SETP ' + str(i) + ',' + str(value))
                time.sleep(0.05)
            return self.get_setpoint(-1)
        if loop in range(1, 3):
            self.inst.write('SETP ' + str(loop) + ',' + str(value))
            time.sleep(0.05)
            return self.get_setpoint(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_setpoint(self, loop):
        if loop == -1:
            self.values['both_setpoints'] = list()
            for i in range(1, 3):
                self.values['setpoint_' + str(i)] = str(self.inst.query('SETP? ' + str(i))).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_setpoints'].append(self.values['setpoint_' + str(i)])
            return self.values['both_setpoints']
        if loop in range(1, 3):
            self.values['setpoint_' + str(loop)] = str(self.inst.query('SETP? ' + str(loop))).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['setpoint_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_srdg(self, inp):
        if inp == -1:
            self.values['both_sensor_unit_inputs'] = list()
            for i in ['A','B']:
                self.values['sensor_unit_input_' + i.lower()] = str(self.inst.query('SRDG? ' + i.upper())).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_sensor_unit_inputs'].append(self.values['sensor_unit_input_' + i.lower()])
            return self.values['both_sensor_unit_inputs']
        if inp.upper() in ['A', 'B']:
            self.values['sensor_unit_input_' + inp.lower()] = str(self.inst.query('SRDG? ' + inp.upper())).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['sensor_unit_input_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def get_thermocouple(self):
        self.values['thermocouple_junction_temperature'] = str(self.inst.query('TEMP?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['thermocouple_junction_temperature']

    def set_tlimit(self, inp, lim):
        if inp == -1:
            for i in ['A', 'B']:
                self.inst.write('TLIMIT ' + i + ',' + str(lim))
                time.sleep(0.05)
            return self.get_tlimit(-1)
        if inp.upper() in ['A', 'B']:
            self.inst.write('TLIMIT ' + inp.upper() + ',' + str(lim))
            time.sleep(0.05)
            return self.get_tlimit(inp)
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def get_tlimit(self, inp):
        if inp == -1:
            self.values['both_temperature_limits'] = list()
            for i in ['A', 'B']:
                self.values['temperature_limit_' + i.lower()] = str(self.inst.query('TLIMIT? ' + i)).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_temperature_limits'].append(self.values['temperature_limit_' + i.lower()])
            return self.values['both_temperature_limits']
        if inp.upper() == 'A' or 'B':
            self.values['temperature_limit_' + inp.lower()] = str(self.inst.query('TLIMIT? ' + inp.upper())).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['temperature_limit_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def is_tuning(self):
        self.values['tune_test'] = str(self.inst.query('TUNEST?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['tune_test']

    def set_zone(self, loop, zone, setp, p, i, d, mout, ran):
        if (loop == -1) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0):
            for i in range(1, 3):
                self.inst.write('ZONE ' + str(i) + ',' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1')
                time.sleep(0.05)
            return self.get_zone(-1)
        if (loop == 1) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0):
            if ran in range(0, 3):
                self.inst.write('ZONE 1,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + str(ran))
            time.sleep(0.05)
            return self.get_zone(1)
        if (loop == 2) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0):
            self.inst.write('ZONE 2,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1')
            time.sleep(0.05)
            return self.get_zone(2)
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_zone(self, loop, zone):
        if (loop == -1) and (zone == -1):
            self.values['both_control_loops_all_zones'] = list()
            for i in range(1, 3):
                for x in range(1, 11):
                    self.values['control_loop_' + str(i) + '_zone_' + str(x)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(x))).replace('\r\n', '')
                    time.sleep(0.05)
                    self.values['both_control_loops_all_zones'].append(self.values['control_loop_' + str(i) + '_zone_' + str(x)])
            return self.values['both_control_loops_all_zones']
        if (loop == -1) and (zone in range(1, 11)):
            self.values['both_control_loops_zone_' + str(zone)] = list()
            for i in range (1, 3):
                self.values['control_loop_' + str(i) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(zone))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_control_loops_zone_' + str(zone)].append(self.values['control_loop_' + str(i) + '_zone_' + str(zone)])
            return self.values['both_control_loops_zone_' + str(zone)]
            self.values['control_loop_1_zone_' + str(zone)] = self.inst.query('ZONE? 1,' + str(zone))
            time.sleep(0.05)
            self.values['control_loop_1_zone_' + str(zone)] = self.inst.query('ZONE? 1,' + str(zone))
            time.sleep(0.05)
            self.values['both_control_loops_zone_' + str(zone)] = self.values['control_loop_a_zone_' + str(zone)]
            return self.values['both_control_loops_zone_' + str(zone)]
        if (loop in range(1, 3)) and (zone in range(1,11)):
            self.values['control_loop_' + str(loop) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(loop) + ',' + str(zone))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['control_loop_' + str(loop) + '_zone_' + str(zone)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2 and zone between 1 and 10.')
            
    def start_logging_csv(self, interval = 5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_csv, 'interval', seconds = interval)
        sched.start()
        
    def lakeshore_logging_csv(self, path=None, filename=None, units = 'K'):
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.csv'
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        number = self.get_number()
        out = self.get_temp(-1)
        time.sleep(0.05)
        ctime = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        ctime.replace(',','').replace(' ','')
        out[0] = str(out[0])
        out[1] = str(out[1])
        out.append(str(self.get_heater_percent(1)))
        time.sleep(0.05)
        out.append(str(self.get_heater_percent(2)))
        time.sleep(0.05)
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, ctime)
        out.insert(0, date)
        setpoint = str(self.get_setpoint(-1)).replace(',','|')
        time.sleep(0.05)
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        header = 'date,time, seconds, hours, Channel A, \'A\' units, setpoints, Lakeshore Number, Channel B, \'B\' units, heater percent 1, heater percent 2,\n'
        with open(os.path.join(path,filename), 'a') as f: #creates .csv file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .csv file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write(header) #if .csv file is empty, header is written in
                f.close()
        out = str(out).replace('[', '').replace(']', '').replace('\'','')
        with open(os.path.join(path,filename), 'a') as f:
            f.write(str(out)) #Writes lakeshore information to .csv file
            f.write('\n')
            f.close()
                
    def start_logging_txt(self, interval = 5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_txt, 'interval', seconds=interval)
        sched.start()
                
    def lakeshore_logging_txt(self, path=None,filename=None, units = 'K'): #Check against 335
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.txt'
        number = self.get_number()
        header = 'date\t\t time\t\t seconds\t hours\t\t Channel A\t \'A\' units\t setpoints\t\t Lakeshore Number\t Channel B\t \'B\' units\t heater percent 1\t heater percent 2\n'
        out = self.get_temp(-1)
        ctime = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        ctime.replace(',','').replace(' ','')
        out.append(self.get_heater_percent(1))
        out.append(self.get_heater_percent(2))
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, ctime)
        out.insert(0, date)
        setpoint = self.get_setpoint(-1)
        setpoint[0] = float(setpoint[0].replace('+',''))
        setpoint[1] = float(setpoint[1].replace('+',''))
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        
        try:
            out[4] = '%.3f' % float((str(out[4])).replace('+',''))
        except (IndexError):
            out[4] = 0.000
        try:
            out[8] = '%.3f' % float((str(out[8])).replace('+',''))
        except(IndexError):
            out[8] = 0.000
        try:
            out[10] = '%.3f' % float((str(out[10])).replace('+',''))
        except(IndexError):
            out[10] = 0.000
        try:
            out[11] = '%.3f' % float((str(out[11])).replace('+',''))
        except(IndexError):
            out[11] = 0.000

        # Aligns columns
        out[2] = str(out[2]) + '         '
        out[4] = str(out[4]) + '        '
        out[6] = '        ' + str(out[6]) + '        '
        out[8] = '        ' + str(out[8]) + '        '
        out[9] = str(out[9]) + '        '
        out[10] = str(out[10]) + '    '
        out[11] = '        ' + str(out[11])

        with open(os.path.join(path,filename), 'a') as f: #creates .txt file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .txt file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write('{:<20}'.format(header)) #if .txt file is empty, header is written in
                f.close()
        with open(os.path.join(path,filename), 'a') as f:
            out = str(out).replace('[','').replace(']','').replace('\'','').replace(',','\t')+'\n'
            f.write('{:^30}'.format(out))
            f.close()
        
    def pause_logging(self):
        sched.pause()
        return 'Logging paused'
        
    def resume_logging(self):
        sched.resume()
        return 'Logging resumed'
        
    def stop_logging(self):
        sched.shutdown()
        return 'Logging stopped'
        
class lakeshore331:
    def __init__(self, asrl, timeout = 2 * 1000, autodetect = False, baud = 9600):
        self.rm = pyvisa.ResourceManager()
        #auto connects to first lakeshore it finds
        """
        if autodetect:
            for res in self.rm.list_resources():
                self.rm.open_resource(res)
                self.inst.write('*IDN')
                info = self.inst.read()
                if str(info[0]).upper() == 'LSCI':
                    break
                if str(info[0]).upper() != 'LSCI':
                    continue
        else:
            self.inst = self.rm.open_resource(asrl)
        """
        self.inst = self.rm.open_resource(asrl)
        self.inst.data_bits = 7
        self.inst.parity = Parity(1)
        if baud in [300, 1200, 9600]:
            self.inst.baud_rate = baud #Can be configured to 300, 1200, or 9600
        else:
            raise ValueError('Baud rate must be 300, 1200, or 9600.')
        self.inst.term_chars = '\n'
        self.values = dict()
        global sched
        sched = BackgroundScheduler()
        
    def close(self):
        self.inst.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        
    def read(self):
        print self.inst.read()
        
    def clear_interface(self):
        """
        Clears the bits in the Status Byte Register and Standard Event Status Register and 
        terminates all pending operations. Clears the interface, but not the controller.
        """
        self.inst.write('*CLS')
        time.sleep(0.05)
        
    def set_ese(self, ese):
        """
        Each bit is assigned a bit weighting and represents the enable/disable mask 
        of the corresponding event flag bit in the Standard Event Status Register.
        """
        self.inst.write('*ESE ' + str(ese))
        time.sleep(0.05)
        return self.get_ese()
        
    def get_ese(self):
        self.values['ese'] = str(self.inst.query('*ESE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ese']
        
    def get_esr(self):
        self.values['esr'] = str(self.inst.query('*ESR?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['esr']

    def get_info(self):
        self.values['idn'] = str(self.inst.query('*IDN?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['idn']

    def get_number(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['number'] = str(out[2])
        return self.values['number']

    def get_model(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['model'] = str(out[1])
        return self.values['model']

    def get_manu(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['manu'] = str(out[0])
        return self.values['manu']

    def set_rst(self):
        """
        Sets controller parameters to power-up settings.
        """
        self.inst.write('*RST')
        time.sleep(0.05)
        return 'Controller set to power-up settings.'
        
    def set_sre(self, sre):
        """
        Each bit has a bit weighting and represents the enable/disable mask of
        the corresponding status flag bit in the Status Byte Register.
        """
        self.inst.write('*SRE ' + str(sre))
        time.sleep(0.05)
        return self.get_sre()
        
    def get_sre(self):
        self.values['sre'] = str(self.inst.query('*SRE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['sre']

    def get_stb(self):
        """
        Acts like a serial poll, but does not reset the register to all zeros. 
        The integer returned represents the sum of the bit weighting of the 
        status flag bits that are set in the Status Byte Register.
        """
        self.values['stb'] = str(self.inst.query('*STB?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['stb']

    def is_error(self):
        self.values['tst'] = str(self.inst.query('*TST?')).replace('\r\n','').replace('\t','')
        if self.values['tst'] is '':
            self.values['tst'] = 0
        time.sleep(0.05)
        return self.values['tst']

    def set_alarm(self, inp, offon, source, hi, lo, db, le):
        if (inp == -1) and (offon in range(0, 2)) and (source in range(1, 5)) and (le in range(0, 2)):
            for i in ['A', 'B']:
                self.inst.write('ALARM ' + i + ',' + str(offon) + ',' + str(source) + ',' + str(hi) + ',' + str(lo) + ',' + str(db) + ',' + str(le) + ',')
                time.sleep(0.05)
            return self.get_alarm(-1)
        if (inp.upper() in ['A', 'B']) and (offon in range(0, 2)) and (source in range(1, 5)) and (le in range(0, 2)):
            self.inst.write('ALARM ' + inp.upper() + ',' + str(offon) + ',' + str(source) + ',' + str(hi) + ',' + str(lo) + ',' + str(db) + ',' + str(le) + ',')
            time.sleep(0.05)
            return self.get_alarm(inp)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_alarm(self, inp):
        if inp == -1:
            self.values['both_alarms'] = list()
            for i in ['A', 'B']:
                self.values['alarm_' + i.lower()] = str(self.inst.query('ALARM? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_alarms'].append(self.values['alarm_' + i.lower()])
            return self.values['both_alarms']
        if inp.upper() in ['A', 'B']:
            self.values['alarm_' + inp.lower()] = str(self.inst.query('ALARM? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['alarm_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def get_alarmst(self, inp):
        if inp == -1:
            self.values['both_alarm_statuses'] = list()
            for i in ['A', 'B']:
                self.values['alarm_status_' + i.lower()] = str(self.inst.query('ALARMST? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_alarm_statuses'].append(self.values['alarm_status_' + i.lower()])
            return self.values['both_alarm_statuses']
        if inp.upper() in ['A', 'B']:
            self.values['alarm_status_' + inp.lower()] = str(self.inst.query('ALARMST? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['alarm_status_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def reset_alarmst(self):
        self.inst.write('ALARMST')
        time.sleep(0.05)
        return 'High and low status alarms cleared.'
        
    def set_analog(self, bi, mode, source, hi, lo, man, inp = None):
        if (bi in range(0, 2)) and (mode in range(0, 4)) and (source in range(1, 5)):
            if mode == 1:
                self.inst.write('ANALOG ' + str(bi) + ',' + str(mode) + ',' + str(inp) + ',' + str(source) + ',' + str(hi) + ',' + str(lo) + ',' + str(man))
                time.sleep(0.05)
                return self.get_analog()
            if mode != 1:
                self.inst.write('ANALOG ' + str(bi) + ',' + str(mode) + ',' + str(source) + ',' + str(hi) + ',' + str(lo) + ',' + str(man))
                time.sleep(0.05)
                return self.get_analog()
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_analog(self):
        self.values['analog'] = str(self.inst.query('ANALOG?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['analog']

    def get_aout(self):
        self.values['aout'] = str(self.inst.query('AOUT?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['aout']

    def set_baud(self, baud):
        if baud in range(0, 3):
            self.inst.write('BAUD ' + str(baud))
            time.sleep(0.05)
            return self.get_baud()
        else:
            raise ValueError('Incorrect input. Input must be be 0, 1, or 2.')
            
    def get_baud(self):
        self.values['baud'] = str(self.inst.query('BAUD?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['baud']

    def set_beep(self, beep):
        if beep in range(0, 2):
            self.inst.write('BEEP ' + str(beep))
            time.sleep(0.05)
            return self.get_beep()
        else:
            raise ValueError('Incorrect input. Beep must be 0 or 2.')
            
    def get_beep(self):
        self.values['beep'] = str(self.inst.query('BEEP?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['beep']

    def set_brightness(self, brit):
        if brit in range(0, 4):
            self.inst.write('BRIGT ' + str(brit))
            time.sleep(0.05)
            return self.get_brightness()
        else:
            raise ValueError('Incorrect input. Brit must be 0, 1, 2, or 3.')
            
    def get_brightness(self):
        self.values['brightness'] = str(self.inst.query('BRIGT?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['brightness']

    def set_cmode(self, loop, mode):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('CMODE ' + str(loop) + ',' + str(mode))
                time.sleep(0.05)
            return self.get_cmode(-1)
        if (loop in range(1, 3)) and (mode in range(1, 7)):
            self.inst.write('CMODE ' + str(loop) + ',' + str(mode))
            time.sleep(0.05)
            return self.get_cmode(loop)
        else:
            raise ValueError('Incorrect input. Loop must be either -1, 1, 2 and mode must be between 1 and 6.')
            
    def get_cmode(self, loop):
        if loop == -1:
            self.values['both_cmodes'] = list()
            for i in range (1, 3):
                self.values['cmode_' + str(i)] = str(self.inst.query('CMODE? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_cmodes'].append(self.values['cmode_' + str(i)])
            return self.values['both_cmodes']
        if loop in range(1, 3):
            self.values['cmode_loop_' + str(loop)] = str(self.inst.query('CMODE? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['cmode_loop_' + str(loop)]
        else:
            raise ValueError('Inocorrect input. Loop must be either -1, 1, or 2.')

    def get_crdg(self, ab):
        if ab == -1:
            self.values['both_crdgs'] = list()
            for i in ['A','B']:
                self.values['crdg_'+ i.lower()] = str(self.inst.query('CRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_crdgs'].append(self.values['crdg_'+ i.lower()])
            return self.values['both_crdgs']
        if ab.upper() in ['A','B']:
            self.values['crdg_' + ab.lower()] = str(self.inst.query('CRDG? ' + str(ab).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['crdg_' + ab.lower()]
        else:
            raise ValueError('Incorrect input. Input must be A, B, or -1.')
            
    def delete_curve(self, curve):
        if curve == -1:
            for i in range(21, 42):
                self.inst.write('CRVDEL ' + str(i))
                time.sleep(0.05)
            return self.get_curve(-1)
        if curve in range(21, 42):
            self.inst.write('CRVDEL ' + str(curve))
            time.sleep(0.05)
            return self.get_curve(curve)
        else:
            raise ValueError('Incorrect input. Curve must be between 21 and 41 be -1.')
            
    def get_curve(self, curve):
        if curve == -1:
            self.values['all_curves'] = list()
            for i in range (1, 42):
                self.values['curve_' + str(i)] = str(self.inst.query('CRVHDR? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curves'].append(self.values['curve_' + str(i)])
            return self.values['all_curves']
        if curve in range(1, 42):
            self.values['curve_' + str(curve)] = str(self.inst.query('CRVHDR? ' + str(curve))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_' + str(curve)]
        else:
            raise ValueError('Incorrect input. Curve must be between 1 and 41 or be -1.')
            
    def set_curve_header(self, curve, name, sn, frmt, lim_val, coe):
        """
        Configures the user curve header.
        """
        if (curve in range(21, 42)) and (len(name) in range (1, 16)) and (len(sn) in range(1, 11)) and (frmt in range(1,5)) and (coe in range(1, 3)):
            self.inst.write('CRVHDR ' + str(curve) + ',' + str(name) + ',' + str(sn) + ',' + str(frmt) + ',' + str(lim_val) + ',' + str(coe))
            time.sleep(0.05)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')

    def set_curve_point(self, curve, index, unit, temp):
        """
        Configures a user curve data point.
        """
        if (curve in range(21, 42)) and (index in range(1, 201)) and (len(unit) in range(1, 7)) and (temp in range(1, 7)):
            self.inst.write('CRVPT ' + str(curve) + ',' + str(index) + ',' + str(unit) + ',' + str(temp))
            time.sleep(0.05)
            return self.get_curve_point(curve, index)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_curve_point(self, curve, index):
        if (curve == -1) and (index == -1):
            self.values['all_curve_points'] = list()
            for i in range(1, 42):
                for x in range(1, 201):
                    self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(x))).replace('\r\n','')
                    time.sleep(0.05)
                    self.values['all_curve_points'].append(self.values['curve_point_at_' + str(curve) + '_' + str(index)])
            return self.values['all_curve_points']
        if (curve == -1) and (index in range(1, 201)):
            self.values['all_curve_points_for_index_' + str(index)] = list()
            for i in range(1,42):
                self.values['curve_point_at_' + str(i) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(index))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_for_index_' + str(index)].append(self.values['curve_point_at_' + str(i) + '_' + str(index)])
            return self.values['all_curve_points_for_index_' + str(index)]
        if (curve in range(1, 42)) and (index == -1):
            self.values['all_curve_points_at_curve_' + str(curve)] = list()
            for i in range(1, 201):
                self.values['curve_point_at_' + str(curve) + '_' + str(i)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_at_curve_' + str(curve)].append(self.values['curve_point_at_' + str(curve) + '_' + str(i)])
            return self.values['all_curve_points_at_curve_' + str(curve)]
        if (curve in range(1, 42)) and (index in range(1, 201)):
            self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(index))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_point_at_' + str(curve) + '_' + str(index)]
        else:
            raise ValueError('Incorrect input. Curve must be between 21 and 41 and index must be between 1 and 200.')
            
    def set_control_loop(self, loop, inp, units, power, cp):
        if (loop == -1) and (inp.upper() in ['A','B']) and (units in range(1, 4)) and (power in range(0, 2)) and (cp in range(1, 3)):
            for i in range(1, 3):
                self.inst.write('CSET ' + str(i) + ',' + str(inp).upper() + ',' + str(units) + ',' + str(power) + str(cp))
                time.sleep(0.05)
            return self.get_control_loop(-1)
        if (loop in range(1, 3)) and (inp.upper() in ['A','B']) and (units in range(1, 4)) and (power in range(0, 2)) and (cp in range(1, 3)):
            self.inst.write('CSET ' + str(loop) + ',' + str(inp).upper() + ',' + str(units) + ',' + str(power) + str(cp))
            time.sleep(0.05)
            return self.get_control_loop(loop)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_control_loop(self, loop):
        if loop == -1:
            self.values['both_control_loops'] = list()
            for i in range(1, 3):
                self.values['control_loop_' + str(i)] = str(self.inst.query('CSET? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_control_loops'].append(self.values['control_loop_' + str(i)])
            return self.values['both_control_loops']
        if loop in range(1, 3):
            self.values['control_loop_' + str(loop)] = str(self.inst.query('CSET? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['control_loop_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_default(self):
        """
        Sets all configuration values to factory defaults and resets the instrument.
        """
        self.inst.write('DFTL 99')
        time.sleep(0.05)
        return 'Configuration settings set to default values.'
        
    def set_display_field(self, field, item, source=None):
        if (field == -1) and (item in range(0, 5)):
             if (item in range(1, 3)) and (source in range(1, 7)):
                 for i in range (1, 5):
                     self.inst.write('DISPFLD ' + str(i) + ',' + str(item) + ',' + str(source))
                     time.sleep(0.05)
                 return self.get_display_field(-1)
             else:
                for i in range(1, 5):
                    self.inst.write('DISPFLD ' + str(i) + ',' + str(item))
                    time.sleep(0.05)
                return self.get_display_field(-1)
        if (field in range(1, 5)) and (item in range(0, 5)):
            if (item in range(1, 3)) and (source in range(1, 7)):
                self.inst.write('DISPFLD ' + str(field) + ',' + str(item) + ',' + str(source))
                time.sleep(0.05)
                return self.get_display_field(field)
            else:
                self.inst.write('DISPFLD ' + str(field) + ',' + str(item))
                time.sleep(0.05)
                return self.get_display_field(field)
        else:
            raise ValueError('Incorrect input. Field and item must be between 1 and 4 and source is between 1 and 3 if item is 1 or 2.')
            
    def get_display_field(self, field):
        if field == -1:
            self.values['all_display_fields'] = list()
            for i in range (1, 5):
                self.values['display_field_' + str(i)] = str(self.inst.query('DISPFLD? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_display_fields'].append(self.values['display_field_' + str(i)])
            return self.values['all_display_fields']
        if field in range(1, 5):
            self.values['display_field_' + str(field)] = str(self.inst.query('DISPFLD? ' + str(field))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['display_field_' + str(field)]
        else:
            raise ValueError('Incorrect input. Field must be -1 or between 1 and 4.')

    def set_emul(self, offon):
        if offon in range(0, 2):
            self.inst.write('EMUL ' + str(offon))
            return self.get_emul()
        else:
            raise ValueError('Incorrect input. Input must be either 0 or 1.')
            
    def get_emul(self):
        self.values['emul'] = str(self.inst.query('EMUL?')).replace('\r\n','')
        return self.values['emul']

    def set_filter(self, inp, io, points, window):
        if (inp == -1) and (io in range(0, 2)) and (points in range(2, 65)) (window in range(1, 11)):
            for i in ['A', 'B']:
                self.inst.write('FILTER ' + i + ',' + str(io) + ',' + str(points) + ',' + str(window))
                time.sleep(0.05)
            return self.get_filter(-1)
        if (inp.upper() in ['A','B']) and (io in range(0, 2)) and (points in range(2, 65)) (window in range(1, 11)):
            self.inst.write('FILTER ' + str(inp).upper() + ',' + str('io') + ',' + str(points) + ',' + str(window))
            time.sleep(0.05)
            return self.get_filter(inp)
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B, io must be 0 or 1, points must be between 2 and 64, and window must be between 1 and 10.')
            
    def get_filter(self, inp):
        if inp == -1:
            self.values['both_filters'] = list()
            for i in ['A','B']:
                self.values['filter_' + i.lower()] = str(self.inst.query('FILTER? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_filters'].append(self.values['filter_' + i.lower()])
            return self.values['both_filters']
        if inp.upper() in ['A','B']:
            self.values['filter_' + inp.lower()] = str(self.inst.query('FILTER? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['filter_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B')
            
    def get_heater_percent(self):
        self.values['heater_1_percent'] = str(self.inst.query('HTR?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['heater_1_percent']

    def get_heater_status(self):
        self.values['heater_status'] = str(self.inst.query('HTRST?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['heater_status']

    def set_ieee(self, term, eoi, addr):
        if (term in range(0, 4)) and (eoi in range(0, 2)) and (addr in range(1, 31)):
            self.inst.write('IEEE ' + str(term) + str(eoi) + str(addr))
            time.sleep(0.05)
            return self.get_ieee(term)
        else:
            raise ValueError('Incorrect input. Terminator must be between 0 and 3, EOI must be 0 or 1, and address must be between 1 and 30.')
            
    def get_ieee(self):
        self.values['ieee'] = str(self.inst.query('IEEE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ieee']

    def set_curve_num(self, inp, num):
        if (inp == -1) and (num in range(0, 42)):
            for i in ['A', 'B']:
                self.inst.write('INCRV ' + i + ',' + str(num))
                time.sleep(0.05)
            return self.get_curve_num(-1)
        if (inp.upper() in ['A','B']) and (num in range(0, 42)):
            self.inst.write('INCRV ' + str(inp).upper() + ',' + str(num))
            time.sleep(0.05)
            return self.get_curve_num(str(inp).upper())
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B and num must be between 0 and 41.')
            
    def get_curve_num(self, inp):
        if inp == -1:
            self.values['both_curve_numbers'] = list()
            for i in ['A','B']:
                self.values['curve_number_' + i.lower()] = str(self.inst.query('INCRV? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_curve_numbers'].append(self.values['curve_number_' + i.lower()])
            return self.values['both_curve_numbers']
        if inp.upper() in ['A','B']:
            self.values['curve_number_' + inp.lower()] = str(self.inst.query('INCRV? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_number_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B')
            
    def set_intype(self, inp, sen, comp):
        if (inp == -1) and (sen in range(0, 10)) and (comp in range (0, 2)):
            for i in ['A', 'B']:
                self.inst.write('INTYPE ' + i + ',' + str(sen) + ',' + str(comp))
                time.sleep(0.05)
            return self.get_intype()
        if (inp.upper() in ['A','B']) and (sen in range(0, 10)) and (comp in range(0, 2)):
            self.inst.write('INTYPE ' + str(inp) + ',' + str(sen) + ',' + str(comp))
            time.sleep(0.05)
            return self.get_intype(str(inp).upper())
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B, sen must be between 0 and 9, and comp must be 0 or 1.')
            
    def get_intype(self, inp):
        if inp == -1:
            self.values['both_intypes'] = list()
            for i in ['A','B']:
                self.values['instype_' + i.lower()] = str(self.inst.query('INTYPE? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_intypes'].append(self.values['instype_' + i.lower()])
            return self.values['both_intypes']
        if inp.upper() in ['A','B']:
            self.values['intype_' + str(inp).lower()] = str(self.inst.query('INTYPE? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['intype_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B.')
            
    def get_last_key_press(self):
        """
        Returns a number descriptor of the last key pressed since the last KEYST?.
        Returns “21” after initial power-up. Returns “00” if no key pressed since last query.
        """
        self.values['last_key_press'] = str(self.inst.query('KEYST?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['last_key_press']

    def get_temp(self, inp):
        if inp == -1:
            self.values['both_temperatures'] = list()
            for i in ['A','B']:
                self.values['temperature_' + i.lower()] = str(self.inst.query('KRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_temperatures'].append(self.values['temperature_' + i.lower()])
            return self.values['both_temperatures']
        if inp.upper() in ['A','B']:
            self.values['temperature_' + inp.lower()] = str(self.inst.query('KRDG? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['temperature_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B.')
            
    def get_ldat(self, inp):
        if inp == -1:
            self.values['both_linear_equations'] = list()
            for i in ['A', 'B']:
                self.values['linear_equation_' + i.lower()] = str(self.inst.query('LDAT? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_linear_equations'].append(self.values['linear_equation_' + i.lower()])
            return self.values['both_linear_equations']
        if inp.upper() in ['A', 'B']:
            self.values['linear_equation_' + inp.lower()] = str(self.inst.query('LDAT? ' + inp.upper())).replace('\r\n','')
            return self.values['linear_equation_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def set_linear(self, inp, eq, m, x, b, bv=None):
        if (inp == -1) and (eq in range(1, 3)) and (x in range(1, 4)) and (b in range(1, 6)):
            if b == 1:
                for i in ['A', 'B']:
                    self.inst.write('LINEAR ' + i + ',' + str(eq) + ',' + str(m) + ',' + str(x) + ',' + str(b) + ',' + str(bv))
                    time.sleep(0.05)
                return self.get_linear(-1)
            if b != 1:
                for i in ['A', 'B']:
                    self.inst.write('LINEAR ' + i + ','+ str(eq) + ',' + str(m) + ',' + str(x) + ',' + str(b))
                    time.sleep(0.05)
                return self.get_linear(-1)
        if (inp in ['A','B']) and (eq in range(1, 3)) and (x in range(1, 4)) and (b in range(1, 6)):
            if b == 1:
                self.inst.write('LINEAR ' + str(inp) + ',' + str(eq) + ',' + str(m) + ',' + str(x) + ',' + str(b) + ',' + str(bv))
                time.sleep(0.05)
            if b != 1:
                self.inst.write('LINEAR ' + str(inp) + ',' + str(eq) + ',' + str(m) + ',' + str(x) + ',' + str(b))
                time.sleep(0.05)
            return self.get_linear(inp)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_linear(self, inp):
        if inp == -1:
            self.values['both_linears'] = list()
            for i in ['A', 'B']:
                self.values['linear_' + i.lower()] = str(self.inst.query('LINEAR ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_linears'].append(self.values['linear_' + i.lower()])
            return self.values['both_linears']
        if inp.upper() in ['A', 'B']:
            self.values['linear_' + inp.lower()] = str(self.inst.query('LINEAR ' + inp.upper())).replace('\r\n','')
            return self.values['linear_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def set_lock(self, state, code):
        if (state in range (0, 2)) and (code in range(0, 1000)):
            self.inst.write('LOCK ' + str(state) + ',' + str(code))
            time.sleep(0.05)
            return self.get_lock()
        else:
            raise ValueError('Incorrect input. State must be 0 or 1 and code must be between 000 and 999.')
            
    def get_lock(self):
        self.values['lock'] = str(self.inst.query('LOCK?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['lock']

    def get_mdat(self, inp):
        if inp == -1:
            self.values['both_mdats'] = list()
            for i in ['A', 'B']:
                self.values['mdat_' + i.lower()] = str(self.inst.query('MDAT? ' + i.upper())).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mdats'].append(self.values['mdat_' + i.lower()])
            return self.values['both_mdats']
        if inp.upper() in ['A', 'B']:
            self.values['mdat_' + inp.lower()] = str(self.inst.query('MDAT? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mdat_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B.')
            
    def set_mnmx(self, inp, source):
        if (inp == -1) and (source in range(1, 5)):
            for i in ['A', 'B']:
                self.inst.write('MNMX ' + i + ',' + str(source))
                time.sleep(0.05)
            return self.get_mnmx(-1)
        if inp.upper() in ['A', 'B']:
            self.inst.write('MNMX ' + inp.upper() + ',' + str(source))
            time.sleep(0.05)
            return self.get_mnmx(inp)
        else:
            raise ValueError('Incorrect value. Inp must be -1, A, or B and source must be between 1 and 4.')
            
    def get_mnmx(self, inp):
        if inp == -1:
            self.values['both_mnmxs'] = list()
            for i in ['A', 'B']:
                self.values['mnmx_' + i.lower()] = str(self.inst.query('MNMX? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mnmxs'].append(self.values['mnmx_' + i.lower()])
            return self.values['both_mnmxs']
        if inp.upper() in ['A', 'B']:
            self.values['mnmx_' + inp.lower()] = str(self.inst.query('MNMX? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mnmx_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def reset_mnmx(self):
        self.inst.write('MNMXRST')
        time.sleep(0.05)
        return 'Minimum and maximum function reset.'
        
    def set_mode(self, mode):
        if mode in range(0, 3):
            self.inst.write('MODE ' + str(mode))
            time.sleep(0.05)
            return self.get_mode()
        else:
            raise ValueError('Incorrect input. Input must be 0, 1, or 2.')
            
    def get_mode(self):
        self.values['mode'] = str(self.inst.query('MODE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['mode']

    def set_mout(self, loop, val):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('MOUT ' + str(i) + ',' + str(val))
                time.sleep(0.05)
            return self.get_mout(-1)
        if loop in range(1, 3):
            self.inst.write('MOUT ' + str(loop) + str(val))
            time.sleep(0.05)
            return self.get_mout(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_mout(self, loop):
        if loop == -1:
            self.values['both_mouts'] = list()
            for i in range(1, 3):
                self.values['mout_' + str(i)] = str(self.inst.query('MOUT? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mouts'].append(self.values['mout_' + str(i)])
            return self.values['both_mouts']
        if loop in range(1, 3):
            self.values['mout_' + str(loop)] = str(self.inst.query('MOUT? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mout_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_pid(self, loop, p, i, d):
        """
        Setting resolution is less than 6 digits indicated.
        """
        if (loop == -1) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            for i in range(1, 3):
                self.inst.write('PID ' + str(i) + ',' + str(p) + ',' + str(i) + ',' + str(d))
                time.sleep(0.05)
            return self.get_pid(-1)
        if (loop in range(1,3)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            self.inst.write('PID ' + str(loop) + ',' + str(p) + ',' + str(i) + ',' + str(d))
            time.sleep(0.05)
            return self.get_pid(loop)
        else:
            raise ValueError('Incorrect input. Refer to manual for proper parameters.')
            
    def get_pid(self, loop):
        if loop == -1:
            self.values['both_pids'] = list()
            for i in range(1, 3):
                self.values['pid_' + str(i)] = str(self.inst.query('PID? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_pids'].append(self.values['pid_' + str(i)])
            return self.values['both_pids']
        if loop in range(1, 3):
            self.values['pid_' + str(loop)] = str(self.inst.query('PID? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['pid_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_ramp(self, loop, io, rate):
        if (loop == -1) and (io in range(1, 3)) and (rate <= 100 and rate >= 0.1):
            for i in range(1, 3):
                self.inst.write('RAMP ' + str(i) + ',' + str(io) + str(',') + str(rate))
                time.sleep(0.05)
            return self.get_ramp(-1)
        if (loop in range(1, 3)) and (io in range(1, 3)) and (rate <= 100 and rate >= 0.1):
            self.inst.write('RAMP ' + str(loop) + ',' + str(io) + ',' + str(rate))
            time.sleep(0.05)
            return self.get_ramp(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2, io must be 1 or 2, and rate between 0 and 100.')
            
    def get_ramp(self, loop):
        if loop == -1:
            self.values['both_ramps'] = list()
            for i in range(1, 3):
                self.values['ramp_' + str(i)] = str(self.inst.query('RAMP? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ramps'].append(self.values['ramp_' + str(i)])
            return self.values['both_ramps']
        if loop in range(1, 3):
            self.values['ramp_' + str(loop)] = str(self.inst.query('RAMP? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['ramp_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_rampst(self, loop):
        if loop == -1:
            self.values['both_rampsts'] = list()
            for i in range (1, 3):
                self.values['rampst_' + str(i)] = str(self.inst.query('RAMPST? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_rampsts'].append(self.values['rampst_' + str(i)])
            return self.values['both_rampsts']
        if loop in range (1, 3):
            self.values['rampst_' + str(loop)] = str(self.inst.query('RAMPST? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['rampst_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_range(self, ran):
        if ran in range(0, 4):
            self.inst.write('RANGE ' + str(ran))
            time.sleep(0.05)
        else:
            raise ValueError('Incorrect input. Range must be 0, 1, 2, or 3.')
            
    def get_range(self):
        self.values['range'] = str(self.inst.query('RANGE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['range']
            
    def get_input_reading(self, inp):
        if inp == -1:
            self.values['both_input_readings'] = list()
            for i in ['A', 'B']:
                self.values['input_reading_' + i.lower()] = str(self.inst.query('RDGST? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_input_readings'].append(self.values['input_reading_' + i.lower()])
            return self.values['both_input_readings']
        if inp.upper() in ['A', 'B']:
            self.values['input_reading_' + inp.lower()] = str(self.inst.query('RDGST? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['input_reading_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.') 
            
    def set_relay(self, relay, mode, inp, alrm):
        if (relay == -1) and (mode in range(0, 3)) and (inp in ['A', 'B']) and (alrm in range(0, 3)):
            for i in range(1, 3):
                self.inst.write('RELAY ' + str(i) + ',' + str(mode) + ',' + str(inp) + ',' + str(alrm))
                time.sleep(0.05)
            return self.get_relay(-1)
        if (relay in range(1, 3)) and (mode in range(0, 3)) and (inp in ['A', 'B']) and (alrm in range(0, 3)):
            self.inst.write('RELAY ' + str(relay) + ',' + str(mode) + ',' + str(inp) + ',' + str(alrm))
            time.sleep(0.05)
            return self.get_relay(inp)
        else:
            raise ValueError('Incorrect input. Relay must be -1, 1, or 2, mode must be between 0 and 2, inp must be A or B, and alrm must be between 0 and 2.')
            
    def get_relay(self, num):
        if num == -1:
            self.values['both_relays'] = list()
            for i in range(1, 3):
                self.values['relay_' + str(i)] = str(self.inst.query('RELAY? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_relays'].append(self.values['relay_' + str(i)])
            return self.values['both_relays']
        if num in range(1, 3):
            self.values['relay_' + str(num)] = str(self.inst.query('RELAY? ' + str(num))).replace('\r\n','')
            return self.values['relay_' + str(num)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
    def get_relay_status(self, hilo):
        if hilo == -1:
            self.values['both_relay_statuses'] = list()
            for i in range(1, 3):
                self.values['relay_status_' + str(i)] = str(self.inst.query('RELAYST? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_relay_statuses'].append(self.values['relay_status_' + str(i)])
            return self.values['both_relay_statuses']
        if hilo in range(1, 3):
            self.values['relay_status_' + str(hilo)] = str(self.inst.query('RELAYST? ' + str(hilo))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['relay_status_' + str(hilo)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
            
    def get_rev(self):
        self.values['input_firmware'] = str(self.inst.query('REV?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['input_firmware']

    def gen_softcal(self, std, dest, sn, t1, u1, t2, u2, t3, u3):
        if (std in [1, 6, 7]) and (dest in range(21, 42)) and (len(sn) in range(0, 11)):
            self.inst.write('SCAL ' + str(std) + ',' + str(dest) + ',' + str(dest) + ',' + str(sn) + ',' + str(t1) + ',' + str(u1) + ',' + str(t2) + ',' + str(u2) + ',' + str(t3) + ',' + str(u3))
            time.sleep(0.05)
            return 'Set SoftCal curve.'
        else:
            raise ValueError('Incorrect input. std must be 1, 6, or 7, dest must be between 21 and 41, and sn must be of a length of 10 or less.')
            
    def set_setpoint(self, loop, value):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('SETP ' + str(i) + ',' + str(value))
                time.sleep(0.05)
            return self.get_setpoint(-1)
        if loop in range(1, 3):
            self.inst.write('SETP ' + str(loop) + ',' + str(value))
            time.sleep(0.05)
            return self.get_setpoint(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_setpoint(self, loop):
        if loop == -1:
            self.values['both_setpoints'] = list()
            for i in range(1, 3):
                self.values['setpoint_' + str(i)] = str(self.inst.query('SETP? ' + str(i))).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_setpoints'].append(self.values['setpoint_' + str(i)])
            return self.values['both_setpoints']
        if loop in range(1, 3):
            self.values['setpoint_' + str(loop)] = str(self.inst.query('SETP? ' + str(loop))).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['setpoint_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_srdg(self, inp):
        if inp == -1:
            self.values['both_sensor_unit_inputs'] = list()
            for i in ['A','B']:
                self.values['sensor_unit_input_' + i.lower()] = str(self.inst.query('SRDG? ' + i.upper())).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_sensor_unit_inputs'].append(self.values['sensor_unit_input_' + i.lower()])
            return self.values['both_sensor_unit_inputs']
        if inp.upper() in ['A', 'B']:
            self.values['sensor_unit_input_' + inp.lower()] = str(self.inst.query('SRDG? ' + inp.upper())).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['sensor_unit_input_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def get_thermocouple(self):
        self.values['thermocouple_junction_temperature'] = str(self.inst.query('TEMP?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['thermocouple_junction_temperature']
            
    def is_tuning(self):
        self.values['tune_test'] = str(self.inst.query('TUNEST?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['tune_test']

    def set_zone(self, loop, zone, setp, p, i, d, mout, ran):
        if (loop == -1) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0):
            for i in range(1, 3):
                self.inst.write('ZONE ' + str(i) + ',' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1')
                time.sleep(0.05)
            return self.get_zone(-1)
        if (loop == 1) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0):
            if ran in range(0, 3):
                self.inst.write('ZONE 1,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + str(ran))
                time.sleep(0.05)
            return self.get_zone(1)
        if (loop == 2) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0):
            self.inst.write('ZONE 2,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1')
            time.sleep(0.05)
            return self.get_zone(2)
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_zone(self, loop, zone):
        if (loop == -1) and (zone == -1):
            self.values['both_control_loops_all_zones'] = list()
            for i in range(1, 3):
                for x in range(1, 11):
                    self.values['control_loop_' + str(i) + '_zone_' + str(x)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(x))).replace('\r\n', '')
                    time.sleep(0.05)
                    self.values['both_control_loops_all_zones'].append(self.values['control_loop_' + str(i) + '_zone_' + str(x)])
            return self.values['both_control_loops_all_zones']
        if (loop == -1) and (zone in range(1, 11)):
            self.values['both_control_loops_zone_' + str(zone)] = list()
            for i in range (1, 3):
                self.values['control_loop_' + str(i) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(zone))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_control_loops_zone_' + str(zone)].append(self.values['control_loop_' + str(i) + '_zone_' + str(zone)])
            return self.values['both_control_loops_zone_' + str(zone)]
        if (loop in range(1, 3)) and (zone in range(1,11)):
            self.values['control_loop_' + str(loop) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(loop) + ',' + str(zone))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['control_loop_' + str(loop) + '_zone_' + str(zone)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2 and zone between 1 and 10.')
            
    def start_logging_csv(self, interval = 5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_csv, 'interval', seconds = interval)
        sched.start()
        
    def lakeshore_logging_csv(self, path=None, filename=None, units = 'K'):
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.csv'
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        number = self.get_number()
        out = self.get_temp(-1)
        time.sleep(0.05)
        ctime = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        ctime.replace(',','').replace(' ','')
        out[0] = str(out[0])
        out[1] = str(out[1])
        out.append(str(self.get_heater_percent()))
        time.sleep(0.05)
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, ctime)
        out.insert(0, date)
        setpoint = str(self.get_setpoint(-1)).replace(',','|')
        time.sleep(0.05)
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        header = 'date,time, seconds, hours, Channel A, \'A\' units, setpoints, Lakeshore Number, Channel B, \'B\' units, heater percent 1,\n'
        with open(os.path.join(path,filename), 'a') as f: #creates .csv file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .csv file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write(header) #if .csv file is empty, header is written in
                f.close()
        out = str(out).replace('[', '').replace(']', '').replace('\'','')
        with open(os.path.join(path,filename), 'a') as f:
            f.write(str(out)) #Writes lakeshore information to .csv file
            f.write('\n')
            f.close()
                
    def start_logging_txt(self, interval = 5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_txt, 'interval', seconds=interval)
        sched.start()
                
    def lakeshore_logging_txt(self, path=None,filename=None, units = 'K'): #Check against 335
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.txt'
        number = self.get_number()
        header = 'date\t\t time\t\t seconds\t hours\t\t Channel A\t \'A\' units\t setpoints\t\t Lakeshore Number\t Channel B\t \'B\' units\t heater percent 1\n'
        out = self.get_temp(-1)
        ctime = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        ctime.replace(',','').replace(' ','')
        out.append(self.get_heater_percent())
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, ctime)
        out.insert(0, date)
        setpoint = self.get_setpoint(-1)
        setpoint[0] = float(setpoint[0].replace('+',''))
        setpoint[1] = float(setpoint[1].replace('+',''))
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        
        try:
            out[4] = '%.3f' % float((str(out[4])).replace('+',''))
        except (IndexError):
            out[4] = 0.000
        try:
            out[8] = '%.3f' % float((str(out[8])).replace('+',''))
        except(IndexError):
            out[8] = 0.000
        try:
            out[10] = '%.3f' % float((str(out[10])).replace('+',''))
        except(IndexError):
            out[10] = 0.000

        # Aligns columns
        out[2] = str(out[2]) + '         '
        out[4] = str(out[4]) + '        '
        out[6] = '        ' + str(out[6]) + '        '
        out[7] =str(out[7]) + '    '
        out[8] = '        ' + str(out[8]) + '        '
        out[9] = str(out[9]) + '        '

        with open(os.path.join(path,filename), 'a') as f: #creates .txt file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .txt file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write('{:<20}'.format(header)) #if .txt file is empty, header is written in
                f.close()
        with open(os.path.join(path,filename), 'a') as f:
            out = str(out).replace('[','').replace(']','').replace('\'','').replace(',','\t')+'\n'
            f.write('{:^30}'.format(out))
            f.close()
        
    def pause_logging(self):
        sched.pause()
        return 'Logging paused'
        
    def resume_logging(self):
        sched.resume()
        return 'Logging resumed'
        
    def stop_logging(self):
        sched.shutdown()
        return 'Logging stopped'

class lakeshore332:
    def __init__(self, asrl, timeout = 2 * 1000, autodetect = False, baud = 9600):
        self.rm = pyvisa.ResourceManager()
        #auto connects to first lakeshore it finds
        """
        if autodetect:
            for res in self.rm.list_resources():
                self.rm.open_resource(res)
                self.inst.write('*IDN')
                info = self.inst.read()
                if str(info[0]).upper() == 'LSCI':
                    break
                if str(info[0]).upper() != 'LSCI':
                    continue
        else:
            self.inst = self.rm.open_resource(asrl)
        """
        self.inst = self.rm.open_resource(asrl)
        self.inst.data_bits = 7
        self.inst.parity = Parity(1)
        if baud in [300, 1200, 9600]:
            self.inst.baud_rate = baud #Can be configured to 300, 1200, or 9600.
        else:
            raise ValueError('Baud rate must be 300, 1200, or 9600.')
        self.inst.term_chars = '\n'
        self.values = dict()
        global sched
        sched = BackgroundScheduler()
        
    def close(self):
        self.inst.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        
    def read(self):
        print self.inst.read()
        
    def clear_interface(self):
        """
        Clears the bits in the Status Byte Register and Standard Event Status Register and 
        terminates all pending operations. Clears the interface, but not the controller.
        """
        self.inst.write('*CLS')
        time.sleep(0.05)
        
    def set_ese(self, ese):
        """
        Each bit is assigned a bit weighting and represents the enable/disable mask 
        of the corresponding event flag bit in the Standard Event Status Register.
        """
        self.inst.write('*ESE ' + str(ese))
        time.sleep(0.05)
        return self.get_ese()
        
    def get_ese(self):
        self.values['ese'] = str(self.inst.query('*ESE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ese']
        
    def get_esr(self):
        self.values['esr'] = str(self.inst.query('*ESR?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['esr']

    def get_info(self):
        self.values['idn'] = str(self.inst.query('*IDN?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['idn']

    def get_number(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        time.sleep(0.05)
        self.values['number'] = str(out[2])
        return self.values['number']

    def get_model(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['model'] = str(out[1])
        return self.values['model']

    def get_manu(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['manu'] = str(out[0])
        return self.values['manu']

    def set_rst(self):
        """
        Sets controller parameters to power-up settings.
        """
        self.inst.write('*RST')
        time.sleep(0.05)
        return 'Controller set to power-up settings.'
        
    def set_sre(self, sre):
        """
        Each bit has a bit weighting and represents the enable/disable mask of
        the corresponding status flag bit in the Status Byte Register.
        """
        self.inst.write('*SRE ' + str(sre))
        time.sleep(0.05)
        return self.get_sre()
        
    def get_sre(self):
        self.values['sre'] = str(self.inst.query('*SRE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['sre']

    def get_stb(self):
        """
        Acts like a serial poll, but does not reset the register to all zeros. 
        The integer returned represents the sum of the bit weighting of the 
        status flag bits that are set in the Status Byte Register.
        """
        self.values['stb'] = str(self.inst.query('*STB?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['stb']

    def is_error(self):
        self.values['tst'] = str(self.inst.query('*TST?')).replace('\r\n','').replace('\t','')
        if self.values['tst'] is '':
            self.values['tst'] = 0
        time.sleep(0.05)
        return self.values['tst']

    def set_alarm(self, inp, offon, source, hi, lo, db, le):
        if (inp == -1) and (offon in range(0, 2)) and (source in range(1, 5)) and (le in range(0, 2)):
            for i in ['A', 'B']:
                self.inst.write('ALARM ' + i + ',' + str(offon) + ',' + str(source) + ',' + str(hi) + ',' + str(lo) + ',' + str(db) + ',' + str(le) + ',')
                time.sleep(0.05)
            return self.get_alarm(-1)
        if (inp.upper() in ['A', 'B']) and (offon in range(0, 2)) and (source in range(1, 5)) and (le in range(0, 2)):
            self.inst.write('ALARM ' + inp.upper() + ',' + str(offon) + ',' + str(source) + ',' + str(hi) + ',' + str(lo) + ',' + str(db) + ',' + str(le) + ',')
            time.sleep(0.05)
            return self.get_alarm(inp)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_alarm(self, inp):
        if inp == -1:
            self.values['both_alarms'] = list()
            for i in ['A', 'B']:
                self.values['alarm_' + i.lower()] = str(self.inst.query('ALARM? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_alarms'].append(self.values['alarm_' + i.lower()])
            return self.values['both_alarms']
        if inp.upper() in ['A', 'B']:
            self.values['alarm_' + inp.lower()] = str(self.inst.query('ALARM? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['alarm_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def get_alarmst(self, inp):
        if inp == -1:
            self.values['both_alarm_statuses'] = list()
            for i in ['A', 'B']:
                self.values['alarm_status_' + i.lower()] = str(self.inst.query('ALARMST? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_alarm_statuses'].append(self.values['alarm_status_' + i.lower()])
            return self.values['both_alarm_statuses']
        if inp.upper() in ['A', 'B']:
            self.values['alarm_status_' + inp.lower()] = str(self.inst.query('ALARMST? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['alarm_status_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def reset_alarmst(self):
        self.inst.write('ALARMST')
        time.sleep(0.05)
        return 'High and low status alarms cleared.'
        
    def set_analog(self, bi, mode, inp, source, hi, lo, man):
        if (bi in range(0, 2)) and (mode in range(0, 4)) and (source in range(1, 5)):
            if mode == 1:
                self.inst.write('ANALOG ' + str(bi) + ',' + str(mode) + ',' + str(inp) + ',' + str(source) + ',' + str(hi) + ',' + str(lo))
                time.sleep(0.05)
            if mode == 2:
                self.inst.write('ANALOG ' + str(bi) + ',' + str(mode) + ',' + str(inp) + ',' + str(source) + ',' + str(man))
                time.sleep(0.05)
            if mode not in [1, 2]:
                self.inst.write('ANALOG ' + str(bi) + ',' + str(mode) + ',' + str(inp) + ',' + str(source))
                time.sleep(0.05)
            return self.get_analog()
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_analog(self):
        self.values['analog'] = str(self.inst.query('ANALOG?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['analog']

    def get_aout(self):
        self.values['aout'] = str(self.inst.query('AOUT?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['aout']

    def set_baud(self, baud):
        if baud in range(0, 3):
            self.inst.write('BAUD ' + str(baud))
            time.sleep(0.05)
            return self.get_baud()
        else:
            raise ValueError('Incorrect input. Input must be be 0, 1, or 2.')
            
    def get_baud(self):
        self.values['baud'] = str(self.inst.query('BAUD?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['baud']

    def set_beep(self, beep):
        if beep in range(0, 2):
            self.inst.write('BEEP ' + str(beep))
            time.sleep(0.05)
            return self.get_beep()
        else:
            raise ValueError('Incorrect input. Beep must be 0 or 2.')
            
    def get_beep(self):
        self.values['beep'] = str(self.inst.query('BEEP?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['beep']

    def set_brightness(self, brit):
        if brit in range(0, 4):
            self.inst.write('BRIGT ' + str(brit))
            time.sleep(0.05)
            return self.get_brightness()
        else:
            raise ValueError('Incorrect input. Brit must be 0, 1, 2, or 3.')
            
    def get_brightness(self):
        self.values['brightness'] = str(self.inst.query('BRIGT?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['brightness']

    def set_cmode(self, loop, mode):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('CMODE ' + str(i) + ',' + str(mode))
                time.sleep(0.05)
            return self.get_cmode(-1)
        if (loop in range(1, 3)) and (mode in range(1, 7)):
            self.inst.write('CMODE ' + str(loop) + ',' + str(mode))
            time.sleep(0.05)
            return self.get_cmode(loop)
        else:
            raise ValueError('Incorrect input. Loop must be either -1, 1, 2 and mode must be between 1 and 6.')
            
    def get_cmode(self, loop):
        if loop == -1:
            self.values['both_cmodes'] = list()
            for i in range (1, 3):
                self.values['cmode_' + str(i)] = str(self.inst.query('CMODE? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_cmodes'].append(self.values['cmode_' + str(i)])
            return self.values['both_cmodes']
        if loop in range(1, 3):
            self.values['cmode_loop_' + str(loop)] = str(self.inst.query('CMODE? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['cmode_loop_' + str(loop)]
        else:
            raise ValueError('Inocorrect input. Loop must be either -1, 1, or 2.')

    def get_crdg(self, ab):
        if ab == -1:
            self.values['both_crdgs'] = list()
            for i in ['A','B']:
                self.values['crdg_'+ i.lower()] = str(self.inst.query('CRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_crdgs'].append(self.values['crdg_'+ i.lower()])
            return self.values['both_crdgs']
        if ab.upper() in ['A','B']:
            self.values['crdg_' + ab.lower()] = str(self.inst.query('CRDG? ' + str(ab).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['crdg_' + ab.lower()]
        else:
            raise ValueError('Incorrect input. Input must be A, B, or -1.')
            
    def delete_curve(self, curve):
        if curve == -1:
            for i in range(21, 42):
                self.inst.write('CRVDEL ' + str(i))
            return self.get_curve(-1)
        if curve in range(21, 42):
            self.inst.write('CRVDEL ' + str(curve))
            return self.get_curve(curve)
        else:
            raise ValueError('Incorrect input. Curve must be between 21 and 41 be -1.')
            
    def get_curve(self, curve):
        if curve == -1:
            self.values['all_curves'] = list()
            for i in range (1, 42):
                self.values['curve_' + str(i)] = str(self.inst.query('CRVHDR? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curves'].append(self.values['curve_' + str(i)])
            return self.values['all_curves']
        if curve in range(1, 42):
            self.values['curve_' + str(curve)] = str(self.inst.query('CRVHDR? ' + str(curve))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_' + str(curve)]
        else:
            raise ValueError('Incorrect input. Curve must be between 1 and 41 or be -1.')
            
    def set_curve_header(self, curve, name, sn, frmt, lim_val, coe):
        """
        Configures the user curve header.
        """
        if (curve in range(21, 42)) and (len(name) in range (1, 16)) and (len(sn) in range(1, 11)) and (frmt in range(1,5)) and (coe in range(1, 3)):
            self.inst.write('CRVHDR ' + str(curve) + ',' + str(name) + ',' + str(sn) + ',' + str(frmt) + ',' + str(lim_val) + ',' + str(coe))
            time.sleep(0.05)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')

    def set_curve_point(self, curve, index, unit, temp):
        """
        Configures a user curve data point.
        """
        if (curve in range(21, 42)) and (index in range(1, 201)) and (len(unit) in range(1, 7)) and (temp in range(1, 7)):
            self.inst.write('CRVPT ' + str(curve) + ',' + str(index) + ',' + str(unit) + ',' + str(temp))
            time.sleep(0.05)
            return self.get_curve_point(curve, index)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_curve_point(self, curve, index):
        if (curve == -1) and (index == -1):
            self.values['all_curve_points'] = list()
            for i in range(1, 42):
                for x in range(1, 201):
                    self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(x))).replace('\r\n','')
                    time.sleep(0.05)
                    self.values['all_curve_points'].append(self.values['curve_point_at_' + str(curve) + '_' + str(index)])
            return self.values['all_curve_points']
        if (curve == -1) and (index in range(1, 201)):
            self.values['all_curve_points_for_index_' + str(index)] = list()
            for i in range(1,42):
                self.values['curve_point_at_' + str(i) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(index))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_for_index_' + str(index)].append(self.values['curve_point_at_' + str(i) + '_' + str(index)])
            return self.values['all_curve_points_for_index_' + str(index)]
        if (curve in range(1, 42)) and (index == -1):
            self.values['all_curve_points_at_curve_' + str(curve)] = list()
            for i in range(1, 201):
                self.values['curve_point_at_' + str(curve) + '_' + str(i)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_at_curve_' + str(curve)].append(self.values['curve_point_at_' + str(curve) + '_' + str(i)])
            return self.values['all_curve_points_at_curve_' + str(curve)]
        if (curve in range(1, 42)) and (index in range(1, 201)):
            self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(index))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_point_at_' + str(curve) + '_' + str(index)]
        else:
            raise ValueError('Incorrect input. Curve must be between 21 and 41 and index must be between 1 and 200.')
            
    def set_control_loop(self, loop, inp, units, power, cp):
        if (loop == -1) and (inp.upper() in ['A','B']) and (units in range(1, 4)) and (power in range(0, 2)) and (cp in range(1, 3)):
            for i in range(1, 3):
                self.inst.write('CSET ' + str(i) + ',' + str(inp).upper() + ',' + str(units) + ',' + str(power) + str(cp))
                time.sleep(0.05)
            return self.get_control_loop(-1)
        if (loop in range(1, 3)) and (inp.upper() in ['A','B']) and (units in range(1, 4)) and (power in range(0, 2)) and (cp in range(1, 3)):
            self.inst.write('CSET ' + str(loop) + ',' + str(inp).upper() + ',' + str(units) + ',' + str(power) + str(cp))
            time.sleep(0.05)
            return self.get_control_loop(loop)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_control_loop(self, loop):
        if loop == -1:
            self.values['both_control_loops'] = list()
            for i in range(1, 3):
                self.values['control_loop_' + str(i)] = str(self.inst.query('CSET? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_control_loops'].append(self.values['control_loop_' + str(i)])
            return self.values['both_control_loops']
        if loop in range(1, 3):
            self.values['control_loop_' + str(loop)] = str(self.inst.query('CSET? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['control_loop_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_default(self):
        """
        Sets all configuration values to factory defaults and resets the instrument.
        """
        self.inst.write('DFTL 99')
        time.sleep(0.05)
        return 'Configuration settings set to default values.'
        
    def set_display_field(self, field, item, source=None):
        if (field == -1) and (item in range(0, 5)):
             if (item in range(1, 3)) and (source in range(1, 7)):
                 for i in range (1, 5):
                     self.inst.write('DISPFLD ' + str(i) + ',' + str(item) + ',' + str(source))
                     time.sleep(0.05)
                 return self.get_display_field(-1)
             else:
                for i in range(1, 5):
                    self.inst.write('DISPFLD ' + str(i) + ',' + str(item))
                    time.sleep(0.05)
                return self.get_display_field(-1)
        if (field in range(1, 5)) and (item in range(0, 5)):
            if (item in range(1, 3)) and (source in range(1, 7)):
                self.inst.write('DISPFLD ' + str(field) + ',' + str(item) + ',' + str(source))
                time.sleep(0.05)
                return self.get_display_field(field)
            else:
                self.inst.write('DISPFLD ' + str(field) + ',' + str(item))
                time.sleep(0.05)
                return self.get_display_field(field)
        else:
            raise ValueError('Incorrect input. Field and item must be between 1 and 4 and source is between 1 and 3 if item is 1 or 2.')
            
    def get_display_field(self, field):
        if field == -1:
            self.values['all_display_fields'] = list()
            for i in range (1, 5):
                self.values['display_field_' + str(i)] = str(self.inst.query('DISPFLD? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_display_fields'].append(self.values['display_field_' + str(i)])
                time.sleep(0.05)
            return self.values['all_display_fields']
        if field in range(1, 5):
            self.values['display_field_' + str(field)] = str(self.inst.query('DISPFLD? ' + str(field))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['display_field_' + str(field)]
        else:
            raise ValueError('Incorrect input. Field must be -1 or between 1 and 4.')

    def set_emul(self, offon):
        if offon in range(0, 2):
            self.inst.write('EMUL ' + str(offon))
            time.sleep(0.05)
            return self.get_emul()
        else:
            raise ValueError('Incorrect input. Input must be either 0 or 1.')
            
    def get_emul(self):
        self.values['emul'] = str(self.inst.query('EMUL?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['emul']

    def set_filter(self, inp, io, points, window):
        if (inp == -1) and (io in range(0, 2)) and (points in range(2, 65)) (window in range(1, 11)):
            for i in ['A', 'B']:
                self.inst.write('FILTER ' + i + ',' + str(io) + ',' + str(points) + ',' + str(window))
                time.sleep(0.05)
            return self.get_filter(-1)
        if (inp.upper() in ['A','B']) and (io in range(0, 2)) and (points in range(2, 65)) (window in range(1, 11)):
            self.inst.write('FILTER ' + str(inp).upper() + ',' + str('io') + ',' + str(points) + ',' + str(window))
            time.sleep(0.05)
            return self.get_filter(inp)
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B, io must be 0 or 1, points must be between 2 and 64, and window must be between 1 and 10.')
            
    def get_filter(self, inp):
        if inp == -1:
            self.values['both_filters'] = list()
            for i in ['A','B']:
                self.values['filter_' + i.lower()] = str(self.inst.query('FILTER? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_filters'].append(self.values['filter_' + i.lower()])
            return self.values['both_filters']
        if inp.upper() in ['A','B']:
            self.values['filter_' + inp.lower()] = str(self.inst.query('FILTER? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['filter_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B')
            
    def get_heater_percent(self):
        self.values['heater_1_percent'] = str(self.inst.query('HTR?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['heater_1_percent']

    def get_heater_status(self):
        self.values['heater_status'] = str(self.inst.query('HTRST?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['heater_status']

    def set_ieee(self, term, eoi, addr):
        if (term in range(0, 4)) and (eoi in range(0, 2)) and (addr in range(1, 31)):
            self.inst.write('IEEE ' + str(term) + str(eoi) + str(addr))
            time.sleep(0.05)
            return self.get_ieee(term)
        else:
            raise ValueError('Incorrect input. Terminator must be between 0 and 3, EOI must be 0 or 1, and address must be between 1 and 30.')
            
    def get_ieee(self):
        self.values['ieee'] = str(self.inst.query('IEEE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ieee']

    def set_curve_num(self, inp, num):
        if (inp == -1) and (num in range(0, 42)):
            for i in ['A', 'B']:
                self.inst.write('INCRV ' + i + ',' + str(num))
                time.sleep(0.05)
            return self.get_curve_num(-1)
        if (inp.upper() in ['A','B']) and (num in range(0, 42)):
            self.inst.write('INCRV ' + str(inp).upper() + ',' + str(num))
            time.sleep(0.05)
            return self.get_curve_num(str(inp).upper())
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B and num must be between 0 and 41.')
            
    def get_curve_num(self, inp):
        if inp == -1:
            self.values['both_curve_numbers'] = list()
            for i in ['A','B']:
                self.values['curve_number_' + i.lower()] = str(self.inst.query('INCRV? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_curve_numbers'].append(self.values['curve_number_' + i.lower()])
            return self.values['both_curve_numbers']
        if inp.upper() in ['A','B']:
            self.values['curve_number_' + inp.lower()] = str(self.inst.query('INCRV? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_number_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B')
            
    def set_intype(self, inp, sen, comp):
        if (inp == -1) and (sen in range(0, 13)) and (comp in range (0, 2)):
            for i in ['A', 'B']:
                self.inst.write('INTYPE ' + i + ',' + str(sen) + ',' + str(comp))
                time.sleep(0.05)
            return self.get_intype()
        if (inp.upper() in ['A','B']) and (sen in range(0, 10)) and (comp in range(0, 2)):
            self.inst.write('INTYPE ' + str(inp) + ',' + str(sen) + ',' + str(comp))
            time.sleep(0.05)
            return self.get_intype(str(inp).upper())
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B, sen must be between 0 and 12, and comp must be 0 or 1.')
            
    def get_intype(self, inp):
        if inp == -1:
            self.values['both_intypes'] = list()
            for i in ['A','B']:
                self.values['instype_' + i.lower()] = str(self.inst.query('INTYPE? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_intypes'].append(self.values['instype_' + i.lower()])
            return self.values['both_intypes']
        if inp.upper() in ['A','B']:
            self.values['intype_' + str(inp).lower()] = str(self.inst.query('INTYPE? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['intype_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B.')
            
    def get_last_key_press(self):
        """
        Returns a number descriptor of the last key pressed since the last KEYST?.
        Returns “21” after initial power-up. Returns “00” if no key pressed since last query.
        """
        self.values['last_key_press'] = str(self.inst.query('KEYST?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['last_key_press']

    def get_temp(self, inp):
        if inp == -1:
            self.values['both_temperatures'] = list()
            for i in ['A','B']:
                self.values['temperature_' + i.lower()] = str(self.inst.query('KRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_temperatures'].append(self.values['temperature_' + i.lower()])
            return self.values['both_temperatures']
        if inp.upper() in ['A','B']:
            self.values['temperature_' + inp.lower()] = str(self.inst.query('KRDG? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['temperature_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B.')
            
    def get_ldat(self, inp):
        if inp == -1:
            self.values['both_linear_equations'] = list()
            for i in ['A', 'B']:
                self.values['linear_equation_' + i.lower()] = str(self.inst.query('LDAT? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_linear_equations'].append(self.values['linear_equation_' + i.lower()])
            return self.values['both_linear_equations']
        if inp.upper() in ['A', 'B']:
            self.values['linear_equation_' + inp.lower()] = str(self.inst.query('LDAT? ' + inp.upper())).replace('\r\n','')
            return self.values['linear_equation_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def set_linear(self, inp, eq, m, x, b, bv=None):
        if (inp == -1) and (eq in range(1, 3)) and (x in range(1, 4)) and (b in range(1, 6)):
            if b == 1:
                for i in ['A', 'B']:
                    self.inst.write('LINEAR ' + i + ',' + str(eq) + ',' + str(m) + ',' + str(x) + ',' + str(b) + ',' + str(bv))
                    time.sleep(0.05)
            if b != 1:
                for i in['A', 'B']:
                    self.inst.write('LINEAR ' + i + ',' + str(eq) + ',' + str(m) + ',' + str(x) + ',' + str(b))
                    time.sleep(0.05)
            return self.get_linear(-1)
        if (inp in ['A','B']) and (eq in range(1, 3)) and (x in range(1, 4)) and (b in range(1, 6)):
            if b == 1:
                self.inst.write('LINEAR ' + str(inp) + ',' + str(eq) + ',' + str(m) + ',' + str(x) + ',' + str(b) + ',' + str(bv))
                time.sleep(0.05)
            if b == -1:
                self.inst.write('LINEAR ' + str(inp) + ',' + str(eq) + ',' + str(m) + ',' + str(x) + ',' + str(b))
                time.sleep(0.05)
            return self.get_linear(inp)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_linear(self, inp):
        if inp == -1:
            self.values['both_linears'] = list()
            for i in ['A', 'B']:
                self.values['linear_' + i.lower()] = str(self.inst.query('LINEAR ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_linears'].append(self.values['linear_' + i.lower()])
            return self.values['both_linears']
        if inp.upper() in ['A', 'B']:
            self.values['linear_' + inp.lower()] = str(self.inst.query('LINEAR ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['linear_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def set_lock(self, state, code):
        if (state in range (0, 2)):
            self.inst.write('LOCK ' + str(state) + ',' + str(code))
            time.sleep(0.05)
            return self.get_lock()
        else:
            raise ValueError('Incorrect input. State must be 0 or 1 and code must be between 000 and 999.')
            
    def get_lock(self):
        self.values['lock'] = str(self.inst.query('LOCK?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['lock']

    def get_mdat(self, inp):
        if inp == -1:
            self.values['both_mdats'] = list()
            for i in ['A', 'B']:
                self.values['mdat_' + i.lower()] = str(self.inst.query('MDAT? ' + i.upper())).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mdats'].append(self.values['mdat_' + i.lower()])
            return self.values['both_mdats']
        if inp.upper() in ['A', 'B']:
            self.values['mdat_' + inp.lower()] = str(self.inst.query('MDAT? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mdat_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B.')
            
    def set_mnmx(self, inp, source):
        if (inp == -1) and (source in range(1, 5)):
            for i in ['A', 'B']:
                self.inst.write('MNMX ' + i + ',' + str(source))
                time.sleep(0.05)
            return self.get_mnmx()
        if inp.upper() in ['A', 'B']:
            self.inst.write('MNMX ' + inp.upper() + ',' + str(source))
            time.sleep(0.05)
        else:
            raise ValueError('Incorrect value. Inp must be -1, A, or B and source must be between 1 and 4.')
            
    def get_mnmx(self, inp):
        if inp == -1:
            self.values['both_mnmxs'] = list()
            for i in ['A', 'B']:
                self.values['mnmx_' + i.lower()] = str(self.inst.query('MNMX? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mnmxs'].append(self.values['mnmx_' + i.lower()])
            return self.values['both_mnmxs']
        if inp.upper() in ['A', 'B']:
            self.values['mnmx_' + inp.lower()] = str(self.inst.query('MNMX? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mnmx_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def reset_mnmx(self):
        self.inst.write('MNMXRST')
        time.sleep(0.05)
        return 'Minimum and maximum function reset.'
        
    def set_mode(self, mode):
        if mode in range(0, 3):
            self.inst.write('MODE ' + str(mode))
            time.sleep(0.05)
            return self.get_mode()
        else:
            raise ValueError('Incorrect input. Input must be 0, 1, or 2.')
            
    def get_mode(self):
        self.values['mode'] = str(self.inst.query('MODE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['mode']

    def set_mout(self, loop, val):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('MOUT ' + str(i) + ',' + str(val))
                time.sleep(0.05)
            return self.get_mout(-1)
        if loop in range(1, 3):
            self.inst.write('MOUT ' + str(loop) + str(val))
            time.sleep(0.05)
            return self.get_mout(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_mout(self, loop):
        if loop == -1:
            self.values['both_mouts'] = list()
            for i in range(1, 3):
                self.values['mout_' + str(i)] = str(self.inst.query('MOUT? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mouts'].append(self.values['mout_' + str(i)])
            return self.values['both_mouts']
        if loop in range(1, 3):
            self.values['mout_' + str(loop)] = str(self.inst.query('MOUT? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mout_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_pid(self, loop, p, i, d):
        """
        Setting resolution is less than 6 digits indicated.
        """
        if (loop == -1) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            for i in range(1, 3):
                self.inst.write('PID ' + str(i) + ',' + str(p) + ',' + str(i) + ',' + str(d))
                time.sleep(0.05)
            return self.get_pid(-1)
        if (loop in range(1,3)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            self.inst.write('PID ' + str(loop) + ',' + str(p) + ',' + str(i) + ',' + str(d))
            time.sleep(0.05)
            return self.get_pid(loop)
        else:
            raise ValueError('Incorrect input. Refer to manual for proper parameters.')
            
    def get_pid(self, loop):
        if loop == -1:
            self.values['both_pids'] = list()
            for i in range(1, 3):
                self.values['pid_' + str(i)] = str(self.inst.query('PID? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_pids'].append(self.values['pid_' + str(i)])
            return self.values['both_pids']
        if loop in range(1, 3):
            self.values['pid_' + str(loop)] = str(self.inst.query('PID? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['pid_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_ramp(self, loop, io, rate):
        if (loop == -1) and (io in range(1, 3)) and (rate <= 100 and rate >= 0.1):
            for i in range(1, 3):
                self.inst.write('RAMP ' + str(i) + str(io) + ',' + str(rate))
                time.sleep(0.05)
            return self.get_ramp(-1)
        if (loop in range(1, 3)) and (io in range(1, 3)) and (rate <= 100 and rate >= 0.1):
            self.inst.write('RAMP ' + str(loop) + ',' + str(io) + ',' + str(rate))
            time.sleep(0.05)
            return self.get_ramp(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2, io must be 1 or 2, and rate between 0 and 100.')
            
    def get_ramp(self, loop):
        if loop == -1:
            self.values['both_ramps'] = list()
            for i in range(1, 3):
                self.values['ramp_' + str(i)] = str(self.inst.query('RAMP? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ramps'].append(self.values['ramp_' + str(i)])
            return self.values['both_ramps']
        if loop in range(1, 3):
            self.values['ramp_' + str(loop)] = str(self.inst.query('RAMP? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['ramp_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_rampst(self, loop):
        if loop == -1:
            self.values['both_rampsts'] = list()
            for i in range (1, 3):
                self.values['rampst_' + str(i)] = str(self.inst.query('RAMPST? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_rampsts'].append(self.values['rampst_' + str(i)])
            return self.values['both_rampsts']
        if loop in range (1, 3):
            self.values['rampst_' + str(loop)] = str(self.inst.query('RAMPST? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['rampst_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_range(self, ran):
        if ran in range(0, 4):
            self.inst.write('RANGE ' + str(ran))
            time.sleep(0.05)
        else:
            raise ValueError('Incorrect input. Range must be 0, 1, 2, or 3.')
            
    def get_range(self, loop):
        if loop == -1:
            self.values['both_ranges'] = list()
            for i in range (1, 3):
                self.values['range_' + str(i)] = str(self.inst.query('RANGE? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ranges'].append(self.values['range_' + str(i)])
            return self.values['both_ranges']
        if loop in range(1, 3):
            self.values['range_' + str(loop)] = str(self.inst.query('RANGE? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['range_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_input_reading(self, inp):
        if inp == -1:
            self.values['both_input_readings'] = list()
            for i in ['A', 'B']:
                self.values['input_reading_' + i.lower()] = str(self.inst.query('RDGST? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_input_readings'].append(self.values['input_reading_' + i.lower()])
            return self.values['both_input_readings']
        if inp.upper() in ['A', 'B']:
            self.values['input_reading_' + inp.lower()] = str(self.inst.query('RDGST? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['input_reading_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.') 
            
    def set_relay(self, relay, mode, inp, alrm):
        if (relay == -1) and (mode in range(0, 3)) and (inp in ['A', 'B']) and (alrm in range(0, 3)):
            for i in range(1, 3):
                self.inst.write('RELAY ' + str(i) + ',' + str(mode) + ',' + str(inp) + ',' + str(alrm))
                time.sleep(0.05)
            return self.get_relay(-1)
        if (relay in range(1, 3)) and (mode in range(0, 3)) and (inp in ['A', 'B']) and (alrm in range(0, 3)):
            self.inst.write('RELAY ' + str(relay) + ',' + str(mode) + ',' + str(inp) + ',' + str(alrm))
            time.sleep(0.05)
            return self.get_relay(inp)
        else:
            raise ValueError('Incorrect input. Relay must be -1, 1, or 2, mode must be between 0 and 2, inp must be A or B, and alrm must be between 0 and 2.')
            
    def get_relay(self, num):
        if num == -1:
            self.values['both_relays'] = list()
            for i in range(1, 3):
                self.values['relay_' + str(i)] = str(self.inst.query('RELAY? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_relays'].append(self.values['relay_' + str(i)])
            return self.values['both_relays']
        if num in range(1, 3):
            self.values['relay_' + str(num)] = str(self.inst.query('RELAY? ' + str(num))).replace('\r\n','')
            return self.values['relay_' + str(num)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
    def get_relay_status(self, hilo):
        if hilo == -1:
            self.values['both_relay_statuses'] = list()
            for i in range(1, 3):
                self.values['relay_status_' + str(i)] = str(self.inst.query('RELAYST? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_relay_statuses'].append(self.values['relay_status_' + str(i)])
            return self.values['both_relay_statuses']
        if hilo in range(1, 3):
            self.values['relay_status_' + str(hilo)] = str(self.inst.query('RELAYST? ' + str(hilo))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['relay_status_' + str(hilo)]
        else:
            raise ValueError('Incorrect input. Input must be 1 or 2.')
            
    def get_rev(self):
        self.values['input_firmware'] = str(self.inst.query('REV?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['input_firmware']

    def gen_softcal(self, std, dest, sn, t1, u1, t2, u2, t3, u3):
        if (std == 1 or 6 or 7) and (dest in range(21, 42)) and (len(sn) in range(0, 11)):
            self.inst.write('SCAL ' + str(std) + ',' + str(dest) + ',' + str(dest) + ',' + str(sn) + ',' + str(t1) + ',' + str(u1) + ',' + str(t2) + ',' + str(u2) + ',' + str(t3) + ',' + str(u3))
            time.sleep(0.05)
            return 'Set SoftCal curve.'
        else:
            raise ValueError('Incorrect input. std must be 1, 6, or 7, dest must be between 21 and 41, and sn must be of a length of 10 or less.')
            
    def set_setpoint(self, loop, value):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('SETP ' + str(i) + ',' + str(value))
                time.sleep(0.05)
            return self.get_setpoint(-1)
        if loop in range(1, 3):
            self.inst.write('SETP ' + str(loop) + ',' + str(value))
            time.sleep(0.05)
            return self.get_setpoint(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_setpoint(self, loop):
        if loop == -1:
            self.values['both_setpoints'] = list()
            for i in range(1, 3):
                self.values['setpoint_' + str(i)] = str(self.inst.query('SETP? ' + str(i))).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_setpoints'].append(self.values['setpoint_' + str(i)])
            return self.values['both_setpoints']
        if loop in range(1, 3):
            self.values['setpoint_' + str(loop)] = str(self.inst.query('SETP? ' + str(loop))).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['setpoint_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_srdg(self, inp):
        if inp == -1:
            self.values['both_sensor_unit_inputs'] = list()
            for i in ['A','B']:
                self.values['sensor_unit_input_' + i.lower()] = str(self.inst.query('SRDG? ' + i.upper())).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_sensor_unit_inputs'].append(self.values['sensor_unit_input_' + i.lower()])
            return self.values['both_sensor_unit_inputs']
        if inp.upper() in ['A', 'B']:
            self.values['sensor_unit_input_' + inp.lower()] = str(self.inst.query('SRDG? ' + inp.upper())).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['sensor_unit_input_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def get_thermocouple(self):
        self.values['thermocouple_junction_temperature'] = str(self.inst.query('TEMP?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['thermocouple_junction_temperature']
            
    def is_tuning(self):
        self.values['tune_test'] = str(self.inst.query('TUNEST?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['tune_test']

    def set_zone(self, loop, zone, setp, p, i, d, mout, ran):
        if (loop == -1) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0):
            for i in range(1, 3):
                self.inst.write('ZONE ' + str(i) + ',' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1')
                time.sleep(0.05)
            return self.get_zone(-1)
        if (loop == 1) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0):
            if ran in range(0, 3):
                self.inst.write('ZONE 1,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + str(ran))
            time.sleep(0.05)
            return self.get_zone(1)
        if (loop == 2) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0):
            self.inst.write('ZONE 2,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1')
            time.sleep(0.05)
            return self.get_zone(2)
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_zone(self, loop, zone):
        if (loop == -1) and (zone == -1):
            self.values['both_control_loops_all_zones'] = list()
            for i in range(1, 3):
                for x in range(1, 11):
                    self.values['control_loop_' + str(i) + '_zone_' + str(x)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(x))).replace('\r\n', '')
                    time.sleep(0.05)
                    self.values['both_control_loops_all_zones'].append(self.values['control_loop_' + str(i) + '_zone_' + str(x)])
            return self.values['both_control_loops_all_zones']
        if (loop == -1) and (zone in range(1, 11)):
            self.values['both_control_loops_zone_' + str(zone)] = list()
            for i in range (1, 3):
                self.values['control_loop_' + str(i) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(zone))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_control_loops_zone_' + str(zone)].append(self.values['control_loop_' + str(i) + '_zone_' + str(zone)])
            return self.values['both_control_loops_zone_' + str(zone)]
        if (loop in range(1, 3)) and (zone in range(1,11)):
            self.values['control_loop_' + str(loop) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(loop) + ',' + str(zone))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['control_loop_' + str(loop) + '_zone_' + str(zone)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2 and zone between 1 and 10.')
            
    def start_logging_csv(self, interval = 5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_csv, 'interval', seconds = interval)
        sched.start()
        
    def lakeshore_logging_csv(self, path=None, filename=None, units = 'K'):
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.csv'
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        number = self.get_number()
        out = self.get_temp(-1)
        time.sleep(0.05)
        ctime = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        ctime.replace(',','').replace(' ','')
        out[0] = str(out[0])
        out[1] = str(out[1])
        out.append(str(self.get_heater_percent()))
        time.sleep(0.05)
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, ctime)
        out.insert(0, date)
        setpoint = str(self.get_setpoint(-1)).replace(',','|')
        time.sleep(0.05)
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        header = 'date,time, seconds, hours, Channel A, \'A\' units, setpoints, Lakeshore Number, Channel B, \'B\' units, heater percent 1,\n'
        with open(os.path.join(path,filename), 'a') as f: #creates .csv file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .csv file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write(header) #if .csv file is empty, header is written in
                f.close()
        out = str(out).replace('[', '').replace(']', '').replace('\'','')
        with open(os.path.join(path,filename), 'a') as f:
            f.write(str(out)) #Writes lakeshore information to .csv file
            f.write('\n')
            f.close()
                
    def start_logging_txt(self, interval = 5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_txt, 'interval', seconds=interval)
        sched.start()
                
    def lakeshore_logging_txt(self, path=None,filename=None, units = 'K'): #Check against 335
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.txt'
        number = self.get_number()
        header = 'date\t\t time\t\t seconds\t hours\t\t Channel A\t \'A\' units\t setpoints\t\t Lakeshore Number\t Channel B\t \'B\' units\t heater percent 1\n'
        out = self.get_temp(-1)
        ctime = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        ctime.replace(',','').replace(' ','')
        out.append(self.get_heater_percent())
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, ctime)
        out.insert(0, date)
        setpoint = self.get_setpoint(-1)
        setpoint[0] = float(setpoint[0].replace('+',''))
        setpoint[1] = float(setpoint[1].replace('+',''))
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        
        try:
            out[4] = '%.3f' % float((str(out[4])).replace('+',''))
        except (IndexError):
            out[4] = 0.000
        try:
            out[8] = '%.3f' % float((str(out[8])).replace('+',''))
        except(IndexError):
            out[8] = 0.000
        try:
            out[10] = '%.3f' % float((str(out[10])).replace('+',''))
        except(IndexError):
            out[10] = 0.000

        # Aligns columns
        out[2] = str(out[2]) + '         '
        out[4] = str(out[4]) + '        '
        out[6] = '        ' + str(out[6]) + '        '
        out[7] =str(out[7]) + '    '
        out[8] = '        ' + str(out[8]) + '        '
        out[9] = str(out[9]) + '        '

        with open(os.path.join(path,filename), 'a') as f: #creates .txt file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .txt file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write('{:<20}'.format(header)) #if .txt file is empty, header is written in
                f.close()
        with open(os.path.join(path,filename), 'a') as f:
            out = str(out).replace('[','').replace(']','').replace('\'','').replace(',','\t')+'\n'
            f.write('{:^30}'.format(out))
            f.close()
        
    def pause_logging(self):
        sched.pause()
        return 'Logging paused'
        
    def resume_logging(self):
        sched.resume()
        return 'Logging resumed'
        
    def stop_logging(self):
        sched.shutdown()
        return 'Logging stopped'
        
class lakeshore335:
    def __init__(self, asrl, timeout = 2 * 1000, autodetect = False):
        self.rm = pyvisa.ResourceManager()
        #auto connects to first lakeshore it finds
        """
        if autodetect:
            for res in self.rm.list_resources():
                self.rm.open_resource(res)
                self.inst.write('*IDN')
                info = self.inst.read()
                if str(info[0]).upper() == 'LSCI':
                    break
                if str(info[0]).upper() != 'LSCI':
                    continue
        else:
            self.inst = self.rm.open_resource(asrl)
        """
        self.inst = self.rm.open_resource(asrl)
        self.inst.data_bits = 7
        self.inst.parity = Parity(1)
        self.inst.baud_rate = 57600
        self.inst.term_chars = '\n'
        self.values = dict()
        global sched
        sched = BackgroundScheduler()
        
    def close(self):
        self.inst.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        
    def read(self):
        print self.inst.read()
        
    def clear_interface(self):
        """
        Clears the bits in the Status Byte Register and Standard Event Status Register and 
        terminates all pending operations. Clears the interface, but not the controller.
        """
        self.inst.write('*CLS')
        time.sleep(0.05)
        
    def set_ese(self, ese):
        """
        Each bit is assigned a bit weighting and represents the enable/disable mask 
        of the corresponding event flag bit in the Standard Event Status Register.
        """
        self.inst.write('*ESE ' + str(ese))
        time.sleep(0.05)
        return self.get_ese()
        
    def get_ese(self):
        self.values['ese'] = str(self.inst.query('*ESE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ese']
        
    def get_esr(self):
        self.values['esr'] = str(self.inst.query('*ESR?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['esr']

    def get_info(self):
        self.values['idn'] = str(self.inst.query('*IDN?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['idn']

    def get_number(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['number'] = str(out[2])
        return self.values['number']

    def get_model(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['model'] = str(out[1])
        return self.values['model']

    def get_manu(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['manu'] = str(out[0])
        return self.values['manu']

    def set_rst(self):
        """
        Sets controller parameters to power-up settings.
        """
        self.inst.write('*RST')
        time.sleep(0.05)
        return 'Controller set to power-up settings.'
        
    def set_sre(self, sre):
        """
        Each bit has a bit weighting and represents the enable/disable mask of
        the corresponding status flag bit in the Status Byte Register.
        """
        self.inst.write('*SRE ' + str(sre))
        time.sleep(0.05)
        return self.get_sre()
        
    def get_sre(self):
        self.values['sre'] = str(self.inst.query('*SRE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['sre']

    def get_stb(self):
        """
        Acts like a serial poll, but does not reset the register to all zeros. 
        The integer returned represents the sum of the bit weighting of the 
        status flag bits that are set in the Status Byte Register.
        """
        self.values['stb'] = str(self.inst.query('*STB?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['stb']

    def is_error(self):
        self.values['tst'] = str(self.inst.query('*TST?')).replace('\r\n','').replace('\t','')
        if self.values['tst'] is '':
            self.values['tst'] = 0
        time.sleep(0.05)
        return self.values['tst']

    def set_alarm(self, inp, offon, hi, lo, db, le, aud, vis):
        if (inp == -1) and (offon in range(0, 2)) and (le in range(0, 2)) and (aud in range(0, 2)) and (vis in range(0, 2)):
            for i in ['A', 'B']:
                self.inst.write('ALARM ' + i + ',' + str(offon) + ',' + str(hi) + ',' + str(lo) + ',' + str(db) + ',' + str(le) + ',' + str(aud) + ',' + str(vis))
                time.sleep(0.05)
            return self.get_alarm(-1)
        if (inp.upper() in ['A', 'B']) and (offon in range(0, 2)) and (le in range(0, 2)) and (aud in range(0, 2)) and (vis in range(0, 2)):
            self.inst.write('ALARM ' + inp.upper() + ',' + str(offon) + ',' + str(hi) + ',' + str(lo) + ',' + str(db) + ',' + str(le) + ',' + str(aud) + ',' + str(vis))
            time.sleep(0.05)
            return self.get_alarm(inp)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_alarm(self, inp):
        if inp == -1:
            self.values['both_alarms'] = list()
            for i in ['A', 'B']:
                self.values['alarm_' + i.lower()] = str(self.inst.query('ALARM? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_alarms'].append(self.values['alarm_' + i.lower()])
            return self.values['both_alarms']
        if inp.upper() in ['A', 'B']:
            self.values['alarm_' + inp.lower()] = str(self.inst.query('ALARM? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['alarm_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def get_alarmst(self, inp):
        if inp == -1:
            self.values['both_alarm_statuses'] = list()
            for i in ['A', 'B']:
                self.values['alarm_status_' + i.lower()] = str(self.inst.query('ALARMST? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_alarm_statuses'].append(self.values['alarm_status_' + i.lower()])
            return self.values['both_alarm_statuses']
        if inp.upper() in ['A', 'B']:
            self.values['alarm_status_' + inp.lower()] = str(self.inst.query('ALARMST? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['alarm_status_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def reset_alarmst(self):
        self.inst.write('ALARMST')
        time.sleep(0.05)
        return 'High and low status alarms cleared.'
        
    def set_analog(self, inp, unit, hi, lo, pol):
        if (inp == -1) and (unit in range(1, 4)) and (pol in range(0, 2)):
            for i in range(0, 3):
                self.inst.write('ANALOG 2,' + str(unit) + ',' + str(hi) + ',' + str(lo) + ',' + str(pol))
                time.sleep(0.05)
            return self.get_analog(-1) 
        if (inp in range(0, 3)) and (unit in range(1, 4)) and (pol in range(0, 2)):
            self.inst.write('ANALOG 2,' + str(unit) + ',' + str(hi) + ',' + str(lo) + ',' + str(pol))
            return self.get_analog(inp)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_analog(self):
        self.values['analog'] = str(self.inst.query('ANALOG? 2')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['analog']
            
    def autotune(self, out, mode):
        if (out == -1) and (mode in range(0, 3)):
            for i in range(1, 3):
                self.inst.write('ATUNE ' + str(i) + ',' + str(mode))
                time.sleep(0.05)
            return 'Autotune complete.'
        if (out in range(1, 3)) and (mode in range(0, 3)):
            self.inst.write('ATUNE ' + str(i) + ',' + str(mode))
            return 'Autotune complete.'
        else:
            raise ValueError('Incorrect input. Output must be 1 or and mdoe must be between 0 and 2.')
            
    def set_brightness(self, brit):
        if brit in range(0, 4):
            self.inst.write('BRIGT ' + str(brit))
            time.sleep(0.05)
            return self.get_brightness()
        else:
            raise ValueError('Incorrect input. Brit must be 0, 1, 2, or 3.')
            
    def get_brightness(self):
        self.values['brightness'] = str(self.inst.query('BRIGT?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['brightness']

    def get_crdg(self, ab):
        if ab == -1:
            self.values['both_crdgs'] = list()
            for i in ['A','B']:
                self.values['crdg_'+ i.lower()] = str(self.inst.query('CRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_crdgs'].append(self.values['crdg_'+ i.lower()])
            return self.values['both_crdgs']
        if ab.upper() in ['A','B']:
            self.values['crdg_' + ab.lower()] = str(self.inst.query('CRDG? ' + str(ab).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['crdg_' + ab.lower()]
        else:
            raise ValueError('Incorrect input. Input must be A, B, or -1.')
            
    def delete_curve(self, curve):
        if curve == -1:
            for i in range(21, 60):
                self.inst.write('CRVDEL ' + str(i))
            return self.get_curve(-1)
        if curve in range(21, 60):
            self.inst.write('CRVDEL ' + str(curve))
            return self.get_curve(curve)
        else:
            raise ValueError('Incorrect input. Curve must be between 21 and 59 or be -1.')
            
    def get_curve(self, curve):
        if curve == -1:
            self.values['all_curves'] = list()
            for i in range (1, 60):
                self.values['curve_' + str(i)] = str(self.inst.query('CRVHDR? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curves'].append(self.values['curve_' + str(i)])
            return self.values['all_curves']
        if curve in range(1, 60):
            self.values['curve_' + str(curve)] = str(self.inst.query('CRVHDR? ' + str(curve))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_' + str(curve)]
        else:
            raise ValueError('Incorrect input. Curve must be between 1 and 59 or be -1.')
            
    def set_curve_header(self, curve, name, sn, frmt, lim_val, coe):
        """
        Configures the user curve header.
        """
        if (curve in range(21, 60)) and (len(name) in range (1, 16)) and (len(sn) in range(1, 11)) and (frmt in range(1,5)) and (coe in range (1, 3)):
            self.inst.write('CRVHDR ' + str(curve) + ',' + str(name) + ',' + str(sn) + ',' + str(frmt) + ',' + str(lim_val) + ',' + str(coe))
            time.sleep(0.05)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')

    def set_curve_point(self, curve, index, unit, temp):
        """
        Configures a user curve data point.
        """
        if (curve in range(21, 60)) and (index in range(1, 201)) and (len(unit) in range(1, 7)) and (temp in range(1, 7)):
            self.inst.write('CRVPT ' + str(curve) + ',' + str(index) + ',' + str(unit) + ',' + str(temp))
            time.sleep(0.05)
            return self.get_curve_point(curve, index)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_curve_point(self, curve, index):
        if (curve == -1) and (index == -1):
            self.values['all_curve_points'] = list()
            for i in range(1, 60):
                for x in range(1, 201):
                    self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(x))).replace('\r\n','')
                    time.sleep(0.05)
                    self.values['all_curve_points'].append(self.values['curve_point_at_' + str(curve) + '_' + str(index)])
            return self.values['all_curve_points']
        if (curve == -1) and (index in range(1, 201)):
            self.values['all_curve_points_for_index_' + str(index)] = list()
            for i in range(1,60):
                self.values['curve_point_at_' + str(i) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(index))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_for_index_' + str(index)].append(self.values['curve_point_at_' + str(i) + '_' + str(index)])
            return self.values['all_curve_points_for_index_' + str(index)]
        if (curve in range(1, 60)) and (index == -1):
            self.values['all_curve_points_at_curve_' + str(curve)] = list()
            for i in range(1, 201):
                self.values['curve_point_at_' + str(curve) + '_' + str(i)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_at_curve_' + str(curve)].append(self.values['curve_point_at_' + str(curve) + '_' + str(i)])
            return self.values['all_curve_points_at_curve_' + str(curve)]
        if (curve in range(1, 60)) and (index in range(1, 201)):
            self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(index))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_point_at_' + str(curve) + '_' + str(index)]
        else:
            raise ValueError('Incorrect input. Curve must be between 21 and 41 and index must be between 1 and 200.')
            
    def set_default(self):
        """
        Sets all configuration values to factory defaults and resets the instrument.
        """
        self.inst.write('DFTL 99')
        time.sleep(0.05)
        return 'Configuration settings set to default values.'
        
    def set_diode_excite(self, inp, exc):
        if (inp == -1) and (exc in range(0, 2)):
            for i in ['A', 'B']:
                self.inst.write('DIOCUR ' + i + ',' + str(exc))
                time.sleep(0.05)
            return self.get_diode_excite(-1)
        if (inp.upper() in ['A', 'B']) and (exc in range(0, 2)):
            self.inst.write('DIOCUR? ' + inp.upper() + ',' + str(exc))
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B and exc must be 0 or 1.')
            
    def get_diode_excite(self, inp):
        if inp == -1:
            self.values['both_diode_excitation_parameters'] = list()
            for i in ['A', 'B']:
                self.values['diode_excitation_parameter_' + i.lower()] = str(self.inst.query('DIOCUR? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_diode_excitation_parameters'].append(self.values['diode_excitation_parameter_' + i.lower()])
            return self.values['both_diode_excitation_parameters']
        if inp.upper() in['A', 'B']:
            self.values['diode_excitation_parameter_' + inp.lower()] = str(self.inst.query('DIOCUR? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['diode_excitation_parameter_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def set_display_field(self, field, source, unit):
        if (field == -1) and (source in range(0, 7)) and (unit in range(1, 7)):
            for i in range(1, 5):
                self.inst.write('DISPFLD ' + str(i) + ',' + str(source) + ',' + str(unit))
                time.sleep(0.05)
            return self.get_display_field(-1)             
        if (field in range(1, 5)) and (source in range(0, 7)) and (unit in range(1, 7)):
            self.inst.write('DISPFLD ' + str(field) + ',' + str(source) + ',' + str(unit))
            time.sleep(0.05)
            return self.get_display_field(field)            
        else:
            raise ValueError('Incorrect input. Field and item must be between 1 and 4, source must be between 0 and 6, and unit must be between 1 and 6.')
            
    def get_display_field(self, field):
        if field == -1:
            self.values['all_display_fields'] = list()
            for i in range (1, 5):
                self.values['display_field_' + str(i)] = str(self.inst.query('DISPFLD? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_display_fields'].append(self.values['display_field_' + str(i)])
            return self.values['all_display_fields']
        if field in range(1, 5):
            self.values['display_field_' + str(field)] = str(self.inst.query('DISPFLD? ' + str(field))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['display_field_' + str(field)]
        else:
            raise ValueError('Incorrect input. Field must be -1 or between 1 and 4.')
            
    def set_display_setup(self, mode):
        if mode in range(0, 8):
            self.inst.write('DISPLAY ' + str(mode))
            time.sleep(0.05)
            return self.get_display_setup(self)
        else:
            raise ValueError('Incorrect input. Mode must be between 0 and 7.')
            
    def get_display_setup(self):
        self.values['display_setup'] = str(self.inst.query('DISPLAY?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['display_setup']

    def set_emul(self, mode, pid):
        if mode in range(0, 3) and (pid in range(0, 2)):
            self.inst.write('EMUL ' + str(mode) + ',' + str(pid))
            time.sleep(0.05)
            return self.get_emul()
        else:
            raise ValueError('Incorrect input. Input must be either 0 or 1.')
            
    def get_emul(self):
        self.values['emul'] = str(self.inst.query('EMUL?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['emul']

    def set_filter(self, inp, io, points, window):
        if (inp == -1) and (io in range(0, 2)) and (points in range(2, 65)) (window in range(1, 11)):
            for i in ['A', 'B']:
                self.inst.write('FILTER ' + i + ',' + str(io) + ',' + str(points) + ',' + str(window))
                time.sleep(0.05)
            return self.get_filter(-1)
        if (inp.upper() in ['A','B']) and (io in range(0, 2)) and (points in range(2, 65)) (window in range(1, 11)):
            self.inst.write('FILTER ' + str(inp).upper() + ',' + str('io') + ',' + str(points) + ',' + str(window))
            time.sleep(0.05)
            return self.get_filter(inp)
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B, io must be 0 or 1, points must be between 2 and 64, and window must be between 1 and 10.')
            
    def get_filter(self, inp):
        if inp == -1:
            self.values['both_filters'] = list()
            for i in ['A','B']:
                self.values['filter_' + i.lower()] = str(self.inst.query('FILTER? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_filters'].append(self.values['filter_' + i.lower()])
            return self.values['both_filters']
        if inp.upper() in ['A','B']:
            self.values['filter_' + inp.lower()] = str(self.inst.query('FILTER? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['filter_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B')
            
    def get_heater_percent(self, out):
        if out == -1:
            self.values['both_heater_percents'] = list()
            for i in range(1, 3):
                self.values['heater_' + str(i) + '_percent'] = str(self.inst.query('HTR? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_heater_percents'].append(self.values['heater_' + str(i) + '_percent'])
            return self.values['both_heater_percents']
        if out in range(1, 3):
            self.values['heater_' + str(out) + '_percent'] = str(self.inst.query('HTR? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['heater_' + str(out) + '_percent']
        else:
            raise ValueError('Incorrect input. Input must be either 1 or 2.')
            
    def setup_heater(self, out, ty, res, maxc, maxu, po):
        if (out == -1) and (ty in range(0, 2)) and (res in range(1, 3)) and (maxc in range(0,5)) and (po in range(1, 3)):
            if (maxc == 0):
                for i in range(1, 3):
                    self.inst.write('HTRSET ' + str(i) + ',' + str(ty) + ',' + str(res) + ',' + str(maxc) + ',' + str(maxu) + ',' + str(po))
                    time.sleep(0.05)
            if (maxc != 0):
                for i in range(1, 3):
                    self.inst.write('HTRSET ' + str(i) + ',' + str(ty) + ',' + str(res) + ','  + str(maxu) + ',' + str(po))
                    time.sleep(0.05)
            return self.get_setup_heater(-1)
        if (out in range(1, 3)) and (ty in range(0, 2)) and (res in range(1, 3)) and (maxc in range(0,5)) and (po in range(1, 3)):
            if (maxc == 0):
                self.inst.write('HTRSET ' + str(out) + str(i) + ',' + str(ty) + ',' + str(res) + ',' + str(maxc) + ',' + str(maxu) + ',' + str(po))
                time.sleep(0.05)
            if (maxc != 0):
                self.inst.write('HTRSET ' + str(out) + ',' + str(ty) + ',' + str(res) + ','  + str(maxu) + ',' + str(po))
                time.sleep(0.05)
            return self.get_setup_heater(out)
        else:
            raise ValueError('Incorrect input. Refer to the manual for the proper parameters.')
            
    def get_setup_heater(self, out):
        if out == -1:
            self.values['all_heater_setups'] = list()
            for i in range(1, 3):
                self.values['heater_setup_' + str(i)] = str(self.inst.query('HTRSET? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_heater_setups'].append(self.values['heater_setup_' + str(i)])
            return self.values['all_heater_setups']
        if out in range(1, 3):
            self.values['heater_setup_' + str(out)] = str(self.inst.query('HTRSET? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['heater_setup_' + str(out)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
            
    def set_ieee(self, addr):
        if addr in range (1, 31):
            self.inst.write('IEEE ' + str(addr))
            time.sleep(0.05)
            return self.get_ieee()
        else:
            raise ValueError('Incorrect input. Input must be between 1 and 30.')
        
    def get_ieee(self):
        self.values['ieee'] = str(self.inst.query('IEEE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ieee']

    def set_curve_num(self, inp, num):
        if (inp == -1) and (num in range(0, 60)):
            for i in ['A', 'B']:
                self.inst.write('INCRV ' + i + ',' + str(num))
                time.sleep(0.05)
            return self.get_curve_num(-1)
        if (inp.upper() in ['A','B']) and (num in range(0, 60)):
            self.inst.write('INCRV ' + str(inp).upper() + ',' + str(num))
            time.sleep(0.05)
            return self.get_curve_num(str(inp).upper())
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B and num must be between 0 and 59.')
            
    def get_curve_num(self, inp):
        if inp == -1:
            self.values['both_curve_numbers'] = list()
            for i in ['A','B']:
                self.values['curve_number_' + i.lower()] = str(self.inst.query('INCRV? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_curve_numbers'].append(self.values['curve_number_' + i.lower()])
            return self.values['both_curve_numbers']
        if inp.upper() in ['A','B']:
            self.values['curve_number_' + inp.lower()] = str(self.inst.query('INCRV? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_number_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B')
            
    def set_sensor_name(self, inp, name):
        if (inp in ['A', 'B']) and (len(name) in range(1, 16)):
            self.inst.write('INNAME ' + str(inp) + str(name))
            time.sleep(0.05)
            return self.get_sensor_name()
        else:
            raise ValueError('Incorrect input. Inp must be A or B and the name must be between 1 and 15 characters.')
            
    def get_sensor_name(self, inp):
        if inp == -1:
            self.values['both_sensor_names'] = list()
            for i in ['A', 'B']:
                self.values['sensor_' + i.lower() + '_name'] = str(self.inst.query('INNAME? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_sensor_names'].append(self.values['sensor_' + i.lower() + '_name'])
            return self.values['both_sensor_names']
        if inp.upper() in ['A', 'B']:
            self.values['sensor_' + inp.lower() + '_name'] = str(self.inst.query('INNAME? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['sensor_' + inp.lower() + '_name']
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def set_intype(self, inp, sen, autorange, ran, comp, unit):
        if inp == -1:
            if (sen in range(0, 5)) and (autorange == 1) and (comp in range(0, 2)) and (unit in range(1, 4)):
                for i in ['A', 'B']:
                    self.inst.write('INTYPE ' + i + ',' + str(sen) + ',1,' + str(comp) + ',' + str(unit))
                    time.sleep(0.05)
                return self.get_intype(-1)
            if (sen in range(0, 5)) and (autorange == 0) and (comp in range(0, 2)) and (unit in range(1, 4)):
                if (sen == 1) and (ran in range(0, 2)):
                    for i in ['A', 'B']:
                        self.inst.write('INTYPE ' + i + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit))
                        time.sleep(0.05)
                    return self.get_intype(-1)
                if (sen == 2) and (ran in range(0, 7)):
                    for i in ['A', 'B']:
                        self.inst.write('INTYPE ' + i + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit))
                        time.sleep(0.05)
                    return self.get_intype(-1)
                if (sen == 3) and (ran in range(0, 9)):
                    for i in ['A', 'B']:
                        self.inst.write('INTYPE ' + i + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit))
                        time.sleep(0.05)
                    return self.get_intype(-1)
                if (sen == 4) and (ran == 0):
                    for i in ['A', 'B']:
                        self.inst.write('INTYPE ' + i + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit))
                        time.sleep(0.05)
                    return self.get_intype(-1)
        if inp.upper() in ['A', 'B']:
            if (sen in range(0, 5)) and (autorange == 1) and (comp in range(0, 2)) and (unit in range(1, 4)):
                self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',1,' + str(comp) + ',' + str(unit))
                time.sleep(0.05)
                return self.get_intype(inp)
            if (sen in range(0, 5)) and (autorange == 0) and (comp in range(0, 2)) and (unit in range(1, 4)):
                if (sen == 1) and (ran in range(0, 2)):
                    self.inst.write(self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit)))
                    time.sleep(0.05)
                    return self.get_intype(inp)
                if (sen == 2) and (ran in range(0, 7)):
                    self.inst.write(self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit)))
                    time.sleep(0.05)
                    return self.get_intype(inp)
                if (sen == 3) and (ran in range(0, 9)):
                    self.inst.write(self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit)))
                    time.sleep(0.05)
                    return self.get_intype(inp)
                if (sen == 4) and (ran == 0):
                    self.inst.write(self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit)))
                    time.sleep(0.05)
                    return self.get_intype(inp)
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_intype(self, inp):
        if inp == -1:
            self.values['both_intypes'] = list()
            for i in ['A','B']:
                self.values['instype_' + i.lower()] = str(self.inst.query('INTYPE? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_intypes'].append(self.values['instype_' + i.lower()])
            return self.values['both_intypes']
        if inp.upper() in ['A','B']:
            self.values['intype_' + str(inp).lower()] = str(self.inst.query('INTYPE? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['intype_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B.')
            
    def get_temp(self, inp):
        if inp == -1:
            self.values['both_temperatures'] = list()
            for i in ['A','B']:
                self.values['temperature_' + i.lower()] = str(self.inst.query('KRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_temperatures'].append(self.values['temperature_' + i.lower()])
            return self.values['both_temperatures']
        if inp.upper() in ['A','B']:
            self.values['temperature_' + inp.lower()] = str(self.inst.query('KRDG? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['temperature_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B.')
            
    def set_leds(self, offon):
        if offon in range(0, 2):
            self.inst.write('LEDS ' + str(offon))
            time.sleep(0.05)
            return self.get_leds()
        else:
            raise ValueError('Incorrect input. Input must be either 0 or 1.')
            
    def get_leds(self):
        self.values['leds'] = str(self.inst.query('LEDS?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['leds']

    def set_lock(self, state, code):
        if (state in range (0, 2)):
            self.inst.write('LOCK ' + str(state) + ',' + str(code))
            time.sleep(0.05)
            return self.get_lock()
        else:
            raise ValueError('Incorrect input. State must be 0 or 1 and code must be between 000 and 999.')
            
    def get_lock(self):
        self.values['lock'] = str(self.inst.query('LOCK?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['lock']

    def get_mdat(self, inp):
        if inp == -1:
            self.values['both_mdats'] = list()
            for i in ['A', 'B']:
                self.values['mdat_' + i.lower()] = str(self.inst.query('MDAT? ' + i.upper())).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mdats'].append(self.values['mdat_' + i.lower()])
            return self.values['both_mdats']
        if inp.upper() in ['A', 'B']:
            self.values['mdat_' + inp.lower()] = str(self.inst.query('MDAT? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mdat_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B.')
            
    def reset_mnmx(self):
        self.inst.write('MNMXRST')
        time.sleep(0.05)
        return 'Minimum and maximum function reset.'
        
    def set_mode(self, mode):
        if mode in range(0, 3):
            self.inst.write('MODE ' + str(mode))
            time.sleep(0.05)
            return self.get_mode()
        else:
            raise ValueError('Incorrect input. Input must be 0, 1, or 2.')
            
    def get_mode(self):
        self.values['mode'] = str(self.inst.query('MODE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['mode']

    def set_mout(self, loop, val):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('MOUT ' + str(i) + ',' + str(val))
                time.sleep(0.05)                
            return self.get_mout(-1)
        if loop in range(1, 3):
            self.inst.write('MOUT ' + str(loop) + str(val))
            time.sleep(0.05)
            return self.get_mout(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_mout(self, loop):
        if loop == -1:
            self.values['both_mouts'] = list()
            for i in range(1, 3):
                self.values['mout_' + str(i)] = str(self.inst.query('MOUT? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mouts'].append(self.values['mout_' + str(i)])
            return self.values['both_mouts']
        if loop in range(1, 3):
            self.values['mout_' + str(loop)] = str(self.inst.query('MOUT? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mout_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
        
    def get_opst(self):
        self.values['operational_status_query'] = str(self.inst.query('OPST?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['operational_status_query']

    def set_opste(self, bit):
        self.inst.write('OPSTE ' + str(bit))
        time.sleep(0.05)
        return self.get_opste()
        
    def get_opste(self):
        self.values['operational_status_enable_query'] = str(self.inst.query('OPSTE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['operational_status_enable_query']

    def get_opstr(self):
        self.values['operational_status_register'] = str(self.inst.query('OPSTR?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['operational_status_register']

    def set_outmode(self, out, mode, inp, power):
        if (out == -1) and (mode in range(0, 5)) and (inp == -1) and (power in range(0, 2)):
            for i in range(1, 3):
                for x in ['A', 'B']:
                    self.inst.write('OUTMODE ' + str(i) + ',' + str(mode) + ',' + inp + ',' + str(power))
            return self.get_outmode(-1)
        if (out == -1) and (mode in range(0, 5)) and ((inp == 0) or (inp.upper() in ['A', 'B'])) and (power in range(0, 2)):
            if inp in ['A', 'B']:
                inp = inp.upper()
            for i in range(1, 3):
                self.inst.write('OUTMODE ' + str(i) + ',' + str(mode) + ',' + str(inp) + ',' + str(power))
                time.sleep(0.05)
                return self.get_outmode(-1)
        if (out in range(1, 3)) and (mode in range(0, 5)) and (inp == -1) and (power in range(0, 2)):
            for i in ['A', 'B']:
                self.inst.write('OUTMODE ' + str(out) + ',' + str(mode) + ',' + i + ',' + str(power))
                time.sleep(0.05)
                return self.get_outmode(out)
        if (out in range(1, 3)) and (mode in range(0, 5)) and ((inp == 0) or (inp.upper() in ['A', 'B'])) and (power in range(0, 2)):
            if inp.upper() in ['A', 'B']:
                inp = inp.upper()
            self.inst.write('OUTMODE ' + str(out) + ',' + str(mode) + ',' + str(inp) + ',' + str(power))
            time.sleep(0.05)
            return self.get_outmode(out)
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_outmode(self, out):
        if out == -1:
            self.values['both_outmodes'] = list()
            for i in range(1, 3):
                self.values['outmode_' + str(i)] = str(self.inst.query('OUTMODE? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_outmodes'].append(self.values['outmode_' + str(i)])
            return self.values['both_outmodes']
        if out in range(1, 3):
            self.values['outmode_' + str(out)] = str(self.inst.query('OUTMODE? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['outmode_' + str(out)]
        else:
            raise ValueError('Incorrect input. Input must be either 1 or 2.')
            
    def set_pid(self, loop, p, i, d):
        """
        Setting resolution is less than 6 digits indicated.
        """
        if (loop == -1) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            for i in range(1, 3):
                self.inst.write('PID ' + str(i) + ',' + str(p) + ',' + str(i) + ',' + str(d))
                time.sleep(0.05)
            return self.get_pid(-1)
        if (loop in range(1,3)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            self.inst.write('PID ' + str(loop) + ',' + str(p) + ',' + str(i) + ',' + str(d))
            time.sleep(0.05)
            return self.get_pid(loop)
        else:
            raise ValueError('Incorrect input. Refer to manual for proper parameters.')
            
    def get_pid(self, loop):
        if loop == -1:
            self.values['both_pids'] = list()
            for i in range(1, 3):
                self.values['pid_' + str(i)] = str(self.inst.query('PID? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_pids'].append(self.values['pid_' + str(i)])
            return self.values['both_pids']
        if loop in range(1, 3):
            self.values['pid_' + str(loop)] = str(self.inst.query('PID? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['pid_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_polarity(self, pol):
        if pol in range(0, 2):
            self.inst.write('POLARITY 2,' + str(pol))
            time.sleep(0.05)
            return self.get_polarity()
        else:
            raise ValueError('Incorrect input. Polarity must be 0 or 1.')
            
    def get_polarity(self):
        self.values['polarity'] = str(self.inst.query('POLARITY?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['polarity']

    def set_ramp(self, loop, io, rate):
        if (loop == -1) and (io in range(1, 3)) and (rate <= 100 and rate >= 0.1):
            for i in range(1, 3):
                self.inst.write('RAMP ' + str(i) + ',' + str(io) + ',' + str(rate))
                time.sleep(0.05)
            return self.get_ramp(-1)
        if (loop in range(1, 3)) and (io in range(1, 3)) and (rate <= 100 and rate >= 0.1):
            self.inst.write('RAMP ' + str(loop) + ',' + str(io) + ',' + str(rate))
            time.sleep(0.05)
            return self.get_ramp(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2, io must be 1 or 2, and rate between 0 and 100.')
            
    def get_ramp(self, loop):
        if loop == -1:
            self.values['both_ramps'] = list()
            for i in range(1, 3):
                self.values['ramp_' + str(i)] = str(self.inst.query('RAMP? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ramps'].append(self.values['ramp_' + str(i)])
            return self.values['both_ramps']
        if loop in range(1, 3):
            self.values['ramp_' + str(loop)] = str(self.inst.query('RAMP? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['ramp_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_rampst(self, loop):
        if loop == -1:
            self.values['both_rampsts'] = list()
            for i in range (1, 3):
                self.values['rampst_' + str(i)] = str(self.inst.query('RAMPST? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_rampsts'].append(self.values['rampst_' + str(i)])
            return self.values['both_rampsts']
        if loop in range (1, 3):
            self.values['rampst_' + str(loop)] = str(self.inst.query('RAMPST? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['rampst_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_range(self, out, ran):
        if (out == -1) and (ran in range(0, 4)):
            for i in range(1, 3):
                self.inst.write('RANGE ' + str(i) + ',' + str(ran))
                time.sleep(0.05)
            return self.get_range(-1)
        if (out in range(1, 3)) and (ran in range(0, 4)):
            self.inst.write('RANGE ' + str(out) + str(ran))
            time.sleep(0.05)
            return self.get_range(out)
        else:
            raise ValueError('Incorrect input. Out must be -1, 1, or 2 and range must be between 0 and 3.')
            
    def get_range(self, out):
        if out == -1:
            self.values['both_ranges'] = list()
            for i in range(1, 3):
                self.values['range_' + str(i)] = str(self.inst.query('RANGE? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ranges'].append(self.values['range_' + str(i)])
            return self.values['both_ranges']
        if out in range(1, 3):
            self.values['range_' + str(out)] = str(self.inst.query('RANGE? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['range_' + str(out)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
            
    def get_input_reading(self, inp):
        if inp == -1:
            self.values['both_input_readings'] = list()
            for i in ['A', 'B']:
                self.values['input_reading_' + i.lower()] = str(self.inst.query('RDGST? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_input_readings'].append(self.values['input_reading_' + i.lower()])
            return self.values['both_input_readings']
        if inp.upper() in ['A', 'B']:
            self.values['input_reading_' + inp.lower()] = str(self.inst.query('RDGST? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['input_reading_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.') 
            
    def set_relay(self, relay, mode, inp, alrm):
        if (relay == -1) and (mode in range(0, 3)) and (inp in ['A', 'B']) and (alrm in range(0, 3)):
            for i in range(1, 3):
                self.inst.write('RELAY ' + str(i) + ',' + str(mode) + ',' + str(inp) + ',' + str(alrm))
                time.sleep(0.05)
            return self.get_relay(-1)
        if (relay in range(1, 3)) and (mode in range(0, 3)) and (inp in ['A', 'B']) and (alrm in range(0, 3)):
            self.inst.write('RELAY ' + str(relay) + ',' + str(mode) + ',' + str(inp) + ',' + str(alrm))
            time.sleep(0.05)
            return self.get_relay(inp)
        else:
            raise ValueError('Incorrect input. Relay must be -1, 1, or 2, mode must be between 0 and 2, inp must be A or B, and alrm must be between 0 and 2.')
            
    def get_relay(self, num):
        if num == -1:
            self.values['both_relays'] = list()
            for i in range(1, 3):
                self.values['relay_' + str(i)] = str(self.inst.query('RELAY? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_relays'].append(self.values['relay_' + str(i)])
            return self.values['both_relays']
        if num in range(1, 3):
            self.values['relay_' + str(num)] = str(self.inst.query('RELAY? ' + str(num))).replace('\r\n','')
            return self.values['relay_' + str(num)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
    def get_relay_status(self, hilo):
        if hilo == -1:
            self.values['both_relay_statuses'] = list()
            for i in range(1, 3):
                self.values['relay_status_' + str(i)] = str(self.inst.query('RELAYST? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_relay_statuses'].append(self.values['relay_status_' + str(i)])
            return self.values['both_relay_statuses']
        if hilo in range(1, 3):
            self.values['relay_status_' + str(hilo)] = str(self.inst.query('RELAYST?')).replace('\r\n','')
            time.sleep(0.05)
            return self.values['relay_status_' + str(hilo)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')

    def gen_softcal(self, std, dest, sn, t1, u1, t2, u2, t3, u3):
        if (std in [1, 6, 7]) and (dest in range(21, 60)) and (len(sn) in range(0, 11)):
            self.inst.write('SCAL ' + str(std) + ',' + str(dest) + ',' + str(dest) + ',' + str(sn) + ',' + str(t1) + ',' + str(u1) + ',' + str(t2) + ',' + str(u2) + ',' + str(t3) + ',' + str(u3))
            time.sleep(0.05)
            return 'Set SoftCal curve.'
        else:
            raise ValueError('Incorrect input. std must be 1, 6, or 7, dest must be between 21 and 59, and sn must be of a length of 10 or less.')
            
    def set_setpoint(self, loop, value):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('SETP ' + str(i) + ',' + str(value))
                time.sleep(0.05)
            return self.get_setpoint(-1)
        if loop in range(1, 3):
            self.inst.write('SETP ' + str(loop) + ',' + str(value))
            time.sleep(0.05)
            return self.get_setpoint(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_setpoint(self, loop):
        if loop == -1:
            self.values['both_setpoints'] = list()
            for i in range(1, 3):
                self.values['setpoint_' + str(i)] = str(self.inst.query('SETP? ' + str(i))).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_setpoints'].append(self.values['setpoint_' + str(i)])
            return self.values['both_setpoints']
        if loop in range(1, 3):
            self.values['setpoint_' + str(loop)] = str(self.inst.query('SETP? ' + str(loop))).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['setpoint_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_srdg(self, inp):
        if inp == -1:
            self.values['both_sensor_unit_inputs'] = list()
            for i in ['A','B']:
                self.values['sensor_unit_input_' + i.lower()] = str(self.inst.query('SRDG? ' + i.upper())).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_sensor_unit_inputs'].append(self.values['sensor_unit_input_' + i.lower()])
            return self.values['both_sensor_unit_inputs']
        if inp.upper() in ['A', 'B']:
            self.values['sensor_unit_input_' + inp.lower()] = str(self.inst.query('SRDG? ' + inp.upper())).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['sensor_unit_input_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def get_thermocouple(self):
        self.values['thermocouple_junction_temperature'] = str(self.inst.query('TEMP?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['thermocouple_junction_temperature']

    def set_tlimit(self, inp, lim):
        if (inp == -1):
            for i in ['A', 'B']:
                self.inst.write('TLIMIT ' + i + ',' + str(lim))
                time.sleep(0.05)
            return self.get_tlimit(-1)
        if inp.upper() in ['A', 'B']:
            self.inst.write('TLIMIT ' + inp.upper() + ',' + str(lim))
            return self.get_tlimit(-1)
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B')
            
    def get_tlimit(self, inp):
        if inp == -1:
            self.values['both_temperature_limits'] = list()
            for i in ['A', 'B']:
                self.values['temperature_limit_' + i.lower()] = str(self.inst.query('TLIMIT? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_temperature_limits'].append(self.values['temperature_limit_' + i.lower()])
            return self.values['both_temperature_limits']
        if inp.upper() in ['A', 'B']:
            self.values['temperature_limit_' + inp.lower()] = str(self.inst.query('TLIMIT? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['temperature_limit_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, or B.')
            
    def is_tuning(self):
        self.values['tune_test'] = str(self.inst.query('TUNEST?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['tune_test']

    def set_warmup(self, con, per):
        if (con in range(0, 2)):
            self.inst.write('WARMUP 2,' + str(con) + ',' + str(per))
            return self.get_warmup()
        else:
            raise ValueError('Incorrect input. Control must be 0 or 1.')
            
    def get_warmup(self):
        self.values['warmup_supply_parameter'] = str(self.inst.query('WARMUP? 2')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['warmup_supply_parameter']

    def set_zone(self, loop, zone, setp, p, i, d, mout, ran, rate):
        if (loop == -1) and (zone in range(1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0) and (rate <= 100 and rate >= 0.1):
            for i in range(1, 3):
                self.inst.write('ZONE ' + str(i) + ',' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1' + str(rate))
                time.sleep(0.05)
            return self.get_zone(-1)
        if (loop == 1) and (zone in range(1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0) and (rate <= 100 and rate >= 0.1):
            if ran in range(0, 3):
                self.inst.write('ZONE 1,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + str(ran) + str(rate))
            time.sleep(0.05)
            return self.get_zone(1)
        if (loop == 2) and (zone in range(1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0) and (rate <= 100 and rate >= 0.1):
            self.inst.write('ZONE 2,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1' + str(rate))
            time.sleep(0.05)
            return self.get_zone(2)
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_zone(self, loop, zone):
        if (loop == -1) and (zone == -1):
            self.values['both_control_loops_all_zones'] = list()
            for i in range(1, 3):
                for x in range(1, 11):
                    self.values['control_loop_' + str(i) + '_zone_' + str(x)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(x))).replace('\r\n', '')
                    time.sleep(0.05)
                    self.values['both_control_loops_all_zones'].append(self.values['control_loop_' + str(i) + '_zone_' + str(x)])
            return self.values['both_control_loops_all_zones']
        if (loop == -1) and (zone in range(1, 11)):
            self.values['both_control_loops_zone_' + str(zone)] = list()
            for i in range(1, 3):
                self.values['control_loop_' + str(i) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(zone))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_control_loops_zone_' + str(zone)].append(self.values['control_loop_' + str(i) + '_zone_' + str(zone)])
            return self.values['both_control_loops_zone_' + str(zone)]
        if (loop in range(1, 3)) and (zone in range(1,11)):
            self.values['control_loop_' + str(loop) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(loop) + ',' + str(zone))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['control_loop_' + str(loop) + '_zone_' + str(zone)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2 and zone between 1 and 10.')
            
    def start_logging_csv(self, interval=5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_csv, 'interval', seconds=interval)
        sched.start()
        
    def lakeshore_logging_csv(self, path=None, filename=None, units = 'K'): #Check against 335
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.csv'
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        number = self.get_number()
        out = self.get_temp(-1)
        time = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        time.replace(',','').replace(' ','')
        out[0] = str(out[0])
        out[1] = str(out[1])
        out.append(str(self.get_heater_percent(1)))
        out.append(str(self.get_heater_percent(2)))
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, time)
        out.insert(0, date)
        setpoint = str(self.get_setpoint(-1)).replace(',','|')
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        header = 'date,time, seconds, hours, Channel A, \'A\' units, setpoints, Lakeshore Number, Channel B, \'B\' units, heater percent 1, heater percent 2\n'
        with open(os.path.join(path,filename), 'a') as f: #creates .csv file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .csv file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write(header) #if .csv file is empty, header is written in
                f.close()
        out = str(out).replace('[', '').replace(']', '').replace('\'','')
        with open(os.path.join(path,filename), 'a') as f:
            f.write(str(out)) #Writes lakeshore information to .csv file
            f.write('\n')
            f.close()
        
    def start_logging_txt(self, interval=5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_txt, 'interval', seconds=interval)
        sched.start()
                
    def lakeshore_logging_txt(self, path=None,filename=None, units = 'K'): #Check against 335
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.txt'
        number = self.get_number()
        header = 'date\t\t time\t\t seconds\t hours\t\t Channel A\t \'A\' units\t setpoints\t Lakeshore Number\t Channel B\t \'B\' units\t heater percent 1\t heater percent 2\n'
        out = self.get_temp(-1)
        time = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        time.replace(',','').replace(' ','')
        out.append(self.get_heater_percent(1))
        out.append(self.get_heater_percent(2))
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, time)
        out.insert(0, date)
        setpoint = str(self.get_setpoint(-1)).replace(',','|').replace('+','')
        setpoint = setpoint.split()
        for i in range(0, 2):
            setpoint[i] = float(setpoint[i].replace('|','').replace('[','').replace('\'','').replace(']',''))
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        
        try:
            out[4] = '%.3f' % float(out[4])
        except (IndexError):
            out[4] = 0.000
        try:
            out[8] = '%.3f' % float(out[8])
        except(IndexError):
            out[8] = 0.000

        # Aligns columns
        out[2] = str(out[2]) + '         '
        out[4] = str(out[4]) + '        '
        out[6] = '        ' + str(out[6])
        out[8] = str(out[8]) + '    '
        out[9] = str(out[9]) + '        '
        out[10] = str(out[10]) + '        '
        out[11] = '        ' + str(out[11])

        with open(os.path.join(path,filename), 'a') as f: #creates .txt file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .txt file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write('{:<20}'.format(header)) #if .txt file is empty, header is written in
                f.close()
        with open(os.path.join(path,filename), 'a') as f:
            out = str(out).replace('[','').replace(']','').replace('\'','').replace(',','\t')+'\n'
            f.write('{:^30}'.format(out))
            f.close()
            
    def pause_logging(self):
        sched.pause()
        return 'Logging paused'
        
    def resume_logging(self):
        sched.resume()
        return 'Logging resumed'
        
    def stop_logging(self):
        sched.shutdown()
        return 'Logging stopped'
            
class lakeshore336:
    def __init__(self, asrl, timeout = 2 * 1000, autodetect = False):
        self.rm = pyvisa.ResourceManager()
        #auto connects to first lakeshore it finds
        """
        if autodetect:
            for res in self.rm.list_resources():
                self.rm.open_resource(res)
                self.inst.write('*IDN')
                info = self.inst.read()
                if str(info[0]).upper() == 'LSCI':
                    break
                if str(info[0]).upper() != 'LSCI':
                    continue
        else:
            self.inst = self.rm.open_resource(asrl)
        """
        self.inst = self.rm.open_resource(asrl)
        self.inst.data_bits = 7
        self.inst.parity = Parity(1)
        self.inst.baud_rate = 57600
        self.inst.term_chars = '\n'
        self.values = dict()
        global sched
        sched = BackgroundScheduler()
        
    def close(self):
        self.inst.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        
    def read(self):
        print self.inst.read()
        
    def clear_interface(self):
        """
        Clears the bits in the Status Byte Register and Standard Event Status Register and 
        terminates all pending operations. Clears the interface, but not the controller.
        """
        self.inst.write('*CLS')
        time.sleep(0.05)
        
    def set_ese(self, ese):
        """
        Each bit is assigned a bit weighting and represents the enable/disable mask 
        of the corresponding event flag bit in the Standard Event Status Register.
        """
        self.inst.write('*ESE ' + str(ese))
        time.sleep(0.05)
        return self.get_ese()
        
    def get_ese(self):
        self.values['ese'] = str(self.inst.query('*ESE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ese']
        
    def get_esr(self):
        self.values['esr'] = str(self.inst.query('*ESR?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['esr']

    def get_info(self):
        self.values['idn'] = str(self.inst.query('*IDN?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['idn']

    def get_number(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['number'] = str(out[2])
        return self.values['number']

    def get_model(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['model'] = str(out[1])
        return self.values['model']

    def get_manu(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['manu'] = str(out[0])
        return self.values['manu']

    def set_rst(self):
        """
        Sets controller parameters to power-up settings.
        """
        self.inst.write('*RST')
        time.sleep(0.05)
        return 'Controller set to power-up settings.'
        
    def set_sre(self, sre):
        """
        Each bit has a bit weighting and represents the enable/disable mask of
        the corresponding status flag bit in the Status Byte Register.
        """
        self.inst.write('*SRE ' + str(sre))
        time.sleep(0.05)
        return self.get_sre()
        
    def get_sre(self):
        self.values['sre'] = str(self.inst.query('*SRE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['sre']

    def get_stb(self):
        """
        Acts like a serial poll, but does not reset the register to all zeros. 
        The integer returned represents the sum of the bit weighting of the 
        status flag bits that are set in the Status Byte Register.
        """
        self.values['stb'] = str(self.inst.query('*STB?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['stb']

    def is_error(self):
        self.values['tst'] = str(self.inst.query('*TST?')).replace('\r\n','').replace('\t','')
        if self.values['tst'] is '':
            self.values['tst'] = 0
        time.sleep(0.05)
        return self.values['tst']

    def set_alarm(self, inp, offon, hi, lo, db, le, aud, vis):
        if (inp == -1) and (offon in range(0, 2)) and (le in range(0, 2)) and (aud in range(0, 2)) and (vis in range(0, 2)):
            for i in ['A', 'B', 'C', 'D']:
                self.inst.write('ALARM ' + i + ',' + str(offon) + ',' + str(hi) + ',' + str(lo) + ',' + str(db) + ',' + str(le) + ',' + str(aud) + ',' + str(vis))
                time.sleep(0.05)
            return self.get_alarm(-1)
        if (inp.upper() in ['A', 'B','C','D']) and (offon in range(0, 2)) and (le in range(0, 2)) and (aud in range(0, 2)) and (vis in range(0, 2)):
            self.inst.write('ALARM ' + inp.upper() + ',' + str(offon) + ',' + str(hi) + ',' + str(lo) + ',' + str(db) + ',' + str(le) + ',' + str(aud) + ',' + str(vis))
            time.sleep(0.05)
            return self.get_alarm(inp)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_alarm(self, inp):
        if inp == -1:
            self.values['both_alarms'] = list()
            for i in ['A', 'B','C','D']:
                self.values['alarm_' + i.lower()] = str(self.inst.query('ALARM? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_alarms'].append(self.values['alarm_' + i.lower()])
            return self.values['both_alarms']
        if inp.upper() in ['A', 'B','C','D']:
            self.values['alarm_' + inp.lower()] = str(self.inst.query('ALARM? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['alarm_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.')
            
    def get_alarmst(self, inp):
        if inp == -1:
            self.values['both_alarm_statuses'] = list()
            for i in ['A', 'B','C','D']:
                self.values['alarm_status_' + i.lower()] = str(self.inst.query('ALARMST? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_alarm_statuses'].append(self.values['alarm_status_' + i.lower()])
            return self.values['both_alarm_statuses']
        if inp.upper() in ['A', 'B','C','D']:
            self.values['alarm_status_' + inp.lower()] = str(self.inst.query('ALARMST? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['alarm_status_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.')
            
    def reset_alarmst(self):
        self.inst.write('ALARMST')
        time.sleep(0.05)
        return 'High and low status alarms cleared.'
        
    def set_analog(self, out, inp, unit, hi, lo, pol):
        if (out ==-1) and (inp in range(0, 9)) and (unit in range(1, 4)) and (pol in range(0, 2)):
            for i in range(3, 5):
                self.inst.write('ANALOG ' + str(out) + ',' + str(inp) + ',' + str(unit) + ',' + str(hi) + ',' + str(lo) + ',' + str(pol))
                time.sleep(0.05)
            return self.get_analog(-1) 
        if (out in range(3, 5)) and (inp in range(0, 9)) and (unit in range(1, 4)) and (pol in range(0, 2)):
            self.inst.write('ANALOG ' + str(out) + ',' + str(inp) + ',' + str(unit) + ',' + str(hi) + ',' + str(lo) + ',' + str(pol))
            time.sleep(0.05)
            return self.get_analog(out)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_analog(self, out):
        if out == -1:
            self.values['all_analogs'] = list()
            for i in range(3, 5):
                self.values['analog_' + str(i)] = str(self.inst.query('ANALOG? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_analogs'].append(self.values['analog_' + str(i)])
            return self.values['all_analogs']
        if out in range(3, 5):
            self.values['analog_' + str(out)] = str(self.inst.query('ANALOG? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['analog_' + str(out)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 3, or 4.')
            
    def get_aout(self, out):
        if out == -1:
            self.values['both_analog_outputs'] = list()
            for i in range(3, 5):
                self.values['analog_output_' + str(i)] = str(self.inst.query('AOUT? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_analog_outputs'].append(self.values['analog_output_' + str(i)])
            return self.values['both_analog_outputs']
        if out in range(3, 5):
            self.values['analog_output_' + str(out)] = str(self.inst.query('AOUT? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['analog_output_' + str(out)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 3, or 4.')
            
    def autotune(self, out, mode):
        if (out == -1) and (mode in range(0, 3)):
            for i in range(1, 3):
                self.inst.write('ATUNE ' + str(i) + ',' + str(mode))
                time.sleep(0.05)
            return 'Autotune complete.'
        if (out in range(1, 3)) and (mode in range(0, 3)):
            self.inst.write('ATUNE ' + str(i) + ',' + str(mode))
            return 'Autotune complete.'
        else:
            raise ValueError('Incorrect input. Output must be 1 or and mdoe must be between 0 and 2.')
            
    def set_brightness(self, brit):
        if brit in range(1, 33):
            self.inst.write('BRIGT ' + str(brit))
            time.sleep(0.05)
            return self.get_brightness()
        else:
            raise ValueError('Incorrect input. Brit must be an integer between 1 and 32.')
            
    def get_brightness(self):
        self.values['brightness'] = str(self.inst.query('BRIGT?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['brightness']

    def get_crdg(self, ab):
        if ab == -1:
            self.values['both_crdgs'] = list()
            for i in ['A','B', 'C', 'D']:
                self.values['crdg_'+ i.lower()] = str(self.inst.query('CRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_crdgs'].append(self.values['crdg_'+ i.lower()])
            return self.values['both_crdgs']
        if ab.upper() in ['A','B', 'C', 'D']:
            self.values['crdg_' + ab.lower()] = str(self.inst.query('CRDG? ' + str(ab).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['crdg_' + ab.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.')
            
    def delete_curve(self, curve):
        if curve == -1:
            for i in range(21, 60):
                self.inst.write('CRVDEL ' + str(i))
            return self.get_curve(-1)
        if curve in range(21, 60):
            self.inst.write('CRVDEL ' + str(curve))
            return self.get_curve(curve)
        else:
            raise ValueError('Incorrect input. Curve must be between 21 and 59 or be -1.')
            
    def get_curve(self, curve):
        if curve == -1:
            self.values['all_curves'] = list()
            for i in range(1, 60):
                self.values['curve_' + str(i)] = str(self.inst.query('CRVHDR? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curves'].append(self.values['curve_' + str(i)])
            return self.values['all_curves']
        if curve in range(1, 60):
            self.values['curve_' + str(curve)] = str(self.inst.query('CRVHDR? ' + str(curve))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_' + str(curve)]
        else:
            raise ValueError('Incorrect input. Curve must be between 1 and 59 or be -1.')
            
    def set_curve_header(self, curve, name, sn, frmt, lim_val, coe):
        """
        Configures the user curve header.
        """
        if (curve in range(21, 60)) and (len(name) in range(1, 16)) and (len(sn) in range(1, 11)) and (frmt in range(1,5)) and (coe == 1 or 2):
            self.inst.write('CRVHDR ' + str(curve) + ',' + str(name) + ',' + str(sn) + ',' + str(frmt) + ',' + str(lim_val) + ',' + str(coe))
            time.sleep(0.05)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')

    def set_curve_point(self, curve, index, unit, temp):
        """
        Configures a user curve data point.
        """
        if (curve in range(21, 60)) and (index in range(1, 201)) and (len(unit) in range(1, 7)) and (temp in range(1, 7)):
            self.inst.write('CRVPT ' + str(curve) + ',' + str(index) + ',' + str(unit) + ',' + str(temp))
            time.sleep(0.05)
            return self.get_curve_point(curve, index)
        else:
            raise ValueError('Incorrect input. Refer to the manual for proper parameters.')
            
    def get_curve_point(self, curve, index):
        if (curve == -1) and (index == -1):
            self.values['all_curve_points'] = list()
            for i in range(1, 60):
                for x in range(1, 201):
                    self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(x))).replace('\r\n','')
                    time.sleep(0.05)
                    self.values['all_curve_points'].append(self.values['curve_point_at_' + str(curve) + '_' + str(index)])
            return self.values['all_curve_points']
        if (curve == -1) and (index in range(1, 201)):
            self.values['all_curve_points_for_index_' + str(index)] = list()
            for i in range(1,60):
                self.values['curve_point_at_' + str(i) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(i) + ',' + str(index))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_for_index_' + str(index)].append(self.values['curve_point_at_' + str(i) + '_' + str(index)])
            return self.values['all_curve_points_for_index_' + str(index)]
        if (curve in range(1, 60)) and (index == -1):
            self.values['all_curve_points_at_curve_' + str(curve)] = list()
            for i in range(1, 201):
                self.values['curve_point_at_' + str(curve) + '_' + str(i)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_curve_points_at_curve_' + str(curve)].append(self.values['curve_point_at_' + str(curve) + '_' + str(i)])
            return self.values['all_curve_points_at_curve_' + str(curve)]
        if (curve in range(1, 60)) and (index in range(1, 201)):
            self.values['curve_point_at_' + str(curve) + '_' + str(index)] = str(self.inst.query('CRVPT? ' + str(curve) + ',' + str(index))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_point_at_' + str(curve) + '_' + str(index)]
        else:
            raise ValueError('Incorrect input. Curve must be between 21 and 41 and index must be between 1 and 200.')
            
    def set_default(self):
        """
        Sets all configuration values to factory defaults and resets the instrument.
        """
        self.inst.write('DFTL 99')
        time.sleep(0.05)
        return 'Configuration settings set to default values.'
        
    def set_diode_excite(self, inp, exc):
        if (inp == -1) and (exc in range(0, 2)):
            for i in ['A', 'B', 'C', 'D']:
                self.inst.write('DIOCUR ' + i + ',' + str(exc))
                time.sleep(0.05)
            return self.get_diode_excite(-1)
        if (inp.upper() in ['A', 'B', 'C', 'D']) and (exc in range(0, 2)):
            self.inst.write('DIOCUR? ' + inp.upper() + ',' + str(exc))
            return self.get_diode_excite(inp)
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B and exc must be 0 or 1.')
            
    def get_diode_excite(self, inp):
        if inp == -1:
            self.values['all_diode_excitation_parameters'] = list()
            for i in ['A', 'B', 'C', 'D']:
                self.values['diode_excitation_parameter_' + i.lower()] = str(self.inst.query('DIOCUR? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_diode_excitation_parameters'].append(self.values['diode_excitation_parameter_' + i.lower()])
            return self.values['all_diode_excitation_parameters']
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.values['diode_excitation_parameter_' + inp.lower()] = str(self.inst.query('DIOCUR? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['diode_excitation_parameter_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.')
            
    def set_display_field(self, field, inp, unit):
        if (field == -1) and (inp in range(0, 9)) and (unit in range(1, 6)):
             for i in range(1, 9):
                 self.inst.write('DISPFLD ' + str(i) + ',' + str(inp) + ',' + str(unit))
                 time.sleep(0.05)
             return self.get_display_field(-1)
        if (field in range(1, 9)) and (inp in range(0, 9)) and (unit in range(1, 6)):
            self.inst.write('DISPFLD ' + str(field) + ',' + str(inp) + ',' + str(unit))
            time.sleep(0.05)
            return self.get_display_field(field)            
        else:
            raise ValueError('Incorrect input. Field and item must be between 1 and 4 and source is between 1 and 3 if item is 1 or 2.')
            
    def get_display_field(self, field):
        if field == -1:
            self.values['all_display_fields'] = list()
            for i in range(1, 9):
                self.values['display_field_' + str(i)] = str(self.inst.query('DISPFLD? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_display_fields'].append(self.values['display_field_' + str(i)])
            return self.values['all_display_fields']
        if field in range(1, 9):
            self.values['display_field_' + str(field)] = str(self.inst.query('DISPFLD? ' + str(field))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['display_field_' + str(field)]
        else:
            raise ValueError('Incorrect input. Field must be -1 or between 1 and 8.')
            
    def set_display_setut(self, mode):
        if mode in range(0, 8):
            self.inst.write('DISPLAY ' + str(mode))
            time.sleep(0.05)
            return self.get_display_setup(self)
        else:
            raise ValueError('Incorrect input. Mode must be between 0 and 7.')
            
    def get_display_setup(self):
        self.values['display_setup'] = str(self.inst.query('DISPLAY?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['display_setup']

    def set_filter(self, inp, io, points, window):
        if (inp == -1) and (io in range(0, 2)) and (points in range(2, 65)) and (window in range(1, 11)):
            for i in ['A', 'B', 'C', 'D']:
                self.inst.write('FILTER ' + str(inp) + ',' + str(io) + ',' + str(points) + ',' + str(window))
                time.sleep(0.05)
            return self.get_filter(-1)
        if (inp.upper() in ['A','B', 'C', 'D']) and (io in range(0, 2)) and (points in range(2, 65)) (window in range(1, 11)):
            self.inst.write('FILTER ' + str(inp).upper() + ',' + str('io') + ',' + str(points) + ',' + str(window))
            time.sleep(0.05)
            return self.get_filter(inp)
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, B, C, or D, io must be 0 or 1, points must be between 2 and 64, and window must be between 1 and 10.')
            
    def get_filter(self, inp):
        if inp == -1:
            self.values['both_filters'] = list()
            for i in ['A', 'B', 'C', 'D']:
                self.values['filter_' + i.lower()] = str(self.inst.query('FILTER? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_filters'].append(self.values['filter_' + i.lower()])
            return self.values['both_filters']
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.values['filter_' + inp.lower()] = str(self.inst.query('FILTER? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['filter_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D')
            
    def get_heater_percent(self, out):
        if out == -1:
            self.values['both_heater_percents'] = list()
            for i in range(1, 3):
                self.values['heater_' + str(i) + '_percent'] = str(self.inst.query('HTR? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_heater_percents'].append(self.values['heater_' + str(i) + '_percent'])
            return self.values['both_heater_percents']
        if out in range(1, 3):
            self.values['heater_' + str(out) + '_percent'] = str(self.inst.query('HTR? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['heater_' + str(out) + '_percent']
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
            
    def setup_heater(self, out, ty, res, maxc, maxu, po):
        if (out == -1) and (ty in range(0, 2)) and (res in range(1, 3)) and (maxc in range(0,5)) and (po in range(1, 3)):
            if (maxc == 0):
                for i in range(1, 3):
                    self.inst.write('HTRSET ' + str(i) + ',' + str(ty) + ',' + str(res) + ',' + str(maxc) + ',' + str(maxu) + ',' + str(po))
                    time.sleep(0.05)
            if (maxc != 0):
                for i in range(1, 3):
                    self.inst.write('HTRSET ' + str(i) + ',' + str(ty) + ',' + str(res) + ','  + str(maxu) + ',' + str(po))
                    time.sleep(0.05)
            return self.get_setup_heater(-1)
        if (out in range(1, 3)) and (ty in range(0, 2)) and (res in range(1, 3)) and (maxc in range(0,5)) and (po in range(1, 3)):
            if (maxc == 0):
                self.inst.write('HTRSET ' + str(out) + str(i) + ',' + str(ty) + ',' + str(res) + ',' + str(maxc) + ',' + str(maxu) + ',' + str(po))
                time.sleep(0.05)
            if (maxc != 0):
                self.inst.write('HTRSET ' + str(out) + ',' + str(ty) + ',' + str(res) + ','  + str(maxu) + ',' + str(po))
                time.sleep(0.05)
            return self.get_setup_heater(out)
        else:
            raise ValueError('Incorrect input. Refer to the manual for the proper parameters.')
            
    def get_setup_heater(self, out):
        if out == -1:
            self.values['all_heater_setups'] = list()
            for i in range(1, 3):
                self.values['heater_setup_' + str(i)] = str(self.inst.query('HTRSET? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_heater_setups'].append(self.values['heater_setup_' + str(i)])
            return self.values['all_heater_setups']
        if out in range(1, 3):
            self.values['heater_setup_' + str(out)] = str(self.inst.query('HTRSET? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['heater_setup_' + str(out)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
            
    def set_ieee(self, addr):
        if addr in range(1, 31):
            self.inst.write('IEEE ' + str(addr))
            time.sleep(0.05)
            return self.get_ieee()
        else:
            raise ValueError('Incorrect input. Input must be between 1 and 30.')
        
    def get_ieee(self):
        self.values['ieee'] = str(self.inst.query('IEEE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['ieee']

    def set_curve_num(self, inp, num):
        if (inp == -1) and (num in range(0, 60)):
            for i in ['A', 'B']:
                self.inst.write('INCRV ' + i + ',' + str(num))
                time.sleep(0.05)
            return self.get_curve_num(-1)
        if (inp.upper() in ['A','B']) and (num in range(0, 60)):
            self.inst.write('INCRV ' + str(inp).upper() + ',' + str(num))
            time.sleep(0.05)
            return self.get_curve_num(str(inp).upper())
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, or B and num must be between 0 and 59.')
            
    def get_curve_num(self, inp):
        if inp == -1:
            self.values['both_curve_numbers'] = list()
            for i in ['A', 'B', 'C', 'D']:
                self.values['curve_number_' + i.lower()] = str(self.inst.query('INCRV? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_curve_numbers'].append(self.values['curve_number_' + i.lower()])
            return self.values['both_curve_numbers']
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.values['curve_number_' + inp.lower()] = str(self.inst.query('INCRV? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['curve_number_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, B, C, or D.')
            
    def set_sensor_name(self, inp, name):
        if (inp in ['A', 'B', 'C', 'D']) and (len(name) in range(1, 16)):
            self.inst.write('INNAME ' + str(inp) + str(name))
            time.sleep(0.05)
            return self.get_sensor_name()
        else:
            raise ValueError('Incorrect input. Inp must be A, B, C, or D and the name must be between 1 and 15 characters.')
            
    def get_sensor_name(self, inp):
        if inp == -1:
            self.values['both_sensor_names'] = list()
            for i in ['A', 'B', 'C', 'D']:
                self.values['sensor_' + i.lower() + '_name'] = str(self.inst.query('INNAME? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_sensor_names'].append(self.values['sensor_' + i.lower() + '_name'])
            return self.values['both_sensor_names']
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.values['sensor_' + inp.lower() + '_name'] = str(self.inst.query('INNAME? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['sensor_' + inp.lower() + '_name']
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.')
            
    def select_interface(self, face):
        if face in range(0, 3):
            self.inst.write('INTSEL ' + str(face))
            time.sleep(0.05)
            return self.get_interface(face)
        else:
            raise ValueError('Incorrect input. Input must be between 0, 1, or 2.')
            
    def get_interface(self):
        self.values['interface'] = str(self.inst.query('INTSEL?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['interface']
            
    def set_intype(self, inp, sen, autorange, ran, comp, unit):
        if inp == -1:
            if (sen in range(0, 5)) and (autorange == 1) and (comp in range(0, 2)) and (unit in range(1, 4)):
                for i in ['A', 'B', 'C', 'D']:
                    self.inst.write('INTYPE ' + i + ',' + str(sen) + ',1,' + str(comp) + ',' + str(unit))
                    time.sleep(0.05)
                return self.get_intype(-1)
            if (sen in range(0, 5)) and (autorange == 0) and (comp in range(0, 2)) and (unit in range(1, 4)):
                if (sen == 1) and (ran in range(0, 2)):
                    for i in ['A', 'B', 'C', 'D']:
                        self.inst.write('INTYPE ' + i + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit))
                        time.sleep(0.05)
                    return self.get_intype(-1)
                if (sen == 2) and (ran in range(0, 7)):
                    for i in ['A', 'B', 'C', 'D']:
                        self.inst.write('INTYPE ' + i + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit))
                        time.sleep(0.05)
                    return self.get_intype(-1)
                if (sen == 3) and (ran in range(0, 9)):
                    for i in ['A', 'B', 'C', 'D']:
                        self.inst.write('INTYPE ' + i + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit))
                        time.sleep(0.05)
                    return self.get_intype(-1)
                if (sen == 4) and (ran == 0):
                    for i in ['A', 'B', 'C', 'D']:
                        self.inst.write('INTYPE ' + i + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit))
                        time.sleep(0.05)
                    return self.get_intype(-1)
        if inp.upper() in ['A', 'B', 'C', 'D']:
            if (sen in range(0, 5)) and (autorange == 1) and (comp in range(0, 2)) and (unit in range(1, 4)):
                self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',1,' + str(comp) + ',' + str(unit))
                time.sleep(0.05)
                return self.get_intype(inp)
            if (sen in range(0, 5)) and (autorange == 0) and (comp in range(0, 2)) and (unit in range(1, 4)):
                if (sen == 1) and (ran in range(0, 2)):
                    self.inst.write(self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit)))
                    time.sleep(0.05)
                    return self.get_intype(inp)
                if (sen == 2) and (ran in range(0, 7)):
                    self.inst.write(self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit)))
                    time.sleep(0.05)
                    return self.get_intype(inp)
                if (sen == 3) and (ran in range(0, 9)):
                    self.inst.write(self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit)))
                    time.sleep(0.05)
                    return self.get_intype(inp)
                if (sen == 4) and (ran == 0):
                    self.inst.write(self.inst.write('INTYPE ' + inp.upper() + ',' + str(sen) + ',0,' + str(ran) + ',' + str(comp) + ',' + str(unit)))
                    time.sleep(0.05)
                    return self.get_intype(inp)
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_intype(self, inp):
        if inp == -1:
            self.values['both_intypes'] = list()
            for i in ['A', 'B', 'C', 'D']:
                self.values['instype_' + i.lower()] = str(self.inst.query('INTYPE? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_intypes'].append(self.values['instype_' + i.lower()])
            return self.values['both_intypes']
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.values['intype_' + str(inp).lower()] = str(self.inst.query('INTYPE? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['intype_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, B, C, or D.')
            
    def get_last_key_press(self):
        """
        Returns a number descriptor of the last key pressed since the last KEYST?.
        Returns “21” after initial power-up. Returns “00” if no key pressed since last query.
        """
        self.values['last_key_press'] = str(self.inst.query('KEYST?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['last_key_press']

    def get_temp(self, inp):
        if inp == -1:
            self.values['both_temperatures'] = list()
            for i in ['A','B', 'C', 'D']:
                self.values['temperature_' + i.lower()] = str(self.inst.query('KRDG? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_temperatures'].append(self.values['temperature_' + i.lower()])
            return self.values['both_temperatures']
        if inp.upper() in ['A','B', 'C', 'D']:
            self.values['temperature_' + inp.lower()] = str(self.inst.query('KRDG? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['temperature_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Inp must be -1, A, B, C, or D.')
            
    def set_leds(self, offon):
        if offon in range(0, 2):
            self.inst.write('LEDS ' + str(offon))
            time.sleep(0.05)
            return self.get_leds()
        else:
            raise ValueError('Incorrect input. Input must be either 0 or 1.')
            
    def get_leds(self):
        self.values['leds'] = str(self.inst.query('LEDS?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['leds']
            
    def set_lock(self, state, code):
        if (state in range(0, 2)) and (code in range(0, 1000)):
            self.inst.write('LOCK ' + str(state) + ',' + str(code))
            time.sleep(0.05)
            return self.get_lock()
        else:
            raise ValueError('Incorrect input. State must be 0 or 1 and code must be between 000 and 999.')
            
    def get_lock(self):
        self.values['lock'] = str(self.inst.query('LOCK?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['lock']

    def get_mdat(self, inp):
        if inp == -1:
            self.values['both_mdats'] = list()
            for i in ['A', 'B', 'C', 'D']:
                self.values['mdat_' + i.lower()] = str(self.inst.query('MDAT? ' + i.upper())).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mdats'].append(self.values['mdat_' + i.lower()])
            return self.values['both_mdats']
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.values['mdat_' + inp.lower()] = str(self.inst.query('MDAT? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mdat_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.')
            
    def reset_mnmx(self):
        self.inst.write('MNMXRST')
        time.sleep(0.05)
        return 'Minimum and maximum function reset.'
        
    def set_mode(self, mode):
        if mode in range(0, 3):
            self.inst.write('MODE ' + str(mode))
            time.sleep(0.05)
            return self.get_mode()
        else:
            raise ValueError('Incorrect input. Input must be 0, 1, or 2.')
            
    def get_mode(self):
        self.values['mode'] = str(self.inst.query('MODE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['mode']

    def set_mout(self, loop, val):
        if loop == -1:
            for i in range(1, 3):
                self.inst.write('MOUT ' + str(i) + ',' + str(val))
            return self.get_mout(-1)
        if loop in range(1, 3):
            self.inst.write('MOUT ' + str(loop) + str(val))
            time.sleep(0.05)
            return self.get_mout(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_mout(self, loop):
        if loop == -1:
            self.values['both_mouts'] = list()
            for i in range(1, 5):
                self.values['mout_' + str(i)] = str(self.inst.query('MOUT? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_mouts'].append(self.values['mout_' + str(i)])
            return self.values['both_mouts']
        if loop in range(1, 5):
            self.values['mout_' + str(loop)] = str(self.inst.query('MOUT? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['mout_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, 2, 3, or 4.')
            
    def set_net(self, dhcp, auip, ip, sub, gate, pri, sec, host, domain, desc):
        if (dhcp in range(0, 2)) and (auip in range(0, 2)) and (len(host) in range(1, 16)) and (len(domain) in range(1, 65)) and (len(desc) in range(1, 33)):
            self.inst.write('NET ' + str(dhcp) + ',' + str(auip) + ',' + str(ip) + ',' + str(sub) + ',' + str(gate) + ',' + str(pri) + ',' + str(sec) + ',' + str(host) + ',' + str(domain) + ',' + str(desc))
            time.sleep(0.05)
            return self.get_net()
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_net(self):
        self.values['network_settings'] = str(self.inst.query('NET?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['network_settings']

    def get_net_id(self):
        self.values['network_configuration'] = str(self.inst.query('NETID?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['network_configuration']

    def get_opst(self):
        self.values['operational_status_query'] = str(self.inst.query('OPST?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['operational_status_query']

    def set_opste(self, bit):
        self.inst.write('OPSTE ' + str(bit))
        time.sleep(0.05)
        return self.get_opste()
        
    def get_opste(self):
        self.values['operational_status_enable_query'] = str(self.inst.query('OPSTE?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['operational_status_enable_query']

    def get_opstr(self):
        self.values['operational_status_register'] = str(self.inst.query('OPSTR?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['operational_status_register']

    def set_outmode(self, out, mode, inp, power):
        if (out == -1) and (mode in range(0, 6)) and (inp == -1) and (power in range(0, 2)):
            for i in range(1, 5):
                for x in range(0, 9):
                    self.inst.write('OUTMODE ' + str(i) + ',' + str(mode) + ',' + str(x) + ',' + str(power))
                    time.sleep(0.05)
            return self.get_outmode(-1)
        if (out == -1) and (mode in range(0, 6)) and (inp in range(0, 9)) and (power in range(0, 2)):
            for i in range(1, 5):
                self.inst.write('OUTMODE ' + str(i) + ',' + str(mode) + ',' + str(inp) + ',' + str(power))
                time.sleep(0.05)
                return self.get_outmode(-1)
        if (out in range(1, 5)) and (mode in range(0, 6)) and (inp == -1) and (power in range(0, 2)):
            for i in range(0, 9):
                self.inst.write('OUTMODE ' + str(out) + ',' + str(mode) + ',' + str(i) + ',' + str(power))
                time.sleep(0.05)
                return self.get_outmode(out)
        if (out in range(1, 5)) and (mode in range(0, 6)) and (inp in range(0, 9)) and (power in range(0, 2)):
            self.inst.write('OUTMODE ' + str(out) + ',' + str(mode) + ',' + str(inp) + ',' + str(power))
            time.sleep(0.05)
            return self.get_outmode(out)
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_outmode(self, out):
        if out == -1:
            self.values['all_outmodes'] = list()
            for i in range(1, 5):
                self.values['outmode_' + str(i)] = str(self.inst.query('OUTMODE? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_outmodes'].append(self.values['outmode_' + str(i)])
            return self.values['all_outmodes']
        if out in range(1, 5):
            self.values['outmode_' + str(out)] = str(self.inst.query('OUTMODE? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['outmode_' + str(out)]
        else:
            raise ValueError('Incorrect input. Input must be either -1, 1, 2, 3, or 4.')
            
    def set_pid(self, loop, p, i, d):
        """
        Setting resolution is less than 6 digits indicated.
        """
        if (loop == -1) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            for i in range(1, 3):
                self.inst.write('PID ' + str(i) + ',' + str(p) + ',' + str(i) + ',' + str(d))
                time.sleep(0.05)
            return self.get_pid(-1)
        if (loop in range(1,3)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            self.inst.write('PID ' + str(loop) + ',' + str(p) + ',' + str(i) + ',' + str(d))
            time.sleep(0.05)
            return self.get_pid(loop)
        else:
            raise ValueError('Incorrect input. Refer to manual for proper parameters.')
            
    def get_pid(self, loop):
        if loop == -1:
            self.values['both_pids'] = list()
            for i in range(1, 3):
                self.values['pid_' + str(i)] = str(self.inst.query('PID? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_pids'].append(self.values['pid_' + str(i)])
            return self.values['both_pids']
        if loop in range(1, 3):
            self.values['pid_' + str(loop)] = str(self.inst.query('PID? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['pid_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')

    def set_ramp(self, loop, io, rate):
        if (loop == -1) and (io in range(1, 3)) and (rate <= 100 and rate >= 0.1):
            for i in range(1, 3):
                self.inst.write('RAMP ' + str(i) + ',' + str(io) + ',' + str(rate))
                time.sleep(0.05)
            return self.get_ramp(-1)
        if (loop in range(1, 3)) and (io in range(1, 3)) and (rate <= 100 and rate >= 0.1):
            self.inst.write('RAMP ' + str(loop) + ',' + str(io) + ',' + str(rate))
            time.sleep(0.05)
            return self.get_ramp(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2, io must be 1 or 2, and rate between 0 and 100.')
            
    def get_ramp(self, loop):
        if loop == -1:
            self.values['both_ramps'] = list()
            for i in range(1, 3):
                self.values['ramp_' + str(i)] = str(self.inst.query('RAMP? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ramps'].append(self.values['ramp_' + str(i)])
            return self.values['both_ramps']
        if loop in range(1, 3):
            self.values['ramp_' + str(loop)] = str(self.inst.query('RAMP? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['ramp_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def get_rampst(self, loop):
        if loop == -1:
            self.values['both_rampsts'] = list()
            for i in range(1, 3):
                self.values['rampst_' + str(i)] = str(self.inst.query('RAMPST? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_rampsts'].append(self.values['rampst_' + str(i)])
            return self.values['both_rampsts']
        if loop in range(1, 3):
            self.values['rampst_' + str(loop)] = str(self.inst.query('RAMPST? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['rampst_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_range(self, out, ran):
        if (out == -1) and (ran in range(1, 4)):
            for i in range(1, 3):
                self.inst.write('RANGE ' + str(i) + ',' + str(ran))
                time.sleep(0.05)
            for i in range(3, 5):
                self.inst.write('RANGE 1,' + str(ran))
                time.sleep(0.05)
            return self.get_range(-1)
        if (out == -1) and (ran == 0):
            for i in range(3, 5):
                self.inst.write('RANGE 0,' + str(ran))
                time.sleep(0.05)
        if (out in range(1, 5)) and (ran in range(0, 4)):
            self.inst.write('RANGE ' + str(out) + str(ran))
            time.sleep(0.05)
            return self.get_range(out)
        else:
            raise ValueError('Incorrect input. Out must be -1, 1, 2, 3, or 4 and range must be between 0 and 3.')
            
    def get_range(self, out):
        if out == -1:
            self.values['both_ranges'] = list()
            for i in range(1, 5):
                self.values['range_' + str(i)] = str(self.inst.query('RANGE? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ranges'].append(self.values['range_' + str(i)])
            return self.values['both_ranges']
        if out in range(1, 5):
            self.values['range_' + str(out)] = str(self.inst.query('RANGE? ' + str(out))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['range_' + str(out)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, 2, 3, or 4.')
            
    def get_input_reading(self, inp):
        if inp == -1:
            self.values['both_input_readings'] = list()
            for i in ['A', 'B', 'C', 'D']:
                self.values['input_reading_' + i.lower()] = str(self.inst.query('RDGST? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_input_readings'].append(self.values['input_reading_' + i.lower()])
            return self.values['both_input_readings']
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.values['input_reading_' + inp.lower()] = str(self.inst.query('RDGST? ' + str(inp).upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['input_reading_' + str(inp).lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.') 
            
    def set_relay(self, relay, mode, inp, alrm):
        if (relay == -1) and (mode in range(0, 3)) and (inp in ['A', 'B', 'C', 'D']) and (alrm in range(0, 3)):
            for i in range(1, 3):
                self.inst.write('RELAY ' + str(i) + ',' + str(mode) + ',' + str(inp) + ',' + str(alrm))
                time.sleep(0.05)
            return self.get_relay(-1)
        if (relay in range(1, 3)) and (mode in range(0, 3)) and (inp in ['A', 'B', 'C', 'D']) and (alrm in range(0, 3)):
            self.inst.write('RELAY ' + str(relay) + ',' + str(mode) + ',' + str(inp) + ',' + str(alrm))
            time.sleep(0.05)
            return self.get_relay(inp)
        else:
            raise ValueError('Incorrect input. Relay must be -1, 1, or 2, mode must be between 0 and 2, inp must be A or B, and alrm must be between 0 and 2.')
            
    def get_relay(self, num):
        if num == -1:
            self.values['both_relays'] = list()
            for i in range(1, 3):
                self.values['relay_' + str(i)] = str(self.inst.query('RELAY? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_relays'].append(self.values['relay_' + str(i)])
            return self.values['both_relays']
        if num in range(1, 3):
            self.values['relay_' + str(num)] = str(self.inst.query('RELAY? ' + str(num))).replace('\r\n','')
            return self.values['relay_' + str(num)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
            
    def get_relay_status(self, hilo):
        if hilo == -1:
            self.values['both_relay_statuses'] = list()
            for i in range(1, 3):
                self.values['relay_status_' + str(i)] = str(self.inst.query('RELAYST? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_relay_statuses'].append(self.values['relay_status_' + str(i)])
            return self.values['both_relay_statuses']
        if hilo in range(1, 3):
            self.values['relay_status_' + str(hilo)] = str(self.inst.query('RELAYST? ' + str(hilo))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['relay_status_' + str(hilo)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 1, or 2.')

    def gen_softcal(self, std, dest, sn, t1, u1, t2, u2, t3, u3):
        if (std in [1, 6, 7]) and (dest in range(21, 60)) and (len(sn) in range(0, 11)):
            self.inst.write('SCAL ' + str(std) + ',' + str(dest) + ',' + str(dest) + ',' + str(sn) + ',' + str(t1) + ',' + str(u1) + ',' + str(t2) + ',' + str(u2) + ',' + str(t3) + ',' + str(u3))
            time.sleep(0.05)
            return 'Set SoftCal curve.'
        else:
            raise ValueError('Incorrect input. std must be 1, 6, or 7, dest must be between 21 and 59, and sn must be of a length of 10 or less.')
            
    def set_setpoint(self, loop, value):
        if loop == -1:
            for i in range(1, 5):
                self.inst.write('SETP ', + str(i) + ',' + str(value))
                time.sleep(0.05)
            return self.get_setpoint(-1)
        if loop in range(1, 5):
            self.inst.write('SETP ' + str(loop) + ',' + str(value))
            time.sleep(0.05)
            return self.get_setpoint(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, 2, 3, or 4.')
            
    def get_setpoint(self, loop):
        if loop == -1:
            self.values['all_setpoints'] = list()
            for i in range(1, 5):
                self.values['setpoint_' + str(i)] = str(self.inst.query('SETP? ' + str(i))).replace('\r\n', '')
                time.sleep(0.05)
                self.values['all_setpoints'].append(self.values['setpoint_' + str(i)])
            return self.values['all_setpoints']
        if loop in range(1, 5):
            self.values['setpoint_' + str(loop)] = str(self.inst.query('SETP? ' + str(loop))).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['setpoint_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, 2, 3, or 4.')
            
    def get_srdg(self, inp):
        if inp == -1:
            self.values['both_sensor_unit_inputs'] = list()
            for i in ['A','B', 'C', 'D']:
                self.values['sensor_unit_input_' + i.lower()] = str(self.inst.query('SRDG? ' + i.upper())).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_sensor_unit_inputs'].append(self.values['sensor_unit_input_' + i.lower()])
            return self.values['both_sensor_unit_inputs']
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.values['sensor_unit_input_' + inp.lower()] = str(self.inst.query('SRDG? ' + inp.upper())).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['sensor_unit_input_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.')
            
    def get_thermocouple(self):
        self.values['thermocouple_junction_temperature'] = str(self.inst.query('TEMP?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['thermocouple_junction_temperature']

    def set_tlimit(self, inp, lim):
        if (inp == -1):
            for i in ['A', 'B', 'C', 'D']:
                self.inst.write('TLIMIT ' + i + ',' + str(lim))
                time.sleep(0.05)
            return self.get_tlimit(-1)
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.inst.write('TLIMIT ' + inp.upper() + ',' + str(lim))
            return self.get_tlimit(-1)
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.')
            
    def get_tlimit(self, inp):
        if inp == -1:
            self.values['all_temperature_limits'] = list()
            for i in ['A', 'B', 'C', 'D']:
                self.values['temperature_limit_' + i.lower()] = str(self.inst.query('TLIMIT? ' + i)).replace('\r\n','')
                time.sleep(0.05)
                self.values['all_temperature_limits'].append(self.values['temperature_limit_' + i.lower()])
            return self.values['all_temperature_limits']
        if inp.upper() in ['A', 'B', 'C', 'D']:
            self.values['temperature_limit_' + inp.lower()] = str(self.inst.query('TLIMIT? ' + inp.upper())).replace('\r\n','')
            time.sleep(0.05)
            return self.values['temperature_limit_' + inp.lower()]
        else:
            raise ValueError('Incorrect input. Input must be -1, A, B, C, or D.')
            
    def is_tuning(self):
        self.values['tune_test'] = str(self.inst.query('TUNEST?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['tune_test']

    def set_warmup(self, out, con, per):
        if (out == -1) and (con in range(0, 2)):
            for i in range(3, 5):
                self.inst.write('WARMUP ' + str(i) + ',' + str(con) + ',' + str(per))
                time.sleep(0.05)
            return self.get_warmup(-1)
        if (out in range(3, 5)) and (con in range(0, 2)):
            self.inst.write('WARMUP ' + str(out) + ',' + str(con) + ',' + str(per))
            return self.get_warmup(out)
        else:
            raise ValueError('Incorrect input. Output must be 3 or 4 and control must be 0 or 1.')
            
    def get_warmup(self, out):
        if out == -1:
            self.values['both_warmup_supply_parameters'] = list()
            for i in range(3, 5):
                self.values['warmup_supply_parameter_' + str(i)] = str(self.inst.query('WARMUP? ' + str(i))).replace('\r\n', '')
                time.sleep(0.05)
                self.values['both_warmup_supply_parameters'].append(self.values['warmup_supply_parameter_' + str(i)])
            return self.values['both_warmup_supply_parameters']
        if out in range(3, 5):
            self.values['warmup_supply_parameter_' + str(out)] = str(self.inst.query('WARMUP? ' + str(out))).replace('\r\n', '')
            time.sleep(0.05)
            return self.values['warmup_supply_parameter_' + str(out)]
        else:
            raise ValueError('Incorrect input. Input must be -1, 3, or 4.')

    def set_weblog(self, user, passw):
        if (len(user) in range(1, 16)) and (len(passw) in range(1, 16)):
            self.inst.write('WEBLOG ' + str(user) + ',' + str(passw))
            time.sleep(0.05)
            return self.get_weblog()
        else:
            raise ValueError('Incorrect input. The username and password length can\'t be greater than 15 characters.')
            
    def get_weblog(self):
        self.values['weblog'] = str(self.inst.query('WEBLOG?')).replace('\r\n', '')
        time.sleep(0.05)
        return self.values['weblog']

    def set_zone(self, loop, zone, setp, p, i, d, mout, ran, rate):
        if (loop == -1) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0) and (rate <= 100 and rate >= 0.1):
            for i in range(1, 3):
                self.inst.write('ZONE ' + str(i) + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1' + str(rate))
                time.sleep(0.05)
            return self.get_zone(-1)
        if (loop == 1) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0) and (rate <= 100 and rate >= 0.1):
            if ran in range(0, 3):
                self.inst.write('ZONE 1,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + str(ran) + str(rate))
            time.sleep(0.05)
            return self.get_zone(1)
        if (loop == 2) and (zone in range (1, 11)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0) and (mout <= 100 and mout >= 0) and (rate <= 100 and rate >= 0.1):
            self.inst.write('ZONE 2,' + str(zone) + ',' + str(p) + ',' + str(i) + ',' + str(d) + ',' + str(mout) + ',' + '1' + str(rate))
            time.sleep(0.05)
            return self.get_zone(2)
        else:
            raise ValueError('Incorrect input. Refer to the manual for correct parameters.')
            
    def get_zone(self, loop, zone):
        if (loop == -1) and (zone == -1):
            self.values['both_control_loops_all_zones'] = list()
            for i in range(1, 3):
                for x in range(1, 11):
                    self.values['control_loop_' + str(i) + '_zone_' + str(x)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(x))).replace('\r\n', '')
                    time.sleep(0.05)
                    self.values['both_control_loops_all_zones'].append(self.values['control_loop_' + str(i) + '_zone_' + str(x)])
            return self.values['both_control_loops_all_zones']
        if (loop == -1) and (zone in range(1, 11)):
            self.values['both_control_loops_zone_' + str(zone)] = list()
            for i in range (1, 3):
                self.values['control_loop_' + str(i) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(i) + ',' + str(zone))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_control_loops_zone_' + str(zone)].append(self.values['control_loop_' + str(i) + '_zone_' + str(zone)])
            return self.values['both_control_loops_zone_' + str(zone)]
            self.values['control_loop_1_zone_' + str(zone)] = self.inst.query('ZONE? 1,' + str(zone))
            time.sleep(0.05)
            self.values['control_loop_2_zone_' + str(zone)] = self.inst.query('ZONE? 2,' + str(zone))
            time.sleep(0.05)
            self.values['both_control_loops_zone_' + str(zone)] = self.values['control_loop_a_zone_' + str(zone)]
            return self.values['both_control_loops_zone_' + str(zone)]
        if (loop in range(1, 3)) and (zone in range(1,11)):
            self.values['control_loop_' + str(loop) + '_zone_' + str(zone)] = str(self.inst.query('ZONE? ' + str(loop) + ',' + str(zone))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['control_loop_' + str(loop) + '_zone_' + str(zone)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2 and zone between 1 and 10.')
        
    def start_logging_csv(self, interval=5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_csv, 'interval', seconds=interval)
        sched.start()
        
    def lakeshore_logging_csv(self, path=None, filename=None, units = 'K'): #Check against 335
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.csv'
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        number = self.get_number()
        out = self.get_temp(-1)
        time = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        time.replace(',','').replace(' ','')
        out[0] = str(out[0])
        out[1] = str(out[1])
        out[2] = str(out[2])
        out[3] = str(out[3])
        out.append(str(self.get_heater_percent(1)))
        out.append(str(self.get_heater_percent(2)))
        out.append(str(self.get_aout(3)))
        out.append(str(self.get_aout(4)))
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, time)
        out.insert(0, date)
        setpoint = str(self.get_setpoint(-1)).replace(',','|')
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        out.insert(11, units)
        out.insert(13, units)
        out[16] = str(out[16].replace('0,', '0 |')) #Replaces comma with bar to avoid cell errors
        out[17] = str(out[17].replace('0,', '0 |')) #Replaces comma with bar to avoid cell errors
        header = 'date,time, seconds, hours, Channel A, \'A\' units, setpoints, Lakeshore Number, Channel B, \'B\' units, Channel C, \'C\' units, Channel D, \'D\' Units, heater percent 1, heater percent 2, heater percent 3, heater percent 4\n'
        with open(os.path.join(path,filename), 'a') as f: #creates .csv file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .csv file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write(header) #if .csv file is empty, header is written in
                f.close()
        out = str(out).replace('[', '').replace(']', '').replace('\'','')
        with open(os.path.join(path,filename), 'a') as f:
            f.write(str(out)) #Writes lakeshore information to .csv file
            f.write('\n')
            f.close()
        
    def start_logging_txt(self, interval=5):
        global startTime
        startTime = time.time()
        sched.add_job(self.lakeshore_logging_txt, 'interval', seconds=interval)
        sched.start()
                
    def lakeshore_logging_txt(self, path=None,filename=None, units = 'K'): #Check against 335
        import time
        name = getpass.getuser()
        for i in ['a','b','f','n','r','t','v','ooo','xhh']:
            if name.startswith(i):
                name = '\\' + name
        date = datetime.datetime.now().strftime("%m/%d/%y")
        elapsedTime = int(time.time()) - int(startTime)
        hours = '{:.5f}'.format((elapsedTime / 3600.000))
        if path is None:
            path = 'C:\Users\\' + name + '\Documents\logs'
        if filename is None:
            filename = datetime.datetime.now().strftime("%Y_%m_%d") + '.txt'
        number = self.get_number()
        header = 'date\t\t time\t\t seconds\t hours\t\t Channel A\t \'A\' units\t setpoints\t\t\t Lakeshore Number\t Channel B\t \'B\' units\t Channel C\t \'C\' units\t Channel D\t \'D\' Units\t heater percent 1\t heater percent 2\t heater percent 3\t heater percent 4\n'
        out = self.get_temp(-1)
        time = str(datetime.datetime.now().strftime("%I:%M:%S %p"))
        time.replace(',','').replace(' ','')
        out.append(self.get_heater_percent(1))
        out.append(self.get_heater_percent(2))
        out.append(self.get_aout(3))
        out.append(self.get_aout(4))
        out.insert(0, hours)
        out.insert(0, elapsedTime)
        out.insert(0, time)
        out.insert(0, date)
        setpoint = str(self.get_setpoint(-1)).replace(',','|').replace('+','')
        setpoint = setpoint.split()
        for i in range(0, 4):
            setpoint[i] = float(setpoint[i].replace('|','').replace('[','').replace('\'','').replace(']',''))
        out.insert(5, setpoint)
        out.insert(5, units)
        out.insert(7, number)
        out.insert(9, units)
        out.insert(11, units)
        out.insert(13, units)
        
        try:
            out[4] = '%.3f' % float(out[4])
        except (IndexError):
            out[4] = 0.000
        try:
            out[8] = '%.3f' % float(out[8])
        except(IndexError):
            out[8] = 0.000
        try:
            out[10] = '%.3f' % float(out[10])
        except(IndexError):
            out[10] = 0.000
        try:
            out[12] = '%.3f' % float(out[12])
        except(IndexError):
            out[12] = 0.000
        try:
            out[14] = '%.3f' % float(out[14])
        except(IndexError):
            out[14] = 0.000
        try:
            out[15] = '%.3f' % float(out[15])
        except(IndexError):
            out[15] = 0.000

        # Aligns columns
        out[2] = str(out[2]) + '         '
        out[4] = str(out[4]) + '        '
        out[6] = '        ' + str(out[6])
        out[8] = str(out[8]) + '    '
        out[9] = str(out[9]) + '        '
        out[10] = str(out[10]) + '    '
        out[12] = '        ' + out[12] + '        '
        out[14] = '        ' + out[14] + '            '
        out[16] = str(out[16]).replace(',',' |')
        out[17] = str(out[17]).replace(',',' |')
        out[16] = '                ' + out[16] + '            '

        with open(os.path.join(path,filename), 'a') as f: #creates .txt file if it doesn't exist
            f.close()
        if os.stat(os.path.join(path, filename)).st_size == 0: #checks if .txt file is empty
            with open(os.path.join(path,filename), 'a') as f:
                f.write('{:<20}'.format(header)) #if .txt file is empty, header is written in
                f.close()
        with open(os.path.join(path,filename), 'a') as f:
            out = str(out).replace('[','').replace(']','').replace('\'','').replace(',','\t')+'\n'
            f.write('{:^30}'.format(out))
            f.close()
            
    def pause_logging(self):
        sched.pause()
        return 'Logging paused'
        
    def resume_logging(self):
        sched.resume()
        return 'Logging resumed'
        
    def stop_logging(self):
        sched.shutdown()
        return 'Logging stopped'
        
class lakeshore_gui(): #For general Lakeshore use
    def __init__(self, asrl, timeout = 2 * 1000, baud = 57600):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(asrl)
        self.inst.data_bits = 7
        self.inst.parity = Parity(1)
        if baud in [9600, 57600]:
            self.inst.baud_rate = baud #Can be configured to 9600 or 57600
        else:
            raise ValueError('Baud rate must be 9600 or 57600.')
        self.inst.term_chars = '\r'
        self.values = dict()
        
    def close(self):
        self.inst.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        
    def read(self):
        print self.inst.read()
        
    def get_info(self):
        self.values['idn'] = str(self.inst.query('*IDN?')).replace('\r\n','')
        time.sleep(0.05)
        return self.values['idn']

    def get_number(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['number'] = str(out[2])
        return self.values['number']

    def get_model(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['model'] = str(out[1])
        return self.values['model']

    def get_manu(self):
        out = (str(self.inst.query('*IDN?')).replace('\r\n','')).split(',')
        self.values['manufacturer'] = str(out[0])
        return self.values['manufacturer']

    def get_heater_percent(self, loop):
        if self.get_model() not in ['MODEL331s', 'MODEL331', 'MODEL332']:
            self.values['both_heater_percents'] = list()
            for i in range(1, 3):
                self.values['heater_percent_' + str(i)] = str(self.inst.query('HTR? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_heater_percents'].append(self.values['heater_percent_' + str(i)])
            return self.values['both_heater_percents']
        else:
            self.values['heater_1_percent'] = str(self.inst.query('HTR?')).replace('\r\n','')
            time.sleep(0.05)
            return self.values['heater_1_percent']

    def set_setpoint(self, loop, value):
        if self.get_model() == 'MODEL336':
            if loop == -1:
                for i in range(1, 5):
                    self.inst.write('SETP ', + str(i) + ',' + str(value))
                    time.sleep(0.05)
                return self.get_setpoint(-1)
            if loop in range(1, 5):
                self.inst.write('SETP ' + str(loop) + ',' + str(value))
                time.sleep(0.05)
                return self.get_setpoint(loop)
            else:
                raise ValueError('Incorrect input. Loop must be -1, 1, 2, 3, or 4.')
        else:
            if loop == -1:
                for i in range(1, 3):
                    self.inst.write('SETP ' + str(i) + ',' + str(value))
                    time.sleep(0.05)
                return self.get_setpoint(-1)
            if loop in range(1, 3):
                self.inst.write('SETP ' + str(loop) + ',' + str(value))
                time.sleep(0.05)
                return self.get_setpoint(loop)
            else:
                raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
                
    def get_setpoint(self, loop):
        if self.get_model() == 'MODEL 336':
            if loop == -1:
                self.values['all_setpoints'] = list()
                for i in range(1, 5):
                    self.values['setpoint_' + str(i)] = str(self.inst.query('SETP? ' + str(i))).replace('\r\n', '')
                    time.sleep(0.05)
                    self.values['all_setpoints'].append(self.values['setpoint_' + str(i)])
                return self.values['all_setpoints']
            if loop in range(1, 5):
                self.values['setpoint_' + str(loop)] = str(self.inst.query('SETP? ' + str(loop))).replace('\r\n', '')
                time.sleep(0.05)
                return self.values['setpoint_' + str(loop)]
            else:
                raise ValueError('Incorrect input. Loop must be -1, 1, 2, 3, or 4.')
        else:
            if loop == -1:
                self.values['both_setpoints'] = list()
                for i in range(1, 3):
                    self.values['setpoint_' + str(i)] = str(self.inst.query('SETP? ' + str(i))).replace('\r\n', '')
                    time.sleep(0.05)
                    self.values['both_setpoints'].append(self.values['setpoint_' + str(i)])
                return self.values['both_setpoints']
            if loop in range(1, 3):
                self.values['setpoint_' + str(loop)] = str(self.inst.query('SETP? ' + str(loop))).replace('\r\n', '')
                time.sleep(0.05)
                return self.values['setpoint_' + str(loop)]
            else:
                raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')

    def set_ramp(self, loop, rate):
        if (loop == -1) and (rate <= 100 and rate >= 0.1):
            for i in range(1, 3):
                self.inst.write('RAMP ' + str(i) + ',' + '1' + ',' + str(rate))
                time.sleep(0.05)
            return self.get_ramp(-1)
        if (loop in range(1, 3)) and (rate <= 100 and rate >= 0):
            self.inst.write('RAMP ' + str(loop) + ',' + '1' + ',' + str(rate))
            time.sleep(0.05)
            return self.get_ramp(loop)
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2 and rate between 0.1 and 100.')
            
    def get_ramp(self, loop):
        if loop == -1:
            self.values['both_ramps'] = list()
            for i in range(1, 3):
                self.values['ramp_' + str(i)] = str(self.inst.query('RAMP? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_ramps'].append(self.values['ramp_' + str(i)])
            return self.values['both_ramps']
        if loop in range(1, 3):
            self.values['ramp_' + str(loop)] = str(self.inst.query('RAMP? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['ramp_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_range(self, loop, ran):
        if self.get_model() == 'MODEL336':
            if (loop == -1) and (ran in range(1, 4)):
                for i in range(1, 3):
                    self.inst.write('RANGE ' + str(i) + ',' + str(ran))
                    time.sleep(0.05)
                for i in range(3, 5):
                    self.inst.write('RANGE 1,' + str(ran))
                    time.sleep(0.05)
                return self.get_range(-1)
            if (loop == -1) and (ran == 0):
                for i in range(3, 5):
                    self.inst.write('RANGE 0,' + str(ran))
                    time.sleep(0.05)
            if (loop in range(1, 5)) and (ran in range(0, 4)):
                self.inst.write('RANGE ' + str(loop) + str(ran))
                time.sleep(0.05)
                return self.get_range(loop)
        else:
            raise ValueError('Incorrect input. Out must be -1, 1, 2, 3, or 4 and range must be between 0 and 3.')
        if self.get_model() == 'MODEL325':
            if (loop == -1) and (ran in range(0, 2)):
                for i in range(1, 3):
                    self.inst.write('RANGE ' + str(i) + ',' + str(ran))
                    time.sleep(0.05)
                return self.get_range(-1)
            if (loop == 1) and (ran in range(0, 3)):
                self.inst.write('RANGE 1,' + str(ran))
                time.sleep(0.05)
                return self.get_range(1)
            if (loop == 2) and (ran in range(0, 2)):
                self.inst.write('RANGE 2,' + str(ran))
                time.sleep(0.05)
                return self.get_range(2)
            else:
                raise ValueError('Incorrect input. Range must be 0, 1, or 2 if loop is 1 or range must be 0 or 1 if loop is 2.')
        if self.get_model() in ['MODEL331s', 'MODEL331', 'MODEL332']:
            if ran in range(0, 4):
                self.inst.write('RANGE ' + str(ran))
                time.sleep(0.05)
            else:
                raise ValueError('Incorrect input. Range must be 0, 1, 2, or 3.')
        if self.get_model() == 'MODEL335':
            if (loop == -1) and (ran in range(0, 4)):
                for i in range(1, 3):
                    self.inst.write('RANGE ' + str(i) + ',' + str(ran))
                    time.sleep(0.05)
                return self.get_range(-1)
            if (loop in range(1, 3)) and (ran in range(0, 4)):
                self.inst.write('RANGE ' + str(loop) + str(ran))
                time.sleep(0.05)
                return self.get_range(loop)
            else:
                raise ValueError('Incorrect input. Out must be -1, 1, or 2 and range must be between 0 and 3.')
                
    def get_range(self, out):
        if self.get_model() == 'MODEL336':
            if out == -1:
                self.values['both_ranges'] = list()
                for i in range(1, 3):
                    self.values['range_' + str(i)] = str(self.inst.query('RANGE? ' + str(i))).replace('\r\n','')
                    time.sleep(0.05)
                    self.values['both_ranges'].append(self.values['range_' + str(i)])
                return self.values['both_ranges']
            if out in range(1, 3):
                self.values['range_' + str(out)] = str(self.inst.query('RANGE? ' + str(out))).replace('\r\n','')
                time.sleep(0.05)
                return self.values['range_' + str(out)]
            else:
                raise ValueError('Incorrect input. Input must be -1, 1, 2, 3, or 4.')
        if self.get_model() in ['MODEL325', 'MODEL335']:
            if out == -1:
                self.values['both_ranges'] = list()
                for i in range(1, 3):
                    self.values['range_' + str(i)] = str(self.inst.query('RANGE? ' + str(i))).replace('\r\n','')
                    time.sleep(0.05)
                    self.values['both_ranges'].append(self.values['range_' + str(i)])
                return self.values['both_ranges']
            if out in range(1, 3):
                self.values['range_' + str(out)] = str(self.inst.query('RANGE? ' + str(out))).replace('\r\n','')
                time.sleep(0.05)
                return self.values['range_' + str(out)]
            else:
                raise ValueError('Incorrect input. Input must be -1, 1, or 2.')
        else:
            self.values['range'] = str(self.inst.query('RANGE?')).replace('\r\n','')
            time.sleep(0.05)
            return self.values['range']

    def get_pid(self, loop):
        if loop == -1:
            self.values['both_pids'] = list()
            for i in range(1, 3):
                self.values['pid_' + str(i)] = str(self.inst.query('PID? ' + str(i))).replace('\r\n','')
                time.sleep(0.05)
                self.values['both_pids'].append(self.values['pid_' + str(i)])
            return self.values['both_pids']
        if loop in range(1, 3):
            self.values['pid_' + str(loop)] = str(self.inst.query('PID? ' + str(loop))).replace('\r\n','')
            time.sleep(0.05)
            return self.values['pid_' + str(loop)]
        else:
            raise ValueError('Incorrect input. Loop must be -1, 1, or 2.')
            
    def set_pid(self, loop, p, i, d):
        """
        Setting resolution is less than 6 digits indicated.
        """
        if (loop == -1) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            for i in range(1, 3):
                self.inst.write('PID ' + str(i) + str(p) + ',' + str(i) + ',' + str(d))
                time.sleep(0.05)
            return self.get_pid(-1)
        if (loop in range(1,3)) and (p <= 1000 and p >= 0.1) and (i <= 1000 and i >= 0.1) and (d <= 200 and d >= 0.1):
            self.inst.write('PID ' + str(loop) + ',' + str(p) + ',' + str(i) + ',' + str(d))
            time.sleep(0.05)
            return self.get_pid(loop)
        else:
            raise ValueError('Incorrect input. Refer to manual for proper parameters.')
            
    def get_temp(self, inp):
        if self.get_model() == 'MODEL336':
            if inp == -1:
                self.values['both_temperatures'] = list()
                for i in ['A', 'B', 'C', 'D']:
                    self.values['temperature_' + i.lower()] = str(self.inst.query('KRDG? ' + i)).replace('\r\n','')
                    time.sleep(0.05)
                    self.values['both_temperatures'].append(self.values['temperature_' + i.lower()])
                return self.values['both_temperatures']
            if inp.upper() in ['A', 'B', 'C', 'D']:
                self.values['temperature_' + inp.lower()] = str(self.inst.query('KRDG? ' + inp.upper())).replace('\r\n','')
                time.sleep(0.05)
                return self.values['temperature_' + inp.lower()]
            else:
                raise ValueError('Incorrect input. Inp must be -1, A, B, C, or D.')
        else:
            if inp == -1:
                self.values['both_temperatures'] = list()
                for i in ['A','B']:
                    self.values['temperature_' + i.lower()] = str(self.inst.query('KRDG? ' + i)).replace('\r\n','')
                    time.sleep(0.05)
                    self.values['both_temperatures'].append(self.values['temperature_' + i.lower()])
                return self.values['both_temperatures']
            if inp.upper() in ['A','B']:
                self.values['temperature_' + inp.lower()] = str(self.inst.query('KRDG? ' + inp.upper())).replace('\r\n','')
                time.sleep(0.05)
                return self.values['temperature_' + inp.lower()]
            else:
                raise ValueError('Incorrect input. Inp must be -1, A, or B.')
                
    def log(self):
        if self.get_model() == 'MODEL336':
            info = list()
            temp = self.get_temp(-1)
            for i in range(0, 4):
                info.append(temp[i])
            heater = self.get_heater_percent(-1)
            for i in range(0, 2):
                info.append(heater[i])
            return info
        else:
            info = list()
            temp = self.get_temp(-1)
            for i in range(0, 2):
                info.append(temp[i])
            heater = self.get_heater_percent(-1)
            for i in range(0, 2):
                info.append(heater[i])
            return info