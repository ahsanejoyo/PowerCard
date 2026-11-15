# Import from library saved on Pico
from ina219 import INA219
from ssd1306 import SSD1306_I2C

# INA219 modules
import machine
from machine import Pin, I2C
import time

# Const addresses for I2C devices
I2C_ADDR = const(0x3c)
I2C_ADDR_INA = const(0x40) # note: 0x40 is default hardware I2C address for INA219

# SSD1306 screen initialization (400 khz)
i2c_ssd1306 = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c_ssd1306, addr=I2C_ADDR) # <- change y-value based on your screen (32 or 64)

# INA219 sensor initialization (400khz)
i2c_ina219 = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
sensor = INA219(i2c_ina219, addr=I2C_ADDR_INA) 
sensor.set_calibration_16V_400mA()

bootnum = 1 # counter for boot animation

#time.sleep(1.5) # delay for hardware firing, (omit?)

# Main Loop
while True:        
    oled.fill(0)  # Wipe screen buffer clear
    
    if bootnum == 1:
            oled.text("PowerCard", 0, 12, 1)
            oled.text("By Ahsan Joyo", 0, 22, 1)
            oled.show()
            time.sleep(3)
            bootnum = 0
            oled.fill(0)
        # else statement? or will it cause unnecessary delay/computing?

    # Sensor data
    voltage = sensor.bus_voltage
    current_mA = sensor.current
    current_A = current_mA / 1000.0
    power_w = voltage * current_A
    power_mw = power_w * 1000.0
        
    # Display the sensor data on the OLED screen, first is text and data, second is oled positional data
    oled.text(f"Volt: {voltage:.3f} V", 0, 2, 1)
        
    # conditional branch to switch between mA or A based on current magnitude
    if current_A >= 1.0:
        oled.text(f"Crnt: {current_A:.3f} A", 0, 12, 1)
    else:
        oled.text(f"Crnt: {current_mA:.2f} mA", 0, 12, 1)
        
    # conditional branch to switch between mw or W based on power magnitude
    if power_w >= 1.0:
        oled.text(f"Pwr: {power_w:.2f} W", 0, 22, 1)
    else:
        oled.text(f"Pwr: {power_mw:.2f} mW", 0, 22, 1)
            
    # Push buffer to screen
    oled.show()
            
    # 1 second refresh rate for data parsing from INA219 and screen refresh rate
    time.sleep(1)
