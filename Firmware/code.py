import supervisor
import time
import board
import pwmio
from analogio import AnalogIn
from analogio import AnalogOut
import adafruit_mcp4728

try:
    i2c = board.I2C()
    mcp4728_dac = adafruit_mcp4728.MCP4728(i2c, address=0x60)
    mcp4728_ready = True
except Exception as e:
    mcp4728_dac = None
    mcp4728_ready = False
    print("MCP4728 init failed:", e)

MCP4728_VREF = 4.096

# pwm = pwmio.PWMOut(board.D9, frequency=500)
# pwm = pwmio.PWMOut(board.D9, duty_cycle=2 ** 15, frequency=440, variable_frequency=True)
pwm5 = pwmio.PWMOut(board.D5, duty_cycle=2 ** 15)
pwm7 = pwmio.PWMOut(board.D7, duty_cycle=2 ** 15)
pwm9 = pwmio.PWMOut(board.D9, duty_cycle=2 ** 15)
pwm10 = pwmio.PWMOut(board.D10, duty_cycle=2 ** 15)
pwm11 = pwmio.PWMOut(board.D11, duty_cycle=2 ** 15)
pwm12 = pwmio.PWMOut(board.D12, duty_cycle=2 ** 15)
pwm13 = pwmio.PWMOut(board.D13, duty_cycle=2 ** 15)

# For listening for serial inputs
####
# Define names for In and Out pins
Vout0 = AnalogOut(board.A0)
Vout1 = AnalogOut(board.A1)
Vin2 = AnalogIn(board.A2)
Vin3 = AnalogIn(board.A3)
Vin4 = AnalogIn(board.A4)
Vin5 = AnalogIn(board.A5)
Vin6 = AnalogIn(board.D2) # according to pinout doc pin labelled as 2 is another AI
NRdChLim = 5 # Upper limit for no of channels that can read, previously NRdChLim = 4

B2U_Cal = 14/3

# Define the constants
# For notes on the following see 
# https://learn.adafruit.com/circuitpython-basics-analog-inputs-and-outputs/analog-to-digital-converter-inputs
# ADC values in circuit python are all put in the range of 16-bit unsigned values so 0 - 65535 (-1+2**16)
Vmax = Vin2.reference_voltage # max AO/AI value
bit_scale = (-1+(2**16) )#(-1+(64*1024)) # 64 bits

# Functions to convert from 12-bit to Volt.
def dac_value(volts):
    return int(volts / 3.3 * 65535)
    #return int((volts / Vmax)*bit_scale)
    
def get_voltage(pin):
    return (pin.value * 3.3) / 65535
    #return ((pin.value*Vmax)/bit_scale)
    
def get_PWM(percentage):
    return (int(percentage/100.0*0xffff+0.5))




# def set_gain(gain, channel):
#     if gain == 1 or gain == 2:
#         if channel == "a":
#             mcp4728_dac.channel_a.gain = gain
#         if channel == "b":
#             mcp4728_dac.channel_b.gain = gain
#         if channel == "c":
#             mcp4728_dac.channel_c.gain = gain
#         if channel == "d":
#             mcp4728_dac.channel_d.gain = gain


def set_mcp4728_voltage(channel, volts):
    if not mcp4728_ready:
        raise RuntimeError("MCP4728 not ready")
    if volts < 0.0 or volts > MCP4728_VREF:
        raise ValueError("Voltage out of range 0.0-4.096V")

    value = int((volts / MCP4728_VREF) * 65535)
    if value < 0:
        value = 0
    if value > 65535:
        value = 65535
    if channel == "a":
        mcp4728_dac.channel_a.value = value
    elif channel == "b":
        mcp4728_dac.channel_b.value = value
    elif channel == "c":
        mcp4728_dac.channel_c.value = value
    elif channel == "d":
        mcp4728_dac.channel_d.value = value
    else:
        raise ValueError("Channel must be a, b, c, or d")
    
def Simple_Vout_A0(command):
    # If the user inputs command a<value> this will be interpreted as setting A0 to the volt level <value>
    try:
        SetVoltage = float(command[1:])
        if SetVoltage >= 0.0 and SetVoltage < Vmax: # Sets limits on the Output voltage to board specs
            Vout0.value = dac_value(SetVoltage) # Set the voltage
        else:
            Vout0.value = dac_value(0.0) # Set the voltage to zero in the event of SetVoltage range error
    except Exception as e:
        print('\nERROR: Simple_Vout_A0\n')
        print(e)
        
def Simple_Vout_A1(command):
    # If the user inputs command b<value> this will be interpreted as setting A1 to the volt level <value>
    try:
        SetVoltage = float(command[1:])
        if SetVoltage >= 0.0 and SetVoltage < Vmax: # Sets limits on the Output voltage to board specs
            Vout1.value = dac_value(SetVoltage) # Set the voltage
        else:
            Vout1.value = dac_value(0.0) # Set the voltage to zero in the event of SetVoltage range error
    except Exception as e:
        print('\nERROR: Simple_Vout_A1\n')
        print(e)

def Simple_Read():
    try:
        # High-impedance voltage reading Vout = Vin
        V2real = get_voltage(Vin2) # no BP-UP on A2
        V3real = get_voltage(Vin3) # no BP-UP on A3
        V4real = get_voltage(Vin4) # no BP-UP on A4
        V5real = get_voltage(Vin5) # no BP-UP on A5
        # format string to output to nearest 10 mV
        #output_str = '%(v2)0.2f, %(v3)0.2f, %(v4)0.2f, %(v5)0.2f'%{"v2":V2real, "v3":V3real, "v4":V4real, "v5":V5real}
        DC_offset = get_voltage(Vin6) # read the DC offset of the BP-UP circuit
        output_str = '%(v2)0.2f, %(v3)0.2f, %(v4)0.2f, %(v5)0.2f, %(v6)0.2f'%{"v2":V2real, "v3":V3real, "v4":V4real, "v5":V5real, "v6":DC_offset}
        print(output_str) # Prints to serial to be read by LabVIEW
    except Exception as e:
        print('\nERROR: Simple_Read\n')
        print(e)


TheMode = 0




while True:
    # set_mcp4728_voltage("a", 2.0)
    if supervisor.runtime.serial_bytes_available:   # Listens for a serial command
        command = input()
        if command.startswith("*IDN"):
            print('ISBY-UCC-RevA.Voltage_source')
        if command.startswith("Calibrate"):
            try:
                with open("/Calibration.txt", "r") as fp:
                    read_data = fp.read()
                    fp.close()
                    print(str(read_data))
            except OSError as e:  # When the file is not available...
                print('ERROR: Calibration file not available')

            # Split the string at the comma
            numbers = read_data.split(',')

            # Convert the substrings to floats
            K = float(numbers[0])
            KI = float(numbers[1])

        elif command.startswith("Mode"):
            TheMode = int(command[4:])
            print(TheMode)
        elif command.startswith("PWM"):
            try:
                Tokens = command[3:].split(":")
                ThePin = int(Tokens[0])
                SetPWM = float(Tokens[1])
                if ThePin == 5:
                    pwm5.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 7:
                    pwm7.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 9:
                    pwm9.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 10:
                    pwm10.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 11:
                    pwm11.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 12:
                    pwm12.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 13:
                    pwm13.duty_cycle = get_PWM(SetPWM)
                else:
                    print('Pin out of range: 5,7,9,10-13')
            except ValueError as ex:
                print('Vset must be an integer')
                print(ex)
            else:
                print("PWMset", ThePin, "=", str(SetPWM), end=' ')
                print()
        elif command.startswith("Write"):
            try:
                Tokens = command[5:].split(":")
                Chan = int(Tokens[0])
                SetVoltage = float(Tokens[1])
                if SetVoltage >= 0 and SetVoltage < 3.31:
                    # Sets limits on the Output voltage to board specs
                    if Chan == 0:
                        Vout0.value = dac_value(SetVoltage)  # Set the voltage
                    elif Chan == 1:
                        Vout1.value = dac_value(SetVoltage)  # Set the voltage
                    else:
                        print('Channel out of range: 0 - 1')
                else:
                    print('Vset out of range: 0 - 3.3V')
            except ValueError as ex:
                print('Vset must be a float')
                print(ex)
            except:
                print('Unknown problem')
            else:
                print("Vset", Chan, "=", str(SetVoltage), end=' ')
                print()
        elif command.startswith("Read"):
            try:
                Tokens = command[4:].split(":")
                Chan = int(Tokens[0])
                N = int(Tokens[1])
                if Chan == 0:
                    Pin = Vin2
                elif Chan == 1:
                    Pin = Vin3
                elif Chan == 2:
                    Pin = Vin4
                elif Chan == 3:
                    Pin = Vin5
                elif Chan == 4:
                    Pin = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if Chan in range(0, NRdChLim) and N > 0:
                    Ref = 0.0
                    Mult = 1
                    if TheMode == 1:
                        for i in range(100):
                            Ref += get_voltage(Vin6)
                        Ref /= 100
                        Mult = B2U_Cal
                    Values = [0] * N
                    for i in range(N):
                        Values[i] = get_voltage(Pin)
                    print("Output", Chan, "=", str((Values[0]-Ref)*Mult), end=' ')
                    for i in range(1, N):
                        print(",", str((Values[i]-Ref)*Mult), end=' ')
                    print()
        elif command.startswith("Average"):
            try:
                Tokens = command[7:].split(":")
                Chan = int(Tokens[0])
                N = int(Tokens[1])
                if Chan == 0:
                    Pin = Vin2
                elif Chan == 1:
                    Pin = Vin3
                elif Chan == 2:
                    Pin = Vin4
                elif Chan == 3:
                    Pin = Vin5
                elif Chan == 4:
                    Pin = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                if N < 1:
                    print('Must average at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if Chan in range(0, NRdChLim) and N > 0:
                    Ref = 0.0
                    Mult = 1
                    if TheMode == 1:
                        for i in range(100):
                            Ref += get_voltage(Vin6)
                        Ref /= 100
                        Mult = B2U_Cal
                    Value = 0.0
                    for i in range(N):
                        Value += get_voltage(Pin)
                    Value /= N
                    print("Average", Chan, "=", str((Value-Ref)*Mult))
        elif command.startswith("BRead"):
            try:
                Tokens = command[5:].split(":")
                Chan = int(Tokens[0])
                N = int(Tokens[1])
                if Chan == 0:
                    Pin = Vin2
                elif Chan == 1:
                    Pin = Vin3
                elif Chan == 2:
                    Pin = Vin4
                elif Chan == 3:
                    Pin = Vin5
                elif Chan == 4:
                    Pin = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if Chan in range(0, NRdChLim) and N > 0:
                    Values = [0] * N
                    for i in range(N):
                        Values[i] = Pin.value
                    print("Output", Chan, "=", str(Values[0]), end=' ')
                    for i in range(1, N):
                        print(",", str(Values[i]), end=' ')
                    print()
        elif command.startswith("Diff_Read"):
            try:
                Tokens = command[9:].split(":")
                ChanPlus = int(Tokens[0])
                if ChanPlus == 0:
                    Pplus = Vin2
                elif ChanPlus == 1:
                    Pplus = Vin3
                elif ChanPlus == 2:
                    Pplus = Vin4
                elif ChanPlus == 3:
                    Pplus = Vin5
                elif ChanPlus == 4:
                    Pplus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                ChanMinus = int(Tokens[1])
                if ChanMinus == 0:
                    Pminus = Vin2
                elif ChanMinus == 1:
                    Pminus = Vin3
                elif ChanMinus == 2:
                    Pminus = Vin4
                elif ChanMinus == 3:
                    Pminus = Vin5
                elif ChanMinus == 4:
                    Pminus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                N = int(Tokens[2])
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if ChanPlus in range(0, NRdChLim) and ChanMinus in range(0, NRdChLim) and N > 0:
                    Mult = 1
                    if TheMode == 1:
                        Mult = B2U_Cal
                    Values = [0] * N
                    for i in range(N):
                        Values[i] = get_voltage(Pplus)-get_voltage(Pminus)
                    print("Output =", str(Values[0]*Mult), end=' ')
                    for i in range(1, N):
                        print(",", str(Values[i]*Mult), end=' ')
                    print()
        elif command.startswith("Diff_Average"):
            try:
                Tokens = command[12:].split(":")
                ChanPlus = int(Tokens[0])
                if ChanPlus == 0:
                    Pplus = Vin2
                elif ChanPlus == 1:
                    Pplus = Vin3
                elif ChanPlus == 2:
                    Pplus = Vin4
                elif ChanPlus == 3:
                    Pplus = Vin5
                elif ChanPlus == 4:
                    Pplus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                ChanMinus = int(Tokens[1])
                if ChanMinus == 0:
                    Pminus = Vin2
                elif ChanMinus == 1:
                    Pminus = Vin3
                elif ChanMinus == 2:
                    Pminus = Vin4
                elif ChanMinus == 3:
                    Pminus = Vin5
                elif ChanMinus == 4:
                    Pminus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                N = int(Tokens[2])
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if ChanPlus in range(0, NRdChLim) and ChanMinus in range(0, NRdChLim) and N > 0:
                    Mult = 1
                    if TheMode == 1:
                        Mult = B2U_Cal
                    Value = 0.0
                    for i in range(N):
                        Value += (get_voltage(Pplus) - get_voltage(Pminus))
                    Value /= N
                    print("Average =", str(Value*Mult))
        elif command.startswith("Diff_BRead"):
            try:
                Tokens = command[10:].split(":")
                ChanPlus = int(Tokens[0])
                if ChanPlus == 0:
                    Pplus = Vin2
                elif ChanPlus == 1:
                    Pplus = Vin3
                elif ChanPlus == 2:
                    Pplus = Vin4
                elif ChanPlus == 3:
                    Pplus = Vin5
                elif ChanPlus == 4:
                    Pplus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                ChanMinus = int(Tokens[1])
                if ChanMinus == 0:
                    Pminus = Vin2
                elif ChanMinus == 1:
                    Pminus = Vin3
                elif ChanMinus == 2:
                    Pminus = Vin4
                elif ChanMinus == 3:
                    Pminus = Vin5
                elif ChanMinus == 4:
                    Pminus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                N = int(Tokens[2])
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if ChanPlus in range(0, NRdChLim) and ChanMinus in range(0, NRdChLim) and N > 0:
                    Values = [0] * N
                    for i in range(N):
                        Values[i] = Pplus.value - Pminus.value
                    print("Output =", str(Values[0]), end=' ')
                    for i in range(1, N):
                        print(",", str(Values[i]), end=' ')
                    print()
        elif command.startswith("a"):
            Simple_Vout_A0(command)
        elif command.startswith("b"):
            Simple_Vout_A1(command)
        elif command.startswith("l"):
            Simple_Read()

        elif command.startswith("MCP4728:"):
            try:
                Tokens = command.split(":")
                if len(Tokens) != 3:
                    raise ValueError("Use MCP4728:<channel>:<voltage>")
                channel = Tokens[1].lower()
                if channel not in ["a", "b", "c", "d"]:
                    raise ValueError("Channel must be a, b, c, or d")
                Voltage = float(Tokens[2])
                set_mcp4728_voltage(channel, Voltage)
            except Exception as ex:
                print("MCP4728 command error:", ex)
            
        elif command.startswith("MCP4728_all:"):
            try:
                Tokens = command.split(":")
                # MCP4728_all:<voltage_a>:<voltage_b>:<voltage_c>:<voltage_d>
                if len(Tokens) != 5:
                    raise ValueError("Use MCP4728_all:<voltage_a>:<voltage_b>:<voltage_c>:<voltage_d>")
                voltages = [float(v) for v in Tokens[1:]]
                for i, channel in enumerate(["a", "b", "c", "d"]):
                    set_mcp4728_voltage(channel, voltages[i])
            except Exception as ex:
                print("MCP4728_all command error:", ex)

        elif command.startswith("gain:"):
            try:
                Tokens = command.split(":")
                if len(Tokens) != 3:
                    raise ValueError("Use gain:<channel>:<gain>")
                channel = Tokens[1].lower()
                gain_value = int(Tokens[2])
                if gain_value not in [1, 2]:
                    raise ValueError("Gain must be 1 or 2")
                if channel == "a":
                    mcp4728_dac.channel_a.gain = gain_value
                elif channel == "b":
                    mcp4728_dac.channel_b.gain = gain_value
                elif channel == "c":
                    mcp4728_dac.channel_c.gain = gain_value
                elif channel == "d":
                    mcp4728_dac.channel_d.gain = gain_value
                else:
                    raise ValueError("Channel must be a, b, c, or d")
            except Exception as ex:
                print("Gain command error:", ex)
        else:
            print('\nERROR: Unknown command entered\n')
#    else:
#        print('If you can read this something has gone very wrong. ')