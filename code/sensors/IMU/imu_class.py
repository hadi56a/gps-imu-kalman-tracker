import time
from .accelerometer import accelerometer_configuration, read_accelerometer
from .gyroscope import gyroscope_configuration, read_gyroscope
from config import CTRL1_XL, CTRL2_G, OUT_X_L, CONFIG_MAG_FREQ, CONFIG_MAG_RANGE, CONFIG_MAG_SENSITIVITY
from utils import CSVHandler
from pathlib import Path

class IMU:
    """
    Classe pour la gestion des acqusitions de l'IMU.
    """
    def __init__(self, bus, addr, accel_range, accel_freq, gyro_range, gyro_freq, magneto_range, magneto_freq):
        # Initialisation du bus I2C
        self.bus = bus
        self.__addr = addr
        self.accel_range = accel_range
        self.accel_freq = accel_freq
        self.gyro_range = gyro_range
        self.gyro_freq = gyro_freq
        self.magneto_range = magneto_range
        self.magneto_freq = magneto_freq
        self.ctrl_reg1, self.ctrl_reg2 = self.magnetometer_configuration()

    def initialize_sensors(self):
        """
        Initialise les capteurs en écrivant dans leurs registres de configuration en fonction des paramètres de configuration précisés.

        Arguments:
        - XL_addr: l'adresse I2C du LSM6DSO 
        - accel_range: la range de l'accéléromètre
        - accel_freq: la fréquence d'acquisition de l'accélomètre
        - gyro_range: la range du gyroscope
        - gyro_freq: la fréquence d'acquisition du gyroscope
        """
        print(self.__addr, self.accel_range, self.accel_freq, self.gyro_range, self.gyro_freq)
        self.bus.write_byte_data(self.__addr, CTRL1_XL, accelerometer_configuration(self.accel_range, self.accel_freq))
        self.bus.write_byte_data(self.__addr, CTRL2_G, gyroscope_configuration(self.gyro_range, self.gyro_freq))
        time.sleep(0.1)

    def magnetometer_configuration(self):
        """
        Configure les paramètres du LIS3MDL pour le magnetometer.

        Arguments: 
        - magneto_range: la range du magnetometer
        - magneto_freq: la fréquence d'acquisition du magnetometer

        Résultat : les octets à écrire dans les registres CTRL_REG1 et CTRL_REG2 pour configurer le magnetometer
        """
        # Configuration du magnetometer
        magneto_range_value = CONFIG_MAG_RANGE[self.magneto_range]
        magneto_freq_value = CONFIG_MAG_FREQ[self.magneto_freq]
        ctrl_reg1 = (magneto_freq_value << 1)
        ctrl_reg2 = (magneto_range_value << 5)
        return ctrl_reg1, ctrl_reg2

    def read_raw_data(self, device_addr, start_register):
        """
        Lit 6 octets depuis le capteur à l'adresse spécifiée et retourne les valeurs signées.

        Arguments:
        - device_addr: l'adresse I2C du composant
        - start_register: l'addresse du premier registre à lire 

        Résultat: les données acquises de l'accéléromètre ou gyroscope sur ces 3 axes (en valeur entières brutes signées)
        """
        data = self.bus.read_i2c_block_data(device_addr, start_register, 6)
        x = data[0] | (data[1] << 8)
        y = data[2] | (data[3] << 8)
        z = data[4] | (data[5] << 8)

        # Convertir en valeurs signées 16 bits
        x = x - 65536 if x > 32767 else x
        y = y - 65536 if y > 32767 else y
        z = z - 65536 if z > 32767 else z
        return x, y, z
    
    def save_imu_data(self, imu_data, file_path):
        """
        Sauvegarde des données imu sur disque.

        Parameters
        ----------
        imu_data : tuple
            Les données imu à sauvegarder (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z).
        file_path : str
            Chemin du fichier.
        """
        file = CSVHandler(file_path)
        file.create_csv_with_header(['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z'])
        file.append_row(list(imu_data))
        return file_path

    def save_imu_data_sequence(self, imu_data, directory, index, prefix="imu_data", extension="csv"):
        """
        Sauvegarde des données imu dans une séquence de données numérotées.

        Parameters
        ----------
        imu_data : tuple
            Les données imu à sauvegarder (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z).
        directory : str | Path
            Répertoire dans lequel enregistrer les données imu.
        index : int
            Indice des données imu dans la séquence.
        prefix : str
            Préfixe du nom de fichier.

        Returns
        -------
        str
            Chemin du fichier sauvegardé.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        file_name = f"{prefix}_{index:06d}.{extension}"
        file_path = str(directory / file_name)

        return self.save_position(imu_data, file_path)

    def read_IMU(self):
        """
        Lit les données d'acquisition de l'IMU (accéléromètre et gyroscope)

        Arguments:
        - XL_addr: l'adresse I2C du LSM6DSO 
        - accel_range: la range de l'accéléromètre
        - gyro_range: la range du gyroscope

        Résultat: Les données acquises par l'accéléromètre (accel_x,accel_y,accel_z), le gyroscope (gyro_x,gyro_y,gyro_z)
        """
        accel_x,accel_y,accel_z = read_accelerometer(self.__addr, self.accel_range)
        gyro_x,gyro_y,gyro_z = read_gyroscope(self.__addr, self.gyro_range)
        return time.time(), (accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z)

    def read_magnetometer(self):
        """
        Lit les données du magnetometer et les convertit.

        Arguments:
        - magneto_range: la range du magnetometer

        Résultat: les données acquises par le magnetometer en unité physique sur les 3 axes
        """
        x, y, z = self.read_raw_data(self.__addr, OUT_X_L)
        
        sensitivity = CONFIG_MAG_SENSITIVITY[self.magneto_range]
        return x / sensitivity, y / sensitivity, z / sensitivity
