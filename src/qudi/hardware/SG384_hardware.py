import pyvisa
from qudi.core.module import Base


class SG384Hardware(Base):

    def __init__(self, *args, **kwargs) -> None:
        """
        Some useful parameters to note when using the SG384
        TYPE: Modulation type
        ---------------------
            0 AM
            1 FM
            2 phase Modulation
            3 Sweep
            4 Pulse
            5 Blank
            6 IQ
        SFNC: Modulation Function
        -------------------------
            0 Sine wave
            1 Ramp
            2 Triangle
            5 External
        """
        super().__init__(*args, **kwargs)
        self.device_id = 27
        self.id = ''

        self._modulation_enable = 0
        self._modulation_type = 3
        self._frequency = 2.87
        self._amplitude = -15
        self._phase = 0
        self._sweep_deviation = 0.7
        self._modulation_sweep_rate = 1
        self._sweep_modulation_function = 3
        self._enable_rf_output = 0

        self.frequency_units = 'GHz'
        self.amplitude_units = 'dBm'
        self.sweep_deviation_units = 'GHz'
        self.modulation_sweep_rate_units = 'Hz'

    def on_activate(self) -> None:
        self.initialise()

    def on_deactivate(self) -> None:
        pass

    @property
    def modulation_enable(self) -> int:
        modulation_enable = self.instrument.query('MODL?').strip()
        return int(modulation_enable)
    
    @modulation_enable.setter
    def modulation_enable(self, modulation_enable: int) -> None:
        self.instrument.write(f'MODL {modulation_enable}')
        self._modulation_enable = self.modulation_enable

    @property
    def modulation_type(self) -> int:
        modulation_type = self.instrument.query('TYPE?').strip()
        return int(modulation_type)

    @modulation_type.setter
    def modulation_type(self, modulation_type: int) -> None:
        self.instrument.write(f'TYPE {modulation_type}')
        self._modulation_type = self.modulation_type

    @property
    def frequency(self) -> float:
        frequency = self.instrument.query(f'FREQ? {self.frequency_units}').strip()
        return float(frequency)
    
    @frequency.setter
    def frequency(self, frequency: float) -> None:
        self.instrument.write(f'FREQ {frequency} {self.frequency_units}')
        self._frequency = self.frequency
    
    @property
    def phase(self) -> int:
        phase = self.instrument.query('PHAS?').strip()
        return int(phase)
    
    @phase.setter
    def phase(self, phase: int) -> None:
        self.instrument.write(f'PHAS {phase}')
        self._phase = self.phase

    @property
    def amplitude(self) -> float:
        amplitude = self.instrument.query(f'AMPR? {self.amplitude_units}').strip()
        return float(amplitude)

    @amplitude.setter
    def amplitude(self, amplitude: float) -> None:
        self.instrument.write(f'AMPR {amplitude} {self.amplitude_units}')
        self._amplitude = self.amplitude

    @property
    def sweep_deviation(self) -> float:
        sweep_deviation = self.instrument.query(f'SDEV? {self.sweep_deviation_units}').strip()
        return float(sweep_deviation)
    
    @sweep_deviation.setter
    def sweep_deviation(self, sweep_deviation: float) -> None:
        self.instrument.write(f'SDEV {sweep_deviation} {self.sweep_deviation_units}')
        self._sweep_deviation = self.sweep_deviation

    @property
    def modulation_sweep_rate(self) -> float:
        modulation_sweep_rate = self.instrument.query(f'SRAT? {self.modulation_sweep_rate_units}').strip()
        return float(modulation_sweep_rate)
    
    @modulation_sweep_rate.setter
    def modulation_sweep_rate(self, modulation_sweep_rate: float) -> None:
        self.instrument.write(f'SRAT {modulation_sweep_rate} {self.modulation_sweep_rate_units}')
        self._modulation_sweep_rate = self.modulation_sweep_rate

    @property
    def sweep_modulation_function(self) -> int:
        sweep_modulation_function = self.instrument.query('SFNC?').strip()
        return int(sweep_modulation_function)
    
    @sweep_modulation_function.setter
    def sweep_modulation_function(self, sweep_modulation_function: int) -> None:
        self.instrument.write(f'SFNC {sweep_modulation_function}')
        self._sweep_modulation_function = self.sweep_modulation_function

    @property
    def enable_rf_output(self) -> int:
        enable_rf_output = self.instrument.query('ENBR?').strip()
        return int(enable_rf_output)
    
    @enable_rf_output.setter
    def enable_rf_output(self, enable_rf_output: int) -> None:
        self.instrument.write(f'ENBR {enable_rf_output}')
        self._enable_rf_output = self.enable_rf_output
    
    def initialise(self):
        
        self.resource_manager = pyvisa.ResourceManager()
        instruments = self.get_all_instruments()
        print(instruments)
        for instrument in instruments:
            if str(self.device_id) in instrument:
                print(f'Found signal generator: {instrument}')
                self.open_device(instrument)
                self.id = id
                return True
        return False

    def get_all_instruments(self):

        resources = self.resource_manager.list_resources()
        return resources

    def open_device(self, address: str) -> None:

        self.instrument = self.resource_manager.open_resource(address)
        id = self.instrument.query('*IDN?').strip()
        print(f'Opened device: {id}')
        return id

    def configure_frequency_sweep(
            self, frequency_centre: float, amplitude: float,
            sweep_deviation: float, modulation_sweep_rate: float = 1,
            sweep_modulation_function: int = 1
    ) -> None:

        self.instrument.write(f'MODL 1')
        self.instrument.write(f'TYPE 3') # Type 3 means frequency sweep

        modulation_status = self.instrument.query('MODL?').strip()
        type_status = self.instrument.query('TYPE?').strip()

        self.frequency = frequency_centre
        self.amplitude = amplitude
        self.sweep_deviation = sweep_deviation
        self.modulation_sweep_rate = modulation_sweep_rate
        self.sweep_modulation_function = sweep_modulation_function
        self.enable_rf_output = 0

        print(f'Setted modulation to {modulation_status}')
        print(f'Setted sweep frequency to {self.frequency} GHz')
        print(f'Setted sweep amplitude to {self.amplitude} dBm')
        print(f'Setted SG to type {type_status}')
        print(f'Setted modulation function to {self.sweep_modulation_function}')
        print(f'Setted modulation rate to {self.modulation_sweep_rate} Hz')
        print(f'Setted sweep range to {self.sweep_deviation} GHz')
        print(f'Setted rf output to {self.enable_rf_output}')


if __name__ == '__main__':

    signal_generator = SG384Hardware()
    signal_generator.initialise()
    signal_generator.modulation = 1
    signal_generator.modulation_type = 3
    print(signal_generator.modulation)
    print(signal_generator.modulation_type)
    #signal_generator.configure_frequency_sweep(
    #    frequency_centre=2.87,
    #    sweep_deviation=0.7,
    #    amplitude=-15,
    #    sweep_modulation_function=1,
    #    modulation_sweep_rate=1
    #)
    #print(signal_generator.frequency)
    #signal_generator.frequency = 2.85
    #signal_generator.amplitude = -8
    #signal_generator.sweep_deviation = 0.5
    #signal_generator.modulation_sweep_rate = 2
    #signal_generator.sweep_modulation_function = 1
    #signal_generator.enable_rf_output = 0

    #print(signal_generator.frequency)
    #print(signal_generator.amplitude)
    #print(signal_generator.sweep_deviation)
    #print(signal_generator.modulation_sweep_rate)
    #print(signal_generator.sweep_modulation_function)
    #print(signal_generator.enable_rf_output)