# SSD1306 modules
import machine
import framebuf
import math   
import time

# INA219 modules
import machine
from machine import Pin, I2C
import time
# Import from library saved on Pico
from ina219 import INA219

# SSD1306 config cmds
DISP_OFF = const(0xAE)         # Turn display off
HORIZ_MEM_ADD = const(0x20)    # Memory addressing mode set to horizontal
CTRL_BYTE = const(0x00)        # 0x00 signifies control byte to diffrentiate from visual/pixel data
START_LINE = const(0x40)       # Starting line
SEG_REMAP = const(0xA1)        # Segment re-map (Column 127 mapped to SEG0)
MLTPLX_RTO = const(0xA8)       # Set multiplex ratio
COM_OUT_SCAN = const(0xC8)     # COM output scan direction
DISP_OFFSET1 = const(0xD3)
DISP_OFFSET2 = const(0x00)     # Display offset
COM_PIN1 = const(0xDA)
COM_PIN2 = const(0x02)
COM_PIN3 = const(0x12)         # COM pins configuration
DISP_CLK_DR1 = const(0xD5)
DISP_CLK_DR2 = const(0x80)     # Display clock divide ratio / oscillator frequency
PRE_CHARGE1 = const(0xD9)
PRE_CHARGE2 = const(0xF1)      # Pre-charge Period
VCOMH_DESEL_LVL1 = const(0xDB)
VCOMH_DESEL_LVL2 = const(0x30) # VCOMH deselect level
CONTRAST_CTRL1 = const(0x81) 
CONTRAST_CTRL2 = const(0xFF)   # Contrast control (Set to max brightness)
FULL_DISP_ON = const(0xA4)     # ENTIRE display ON (Resume from RAM)
NORM_DISP = const(0xA6)        # Normal display (non-inverted) 
CHRG_PUMP_CTRL1 = const(0x8D)
CHRG_PUMP_CTRL2 = const(0x14)  # Charge pump control (Enables charge pump)
DISP_ON = const(0xAF)          # Display ON

COL_ADDR = const(0x21)
PAGE_ADDR = const(0x22)
I2C_ADDR = const(0x3c)

# BUILT-IN SSD1306 MINIMAL DRIVER (I2C)
class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height):

        self.width, self.height = width, height
        self.pages = self.height // 8 # Sections of screen are divided into 8 pixel tall "Pages", varies based on screen height
        self.buffer = bytearray(self.pages * self.width) # Buffer of size: pages*screen width (1 byte = 8 pixels)


        # MP's framebuffer is initialized, framebuffer is set to Monochrome & Vertical Least Significant Bit
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB) 

        # Loop iterates through various hex commands to configure OLED controller hardware
        for cmd in (DISP_OFF, HORIZ_MEM_ADD, CTRL_BYTE, START_LINE, SEG_REMAP, MLTPLX_RTO, self.height - 1, COM_OUT_SCAN, 
                    DISP_OFFSET1, DISP_OFFSET2, COM_PIN1, COM_PIN2 if self.width > 2 * self.height else COM_PIN3, DISP_CLK_DR1,  
                    DISP_CLK_DR2, PRE_CHARGE1, PRE_CHARGE2, VCOMH_DESEL_LVL1, VCOMH_DESEL_LVL2, CONTRAST_CTRL1, CONTRAST_CTRL2,
                    FULL_DISP_ON, NORM_DISP, CHRG_PUMP_CTRL1, CHRG_PUMP_CTRL2, DISP_ON):
            self.write_cmd(cmd) # Current command is written directly to screen/display chip

    def show(self): # Function to take drawn pixels sitting in RAM and display them on screen
        self.write_cmd(COL_ADDR); self.write_cmd(0); self.write_cmd(self.width - 1)
        self.write_cmd(PAGE_ADDR); self.write_cmd(0); self.write_cmd(self.pages - 1)
        self.write_framebuf() # sends byte array from RAM to display chip

class SSD1306_I2C(SSD1306): # SSD1306 class called here and specified to work w/ I2C

    def __init__(self, width, height, i2c, addr=I2C_ADDR):
        self.i2c, self.addr = i2c, addr
        super().__init__(width, height)

    def write_cmd(self, cmd): # Function to set configuration info to display chip
        self.i2c.writeto(self.addr, bytearray([CTRL_BYTE, cmd])) 

    def write_framebuf(self): # Bit block transfer of pixel data to screen 
        self.i2c.writeto(self.addr, b'\x40' + self.buffer) # 0x40 signifies following info is visual/pixel data

# Screen hardware initialization
i2c_ssd1306 = machine.I2C(1, sda=machine.Pin(26), scl=machine.Pin(27), freq=400000)
oled = SSD1306_I2C(128, 32, i2c_ssd1306) # change y-coordinate if using bigger screen (32 or 64)

# INA219 sensor initialization
i2c_ina219 = I2C(1, sda=Pin(26), scl=Pin(27), freq=400000)
sensor = INA219(i2c_ina219, addr=0x40) # note: 0x40 is default hardware I2C address for INA219
sensor.set_calibration_16V_400mA()

# Main Loop
while True:
    oled.fill(0)  # Wipe screen buffer clear
    
    # sensor data
    voltage = sensor.bus_voltage
    current = sensor.current
    power_w = voltage * (current / 1000.0) # implement branch to determine pwr magnitude and switch between W or mw
    power_mw = power_w * 1000.0

    # Display the sensor data on the OLED screen, first half is text, second is positional data
    oled.text(f"Volt: {voltage:.3f} V", 0, 2, 1)
    oled.text(f"Current: {current:.2f} mA", 0, 12, 1)
    oled.text(f"Pwr: {power_mw:.2f} mW", 0, 22, 1)
    
    # Push buffer to screen
    oled.show()
    
    # 1 second refresh rate for data parsing from INA219 and screen refresh rate
    time.sleep(1)
