"""
Methods for testing the operation of the IBM4 Serial Controller Class

0. Basic Find, Open, Close
1. Step through voltages
2. Basic single channel sweep
3. Read all input channels
4. Differential read
5. Multi-reads and timings
6. Multimeter mode
7. Linear single channel sweep

R. Sheehan 12 - 6 - 2024
"""

import time
import numpy 
import matplotlib.pyplot as plt
# import Sweep_Interval
import IBM4_Lib

MOD_NAME_STR = "Control_Examples"

def Simple_Open_Close():
    """
    See if an IBM4 is connected to the PC, if so, open it and then close it
    """
    
    FUNC_NAME = ".Simple_Open_Close()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        #the_dev = IBM4_Lib.Ser_Iface(read_mode = 'DC') # find the first connected IBM4, open in DC mode
        
        #the_dev = IBM4_Lib.Ser_Iface(read_mode = 'AC') # find the first connected IBM4, open in AC mode
        
        #the_dev = IBM4_Lib.Ser_Iface('COM3', read_mode='AC') # connect to a named IBM4, open in AC mode

        print("IBM4 IDN string:", the_dev.IdentifyIBM4() )
        # print("Speak Response:", the_dev.talk())

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Step_Through_Voltages():
    """
    Connect to an IBM4, output voltage from a channel, increase that voltage, make a reading
    """
    
    FUNC_NAME = ".Step_Through_Voltages()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        output_ch = 'A1' # select the voltage output channel either A0 or A1
        input_ch = 'A2' # select the voltage input channel A2, A3, A4, A5, D2

        print("Analog Output Steps + Averaged Read on Single Channel")
        print("Analog Out:",output_ch)
        print("Analog In:",input_ch)   

        volt_val = 1.0
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        volt_val = 1.5
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        volt_val = 2.0
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        volt_val = 1.7
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        volt_val = 0.7
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        avg_val = the_dev.ReadAverageVoltage(input_ch, no_reads = 10, loud = False)
        print("Set voltage value = ",volt_val)
        print("Recorded average voltage = ",avg_val)

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Simple_Sweep():
    """
    Perform simple sweep and read on a single channel
    """
    
    FUNC_NAME = ".Simple_Sweep()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        output_ch = 'A1' # select the voltage output channel either A0 or A1
        input_ch = 'A2' # select the voltage input channel A2, A3, A4, A5, D2
        Nreads = 51 # no. readings at each channel
        volts = numpy.arange(0, 3.1, 1)

        print("Analog Output Sweep + Averaged Read on Single Channel")
        print("Analog Out:",output_ch)
        print("Analog In:",input_ch)
        
        start = time.time()
        for v in volts:
            the_dev.WriteVoltage(output_ch, v)
            reading = the_dev.ReadAverageVoltage(input_ch, Nreads)
            print('Vset:',v,', Vread: ',reading)
        end = time.time()
        deltaT = end-start
        readsTot = len(volts)*Nreads
        measT = deltaT/(float(readsTot))
        SR = 1.0/measT
        print("%(v1)d measurements performed in %(v2)0.3f seconds => SR = %(v3)0.3f Hz"%{"v1":readsTot, "v2":deltaT, "v3":SR})

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Simple_Sweep_Read_All():
    """
    Perform simple sweep and read on all input channel
    """
    
    FUNC_NAME = ".Simple_Sweep_Read_All()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        output_ch = 'A1' # select the voltage output channel either A0 or A1
        Nreads = 31 # no. readinngs at each channel
        NAI = 5 # no. analog input channels
        volts = numpy.arange(0, 3.1, 0.5)

        print("Analog Output Sweep + Averaged Read on All Channels")
        print("Analog Out:",output_ch)

        start = time.time()
        for v in volts:
            the_dev.WriteVoltage(output_ch, v)
            readings = the_dev.ReadAverageVoltageAllChnnl(Nreads)
            print('Vset:',v,', Vread: ',readings)
        end = time.time()
        deltaT = end-start
        readsTot = len(volts)*Nreads*NAI
        measT = deltaT/(float(readsTot))
        SR = 1.0/measT
        print("%(v1)d measurements performed in %(v2)0.3f seconds => SR = %(v3)0.3f Hz"%{"v1":readsTot, "v2":deltaT, "v3":SR})

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Differential_Readings():
    """
    Perform differential reads between different pairs of channels
    use the overloaded DifferentialRead Method to obtain an averaged reading

    the user must be careful when using overloaded methods
    python allows for different return types and different numbers of returned elements
    what is not forbidden is permitted and exploited
    """
    
    FUNC_NAME = ".Differential_Readings()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        # this assumes that you are reading the voltage across a resistor and diode in series
        # A2 set to Vin, A3 between the resistor and the diode, A4 at GND
        Nreads = 1000
        Rval = 10.0 / 1000.0 # sense resistance in kOhm
        Vset = 2.25
        output_ch = 'A0' # select the voltage output channel either A0 or A1

        print("Differential Reads on Different Analog Inputs")
        print("Analog Out: ",output_ch)
        
        the_dev.WriteVoltage(output_ch, Vset)
        time.sleep(1) # give it some time to settle

        vals = the_dev.DifferentialRead('A2', 'A4', 'Multiple Voltage', Nreads)
        print("Vhi: A2, Vlo: A4")
        print("Set Voltage: %(v1)0.3f +/- %(v2)0.3f (V)"%{"v1":vals[0],"v2":vals[1]})

        vals = the_dev.DifferentialRead('A2', 'A3', 'Multiple Voltage', Nreads)
        print("Vhi: A2, Vlo: A3")
        print("Sense Voltage: %(v1)0.3f +/- %(v2)0.3f (V)"%{"v1":vals[0],"v2":vals[1]})
        print("Sense Current: %(v1)0.1f +/- %(v2)0.1f (mA)"%{"v1":vals[0]/Rval,"v2":vals[1]/Rval})
        filename = 'Differential_Readings_Data.txt'
        numpy.savetxt(filename, vals[2], fmt = '%0.4f', delimiter = '\t')
        print(vals[2])
        
        vals = the_dev.DifferentialRead('A3', 'A4', 'Multiple Voltage', Nreads)
        print("Vhi: A3, Vlo: A4")
        print("Diode Voltage: %(v1)0.3f +/- %(v2)0.3f (V)"%{"v1":vals[0],"v2":vals[1]})
        
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Multiple_Readings():
    """
    Perform multiple readings by different methods
    use the overloaded ReadVoltage Method to obtain an averaged reading

    the user must be careful when using overloaded methods
    python allows for different return types and different numbers of returned elements
    what is not forbidden is permitted and exploited
    """
    
    FUNC_NAME = ".Multiple_Readings()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        # can compare the timing of each of the different measurement types
        # https://stackoverflow.com/questions/7370801/how-do-i-measure-elapsed-time-in-python
        # ReadAverageVoltage is slightly faster than ReadAverageVoltageMultiple
        # which is weird considering that ReadAverageVoltage has to do extra processing on chip
        # Sample Rate for IBM4 is variable, as we know and find annoying
        # Can see that nothing wrong with timing of ReadAverageVoltageAllChnnl
        # Execution of ReadAverageVoltageAllChnnl takes ~ 5 ReadAverageVoltage which makes sense really
        # since ReadAverageVoltageAllChnnl consists of 5 calls to ReadAverageVoltage
        # R. Sheehan 9 - 7 - 2024

        Nreads = 501
        Vset = 1.5
        output_ch = 'A1'
        the_dev.WriteVoltage(output_ch,Vset)
        time.sleep(1)

        print("Multiple Reads by Different Methods - Test the Overloaded ReadVoltage method")
        print("Analog Out:",output_ch)
        print("Vset =",Vset,"(V)\n")

        # time the measurement
        start = time.time()
        #avg, err, vals = the_dev.ReadMultipleVoltage('A3', Nreads)
        avg, err, vals = the_dev.ReadVoltage('A3', 'Multiple Voltage', Nreads)
        end = time.time()
        deltaT = end-start
        measT = deltaT/(float(Nreads))
        SR = 1.0/measT
        print("Analog Input: A3, Read Method: Multiple Voltage => ReadMultipleVoltage")
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR })
        print("Measured Voltage: %(v1)0.3f +/- %(v2)0.3f (V)\n"%{"v1":avg,"v2":err})

        start = time.time()
        #val = the_dev.ReadAverageVoltage('A3',Nreads)
        val = the_dev.ReadVoltage('A3','Average Voltage', Nreads)
        end = time.time()
        deltaT = end-start
        measT = deltaT/(float(Nreads))
        SR = 1.0/measT
        print("Analog Input: A3, Read Method: Average Voltage => ReadAverageVoltage")
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR })
        print("Measured Voltage: %(v1)0.3f (V)\n"%{"v1":val})

        start = time.time()
        val = the_dev.ReadAverageVoltageAllChnnl(Nreads)
        end = time.time()
        deltaT = end-start
        measT = deltaT/(float(Nreads*5))
        SR = 1.0/measT
        print("Analog Input: All, Read Method: ReadAverageVoltageAllChnnl")
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads*5, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR})
        print("Measured Voltages: ", val)
        #print("\nSR from each Read method are comparable")

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Read_Waveform():
    """
    Perform multiple readings to read a waveform
    use the overloaded ReadVoltage Method to obtain an averaged reading
    or use the ReadMultipleVoltage Method directly

    the user must be careful when using overloaded methods
    python allows for different return types and different numbers of returned elements
    what is not forbidden is permitted and exploited
    """
    
    FUNC_NAME = ".Read_Waveform()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface(read_mode = 'DC') # find the first connected IBM4
        
        Nreads = 5001 # no. readings to be made        
        input_ch_1 = 'A2' # analog input channel on which readings are to be made
        input_ch_2 = 'A3' # analog input channel on which readings are to be made
        # time the measurement
        start = time.time()
        
        # overloaded call to ReadMultipleVoltage
        the_dev.WritePWM(50)
        time.sleep(1)
        print("Hello")
        avg_1, err_1, vals_1 = the_dev.ReadVoltage(input_ch_1, 'Multiple Voltage', Nreads)
        avg_2, err_2, vals_2 = the_dev.ReadVoltage(input_ch_2, 'Multiple Voltage', Nreads)
        
        # Direct call to ReadMultipleVoltage
        # avg, err, vals = the_dev.ReadMultipleVoltage(input_ch, Nreads) # 
        
        end = time.time()

        # compute the time taken to perform all the measurements
        # this time does not include the overheads incurred by the IBM4 itself
        deltaT = end-start
        measT = deltaT/(float(Nreads))
        SR = 1.0/measT
        
        print("Analog Input A2: %(v1)s, Read Method: Multiple Voltage => ReadMultipleVoltage"%{"v1":input_ch_1})
        print("Analog Input A3: %(v1)s, Read Method: Multiple Voltage => ReadMultipleVoltage"%{"v1":input_ch_2})
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR})
        print("Measured Average Voltage A2: %(v1)0.3f +/- %(v2)0.3f (V)\n"%{"v1":avg_1,"v2":err_1})
        print("Measured Average Voltage A3: %(v1)0.3f +/- %(v2)0.3f (V)\n"%{"v1":avg_2,"v2":err_2})

        # Make a plot of the recorded waveform if you desire
        # Write the data to a file, make a plot elsewhere
        filename = 'Waveform_Data_A2.txt'
        numpy.savetxt(filename, vals_1, fmt = '%0.4f', delimiter = '\t')
        max_val = numpy.max(vals_1)
        min_val = numpy.min(vals_1)
        dif = max_val - min_val
        
        print("The p-p voltage across this A2 is " + str(dif))

        filename = 'Waveform_Data_A3.txt'
        numpy.savetxt(filename, vals_2, fmt = '%0.4f', delimiter = '\t')
        max_val = numpy.max(vals_2)
        min_val = numpy.min(vals_2)
        dif = max_val - min_val
        
        print("The p-p voltage across this A3 is " + str(dif))


        time.sleep(10)
        
        
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
        

def Read_Double_Waveform(input_ch1, input_ch2):
    """
    Perform multiple readings to read two waveform at (almost) the same time
    use the overloaded ReadVoltage Method to obtain an averaged reading
    or use the ReadMultipleVoltage Method directly

    the user must be careful when using overloaded methods
    python allows for different return types and different numbers of returned elements
    what is not forbidden is permitted and exploited
    """

    FUNC_NAME = ".Read_Double_Waveform()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface(read_mode="AC")  # find the first connected IBM4

        Nreads = 501  # no. readings to be made
        input_ch1 = "A2"  # analog input channel #1 on which readings are to be made
        input_ch2 = "A3"  # analog input channel #2 on which readings are to be made

        # time the measurement
        start = time.time()

        # overloaded call to ReadMultipleVoltage
        the_dev.WritePWM(50)
        time.sleep(0.2)
        avg1, err1, vals1, avg2, err2, vals2 = the_dev.ReadDoubleMultiple(input_ch1, input_ch2, Nreads)

        # Direct call to ReadMultipleVoltage
        # avg, err, vals = the_dev.ReadMultipleVoltage(input_ch, Nreads) #

        end = time.time()

        # compute the time taken to perform all the measurements
        # this time does not include the overheads incurred by the IBM4 itself
        deltaT = end - start
        measT = deltaT / (float(Nreads))
        SR = 1.0 / measT

        print("Analog Double Input: %(v1)s, %(v2)s, Read Method: Double Voltage => ReadDoubleMultiple"
            % {"v1": input_ch1, "v2": input_ch2})
        print("%(v1)d measurements performed in %(v2)0.3f seconds"
            % {"v1": Nreads, "v2": deltaT})
        print("%(v1)0.4f secs / measurement" % {"v1": measT})
        print("Sample Rate: %(v1)0.2f Hz" % {"v1": SR})
        print("Measured Averages Voltage1: %(v1)0.3f +/- %(v2)0.3f (V), Voltage2: %(v3)0.3f +/- %(v4)0.3f (V)\n"
            % {"v1": avg1, "v2": err1, "v3": avg2, "v4": err2})

        # Write the data to a file, make a plot elsewhere
        filename = "Double_Waveform_Data.txt"
        vals = numpy.column_stack((vals1, vals2))
        numpy.savetxt(filename, vals, fmt="%0.4f", delimiter="\t")

        fft_sig_full1 = numpy.fft.fft(vals1)
        fft_sig1 = numpy.abs(fft_sig_full1)
        numpy.savetxt('FFT_Data_A2.txt', fft_sig1, fmt = '%0.4f', delimiter = '\t')
        fft_sig_full2 = numpy.fft.fft(vals2)
        fft_sig2 = numpy.abs(fft_sig_full2)
        numpy.savetxt('FFT_Data_A3.txt', fft_sig2, fmt = '%0.4f', delimiter = '\t')

        del the_dev  # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)


def Multimeter_Mode():
    """
    Run the IBM4 in multimeter mode
    """
    
    FUNC_NAME = ".Multimeter_Mode()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default

        the_dev.MultimeterMode() # I rock
       
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Linear_Sweep_V1():
    """
    Perform a linear sweep on chosen channels
    """
    
    FUNC_NAME = ".Linear_Sweep_V1()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default

        # instantiate an object to keep track of the sweep space parameters
        no_steps = 50
        v_start = 0.0
        v_end = 3.3
        Ic_array = numpy.array([]) #stores current across resistor c
        Ib_array = numpy.array([]) #stores current across resistor b
        a = 4
        b = 18 #number of voltage measurements for Vb
        index_I = (b - 13) - 1 #replace 7 with other numbers to compare currents at different voltages measurment of Vb
        for v_fixed in range(a, b):
            v_fixed = v_fixed*(3.2/(b-1)) #normalises voltage values to ensure output is between 0 and 3.3 volts

            # A0 will sweep while A1 will be kept constant at v_fixed
            # I wonder what that could be used for? 
            sweep_data = the_dev.SingleChannelSweepA('A0', v_start, v_end, no_steps, v_fixed) # use channel A0 to sweep over the voltage interval

            
            """ print('Measured data')
            print(sweep_data) """
            filename = 'Linear_Sweep_Data_A2.txt'
            numpy.savetxt(filename, sweep_data[:,1], fmt = '%0.4f', delimiter = '\t')
            filename = 'Linear_Sweep_Data_A3.txt'
            numpy.savetxt(filename, sweep_data[:,2], fmt = '%0.4f', delimiter = '\t')
            filename = 'Linear_Sweep_Data_A4.txt'
            numpy.savetxt(filename, sweep_data[:,3], fmt = '%0.4f', delimiter = '\t')
            filename = 'Linear_Sweep_Data_A5.txt'
            numpy.savetxt(filename, sweep_data[:,4], fmt = '%0.4f', delimiter = '\t')

            #PLOTTING TRANSISTOR IV CURVES

            R_b = 1500 #resistor values
            R_c = 10
            Vb_array = numpy.genfromtxt('Linear_Sweep_Data_A5.txt')
            Vcc_array = numpy.genfromtxt('Linear_Sweep_Data_A4.txt')
            Vbe_array = numpy.genfromtxt('Linear_Sweep_Data_A3.txt')
            Vce_array = numpy.genfromtxt('Linear_Sweep_Data_A2.txt')
            Ic_array = numpy.append(Ic_array, (Vcc_array[index_I]-Vce_array[index_I])/R_c)
            Ib_array = numpy.append(Ib_array, (Vb_array[index_I]-Vbe_array[index_I])/R_b)


            plt.plot(Vce_array, (Vcc_array-Vce_array)/R_c, label='Vb = ' + format(v_fixed, '.2f'))


        plt.xlabel('Vce (V)')
        plt.ylabel('Ic (A)')
        plt.xlim(-0.25, 3.5)
        plt.minorticks_on()

        plt.legend()
        plt.savefig('Trans_curves.png')
    
        plt.show()

        
       
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
'''
def Linear_Sweep_V2():
    """
    Perform a linear sweep on chosen channels
    """
    
    FUNC_NAME = ".Linear_Sweep_V2()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default

        # instantiate an object to keep track of the sweep space parameters
        no_steps = 30
        v_start = 0.5
        v_end = 2
        Ic_array = numpy.array([]) #stores current across resistor c
        Ib_array = numpy.array([]) #stores current across resistor b
        the_interval = Sweep_Interval.SweepSpace(no_steps, v_start, v_end)

        # A1 will sweep while A0 will be kept constant at v_fixed
        # I wonder what that could be used for? 
        sweep_data = the_dev.SingleChannelSweepB('A1', the_interval, v_fixed = 3.2) # use channel A1 to sweep over the voltage interval


        filename = 'Linear_Sweep_Data_A2.txt'
        numpy.savetxt(filename, sweep_data[:,1], fmt = '%0.4f', delimiter = '\t')
        filename = 'Linear_Sweep_Data_A3.txt'
        numpy.savetxt(filename, sweep_data[:,2], fmt = '%0.4f', delimiter = '\t')
        filename = 'Linear_Sweep_Data_A4.txt'
        numpy.savetxt(filename, sweep_data[:,3], fmt = '%0.4f', delimiter = '\t')
        filename = 'Linear_Sweep_Data_A5.txt'
        numpy.savetxt(filename, sweep_data[:,4], fmt = '%0.4f', delimiter = '\t')

       

        R_b = 1500 #resistor values
        R_c = 10
        Vb_array = numpy.genfromtxt('Linear_Sweep_Data_A5.txt')
        Vcc_array = numpy.genfromtxt('Linear_Sweep_Data_A4.txt')
        Vbe_array = numpy.genfromtxt('Linear_Sweep_Data_A3.txt')
        Vce_array = numpy.genfromtxt('Linear_Sweep_Data_A2.txt')
        Ic_array = numpy.append(Ic_array, (Vcc_array-Vce_array)/R_c)
        Ib_array = numpy.append(Ib_array, (Vb_array-Vbe_array)/R_b)

        def line_of_best_fit(x, y):
            x = numpy.array(x)
            y = numpy.array(y)

    
            m, b = numpy.polyfit(x, y, 1)
            return m, b
        
        m, b = line_of_best_fit(Ib_array[:15], Ic_array[:15])    
        print(f"Slope: {m}")
        print(f"Intercept: {b}")
        print(f"Equation: y = {m:.3f}x + {b:.3f}")

        bspace = numpy.linspace(-0.00005,0.0017, 1000)

        plt.plot(Ib_array, Ic_array, label='Ic against Ib at Vb = 3.2 volts')
        plt.plot(bspace, m*bspace + b, label="Line of best fit (m = " + format(m, '.2f') + ", b = " + format(b, '.3f') + ') for first 15 x values')
        plt.xlabel('Ib (A)')
        plt.ylabel('Ic (A)')
        plt.minorticks_on()

        plt.xlim(0, 0.000825)
        plt.ylim(0,0.1)
        plt.legend(loc='upper left')
        plt.savefig('Beta_curve.png')

        plt.show()

       
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
'''


def Read_Waveform_plus_FFT():
    """
    Perform multiple readings to read a waveform
    use the overloaded ReadVoltage Method to obtain an averaged reading
    or use the ReadMultipleVoltage Method directly

    the user must be careful when using overloaded methods
    python allows for different return types and different numbers of returned elements
    what is not forbidden is permitted and exploited
    """
    
    FUNC_NAME = ".Read_Waveform()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface(read_mode = 'AC') # find the first connected IBM4
        
        Nreads = 5001 # no. readings to be made        
        input_ch_1 = 'A2' # analog input channel on which readings are to be made
        input_ch_2 = 'A3' # analog input channel on which readings are to be made
        # time the measurement
        start = time.time()
        
        # overloaded call to ReadMultipleVoltage
        # the_dev.WritePWM(50)
        time.sleep(0)
        print("Hello")
        avg_1, err_1, vals_1 = the_dev.ReadVoltage(input_ch_1, 'Multiple Voltage', Nreads)
        
        # Direct call to ReadMultipleVoltage
        # avg, err, vals = the_dev.ReadMultipleVoltage(input_ch, Nreads) # 
        
        end = time.time()

        # compute the time taken to perform all the measurements
        # this time does not include the overheads incurred by the IBM4 itself
        deltaT = end-start
        measT = deltaT/(float(Nreads))
        SR = 1.0/measT
        
        print("Analog Input A2: %(v1)s, Read Method: Multiple Voltage => ReadMultipleVoltage"%{"v1":input_ch_1})
        print("Analog Input A3: %(v1)s, Read Method: Multiple Voltage => ReadMultipleVoltage"%{"v1":input_ch_2})
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR})
        print("Measured Average Voltage A2: %(v1)0.3f +/- %(v2)0.3f (V)\n"%{"v1":avg_1,"v2":err_1})
        print("Measured Average Voltage A3: %(v1)0.3f +/- %(v2)0.3f (V)\n"%{"v1":avg_2,"v2":err_2})

        # Make a plot of the recorded waveform if you desire
        # Write the data to a file, make a plot elsewhere
        filename = 'Waveform_Data_A2.txt'
        numpy.savetxt(filename, vals_1, fmt = '%0.4f', delimiter = '\t')


        fft_sig_full = numpy.fft.fft(vals_1)
        fft_sig = numpy.abs(fft_sig_full)
        numpy.savetxt('FFT_Data_single.txt', fft_sig, fmt = '%0.4f', delimiter = '\t')

        
        
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)



def Read_Waveform_And_Display_Vavg():
    """
    Perform multiple readings to read a waveform
    use the overloaded ReadVoltage Method to obtain an averaged reading
    or use the ReadMultipleVoltage Method directly

    the user must be careful when using overloaded methods
    python allows for different return types and different numbers of returned elements
    what is not forbidden is permitted and exploited
    """
    
    FUNC_NAME = ".Read_Waveform_And_Display()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface(read_mode = 'DC') # find the first connected IBM4
        
        Nreads = 5001 # no. readings to be made        
        input_ch_1 = 'A2' # analog input channel on which readings are to be made
        input_ch_2 = 'A3' # analog input channel on which readings are to be made
        # time the measurement
        start = time.time()
        
        # overloaded call to ReadMultipleVoltage
        the_dev.WritePWM(50)
        time.sleep(1)
        print("Hello")
        avg_1, err_1, vals_1 = the_dev.ReadVoltage(input_ch_1, 'Multiple Voltage', Nreads)
        avg_2, err_2, vals_2 = the_dev.ReadVoltage(input_ch_2, 'Multiple Voltage', Nreads)
        
        # Direct call to ReadMultipleVoltage
        # avg, err, vals = the_dev.ReadMultipleVoltage(input_ch, Nreads) # 
        
        end = time.time()

        # compute the time taken to perform all the measurements
        # this time does not include the overheads incurred by the IBM4 itself
        deltaT = end-start
        measT = deltaT/(float(Nreads))
        SR = 1.0/measT
        
        print("Analog Input A2: %(v1)s, Read Method: Multiple Voltage => ReadMultipleVoltage"%{"v1":input_ch_1})
        print("Analog Input A3: %(v1)s, Read Method: Multiple Voltage => ReadMultipleVoltage"%{"v1":input_ch_2})
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR})
        print("Measured Average Voltage A2: %(v1)0.3f +/- %(v2)0.3f (V)\n"%{"v1":avg_1,"v2":err_1})
        print("Measured Average Voltage A3: %(v1)0.3f +/- %(v2)0.3f (V)\n"%{"v1":avg_2,"v2":err_2})

        # Make a plot of the recorded waveform if you desire
        # Write the data to a file, make a plot elsewhere
        filename = 'Waveform_Data_A2.txt'
        numpy.savetxt(filename, vals_1, fmt = '%0.4f', delimiter = '\t')
        max_val = numpy.max(vals_1)
        min_val = numpy.min(vals_1)
        dif_1 = max_val - min_val
        
        print("The p-p voltage across this A2 is " + str(dif_1))

        filename = 'Waveform_Data_A3.txt'
        numpy.savetxt(filename, vals_2, fmt = '%0.4f', delimiter = '\t')
        max_val = numpy.max(vals_2)
        min_val = numpy.min(vals_2)
        dif_2 = max_val - min_val
        
        print("The p-p voltage across this A3 is " + str(dif_2))

        # Calls method to display values on E-Ink screen
        the_dev.vdisplay(round(avg_2, 5), round(dif_2, 5))

        time.sleep(5)
        
        
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
        


def Simple_Read_and_Display_A2():
    FUNC_NAME = ".Simple_Read_and_Display_A2"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    try:
        the_dev = IBM4_Lib.Ser_Iface()
        the_dev.read_and_display_A2()

        del the_dev

    except Exception as e:
        print(ERR_STATEMENT)
        print(e)


def gain_control(channel, gain):
    FUNC_NAME = ".gain_control"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    try:
        if gain not in [1, 2]:
            print("Invalid gain. Please enter a valid gain (1 or 2).")
            return
        if channel not in ["a", "b", "c", "d"]:
            print("Invalid channel. Please enter a valid channel (a, b, c, or d).")
            return
        the_dev = IBM4_Lib.Ser_Iface()
        the_dev.gain_settings(channel = channel, gain = gain)
        del the_dev

    except Exception as e:
        print(ERR_STATEMENT)
        print(e)



def MCP4728(channel, voltage):
    FUNC_NAME = ".MCP4728"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    try:
        if voltage < 0 or voltage > 4.095:
            print("Voltage out of range. Please enter a value between 0 and 4.095V.")
            return
        if channel not in ["a", "b", "c", "d"]:
            print("Invalid channel. Please enter a valid channel (a, b, c, or d).")
            return
        the_dev = IBM4_Lib.Ser_Iface()
        the_dev.MCP4728_voltage(voltage, channel)
        del the_dev

    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def MCP4728_all(channel, voltage):
    FUNC_NAME = ".MCP4728_all"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    try:
        the_dev = IBM4_Lib.Ser_Iface()
        # pin_list = ["a", "b", "c", "d"]
        the_dev.MCP4728_voltage(voltage, channel)
        del the_dev

    except Exception as e:
        print(ERR_STATEMENT)
        print(e)


def Sweep_MCP4728():
    FUNC_NAME = ".Sweep_MCP4728"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    try:
        the_dev = IBM4_Lib.Ser_Iface()

        del the_dev

    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

        