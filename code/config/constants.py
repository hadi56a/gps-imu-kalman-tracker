#############################################
##                 PATH                    ##
#############################################
ACQUISITION_ROOT = 'data/' # Chemin d'enregistrement des acquisitions

#############################################
##                 GPIO                    ##
#############################################
PORT_BUTTON = 27 # Port GPIO du Bouton
PORT_LED = 12 # Port GPIO de la LED

#############################################
##                  LCD                    ##
#############################################
LCD_DEVICE_ADDR = 0x27            # Adresse I2C de l'écran LCD

#############################################
##                  GPS                    ##
#############################################

# Adresses I2C et USB des composants
GNSS_DEVICE_ADDR = 0x20           # Adresse I2C du module GNSS

# Constantes des registres du GNSS
I2C_START_GET = 29
I2C_ID = 30
I2C_DATA_LEN_H = 31
I2C_DATA_LEN_L = 32
I2C_ALL_DATA = 33
I2C_GNSS_MODE = 34
I2C_SLEEP_MODE = 35

# Mode de sélection des satellites GNSS
GPS = 1
BEIDOU = 2
GPS_BEIDOU = 3
GLONASS = 4
GPS_GLONASS = 5
BEIDOU_GLONASS = 6
GPS_BEIDOU_GLONASS = 7

GNSS_MODES = {'gps':GPS,
              'beidou':BEIDOU,
              'glonass':GLONASS,
              'gps_beidou':GPS_BEIDOU,
              'gps_glonass':GPS_GLONASS,
              'beidou_glonass':BEIDOU_GLONASS,
              'gps_beidou_glonass':GPS_BEIDOU_GLONASS
            }
            
#############################################
##                  IMU                    ##
#############################################

# Adresses I2C et USB des composants
LSM6DSO_ADDR = 0x6b          # Adresse I2C du capteur LSM6DSO (Accéléromètre/Gyroscope)
LIS3MDL_ADDR = 0x1e          # Adresse I2C du capteur LIS3MDL (Magnétomètre)

# Constantes des registres de configuration de l'IMU
CTRL1_XL = 0x10                # Registre de configuration de l'accéléromètre
CTRL2_G = 0x11              # Registre de configuration du gyroscope
OUTX_L_A = 0x28               # Registre de lecture de l'accéléromètre
OUTX_L_G = 0x22                # Registre de lecture du gyroscope

OUTX_H_G = 0x23
OUTY_L_G = 0x24
OUTY_H_G = 0x25
OUTZ_L_G = 0x26
OUTZ_H_G = 0x27

OUTX_H_A = 0x29
OUTY_L_A = 0x2A
OUTY_H_A = 0x2B
OUTZ_L_A = 0x2C
OUTZ_H_A = 0x2D

# Mappages des fréquences (Hz) pour l'accéléromètre
CONFIG_XL_FREQ = {
    0.0:    0b0000,  # Power-down
    12.5:   0b0001,
    26:     0b0010,
    52:     0b0011,
    104:    0b0100,
    208:    0b0101,
    416:    0b0110,
    833:    0b0111,
    1666:   0b1000,
    3332:   0b1001,
    6664:   0b1010
}

# Mappages des plages (full-scale range) pour l'accéléromètre
CONFIG_XL_RANGE = {
    2:   0b00,
    16:  0b01,
    4:   0b10, 
    8:   0b11   
}

# Sensibilités des capteurs pour conversion des données brutes en unités physiques
CONFIG_XL_SENSITIVITY = {
    2:  0.061,
    4:  0.122,
    8:  0.244,
    16: 0.488
}

# Mappages des fréquences (Hz) pour le gyroscope
CONFIG_G_FREQ = {
    0.0:    0b0000,  # Power-down
    12.5:   0b0001,
    26:     0b0010,
    52:     0b0011,
    104:    0b0100,
    208:    0b0101,
    416:    0b0110,
    833:    0b0111,
    1666:   0b1000,
    3332:   0b1001,
    6664:   0b1010
}

# Mappages des plages (full-scale range) pour le gyroscope
CONFIG_G_RANGE = {
    125:   0b0001,
    250:   0b0000,
    500:   0b0010,
    1000:  0b0100,
    2000:  0b0110  
}

# Sensibilités des capteurs pour conversion des données brutes en unités physiques
CONFIG_G_SENSITIVITY = {
    125:  4.375,  # mdps/LSB
    250:  8.75,
    500:  17.50,
    1000: 35.0,
    2000: 70.0
}

#############################################
##              MAGNETOMETRE               ##
#############################################
CTRL_REG1 = 0x20  # Registre de configuration du magnetometre (frequence)
CTRL_REG2 = 0x21  # Registre de configuration du magnetometre (plage)
OUT_X_L = 0x28  # Registre de lecture du magnetometre

# Mappages des frequences (Hz) pour le magnetometre
CONFIG_MAG_FREQ = {
    0.625: 0b000000,
    1.25: 0b000010,
    2.5: 0b000100,
    5: 0b000110,
    10: 0b001000,
    20: 0b001010,
    40: 0b001100,
    80: 0b001110,
    155: 0b110001,
    300: 0b100001,
    560: 0b010001,
    1000: 0b000001,
}

# Mappages des plages (full-scale range) pour le magnetometre
CONFIG_MAG_RANGE = {
    4: 0,  # +/-4 gauss
    8: 1,  # +/-8 gauss
    12: 2,  # +/-12 gauss
    16: 3,  # +/-16 gauss
}

# Sensibilites du magnetometre pour convertir les donnees brutes
CONFIG_MAG_SENSITIVITY = {
    4: 6842,  # LSB/gauss
    8: 3421,  # LSB/gauss
    12: 2281,  # LSB/gauss
    16: 1711,  # LSB/gauss
}

