import pyvisa
from qudi.core.module import Base
from PySide2.QtCore import Signal


class SG384Hardware(Base):

    devices_signal = Signal(list)
    frequency_signal = Signal(float)
    amplitude_signal = Signal(float)
    phase_signal = Signal(int)
    deviation_signal = Signal(float)
    modulation_rate_signal = Signal(float)
    modulation_function_signal = Signal(int)
    modulation_type_signal = Signal(int)
    modulation_enable_signal = Signal(int)
    display_signal = Signal(int)
    outputs_enabled_signal = Signal(int, int, int)


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
        self._deviation = 0.7
        self._modulation_rate = 1
        self._modulation_function = 3
        self._enable_rf_output = 0
        self._enable_lf_output = 0
        self._enable_hf_output = 0
        self._display = 0

        self.frequency_units = 'Hz'
        self.amplitude_units = 'dBm'
        self.deviation_units = 'Hz'
        self.modulation_rate_units = 'Hz'

        self.modulation_function_dict = {
            0: 'MFNC',
            1: 'MFNC',
            2: 'MFNC',
            3: 'SFNC',
            4: 'PFNC',
            6: 'QFNC'
        }
        self.deviation_dict = {
            0: 'ADEP',
            1: 'FDEV',
            2: 'PDEV',
            3: 'SDEV'
        }
        self.modulation_rate_dict = {
            0: 'RATE',
            1: 'RATE',
            2: 'RATE',
            3: 'SRAT',
            6: 'RATE'
        }

    def on_activate(self) -> None:
        self.resource_manager = pyvisa.ResourceManager()

    def on_deactivate(self) -> None:
        pass

    # Status and display commands
    @property
    def display(self) -> int:
        display = self.instrument.query('DISP?').strip()
        return int(display)
    
    @display.setter
    def display(self, display: int) -> None:
        self.instrument.write(f'DISP {display}')
        self._display = self.display
        self.display_signal.emit(self.display)

    # Signal synthesis commands
    @property
    def frequency(self) -> float:
        frequency = self.instrument.query(f'FREQ? {self.frequency_units}').strip()
        return float(frequency)
    
    @frequency.setter
    def frequency(self, frequency: float) -> None:
        self.instrument.write(f'FREQ {frequency} {self.frequency_units}')
        self._frequency = self.frequency
        self.frequency_signal.emit(self.frequency)
    
    @property
    def amplitude(self) -> float:
        # For frequencies between DC and 62.5 MHz, the BNC Output is used
        # this output admits amplitudes between -47 dBm to 13 dBm
        # For frequencies between 950 kHz and 4.05 GHz, the Type-N Output is used
        # this output admits amplitudes between -110 dBm to 16.5 dBm
        # For frequencies between 4.05 GHz and 8.1 GHz, the RF Doubler Output is used
        # this output admits amplitudes between -10 to 16.5 dBm
        command = 'AMPR'
        if 950e3 < self.frequency < 4.05e9:
            command = 'AMPR'
        elif self.frequency < 62.5e6:
            command = 'AMPL'
        elif 4.05e9 < self.frequency < 8.1e9:
            command = 'AMPH'
        amplitude = self.instrument.query(f'{command}?').strip()
        return float(amplitude)

    @amplitude.setter
    def amplitude(self, amplitude: float) -> None:

        command = 'AMPR'
        if 950e3 < self.frequency < 4.05e9:
            command = 'AMPR'
        elif self.frequency < 62.5e6:
            command = 'AMPL'
        elif 4.05e9 < self.frequency < 8.1e9:
            command = 'AMPH'
        self.instrument.write(f'{command} {amplitude} {self.amplitude_units}')
        self._amplitude = self.amplitude
        self.amplitude_signal.emit(self.amplitude)
    
    @property
    def clock_amplitude(self) -> float:
        # Units are Vpp
        clock_amplitude = self.instrument.query('AMPC?').strip()
        return float(clock_amplitude)
    
    @clock_amplitude.setter
    def clock_amplitude(self, clock_amplitude: float) -> None:
        # Units are Vpp
        self.instrument.write(f'AMPC {clock_amplitude}')
        self._clock_amplitude = self.clock_amplitude
        self.clock_amplitude_signal.emit(self.clock_amplitude)

    @property
    def offset(self) -> float:
        offset = self.instrument.query('OFFS?').strip()
        return float(offset)
    
    @offset.setter
    def offset(self, offset: float) -> None:
        self.instrument.write(f'OFFS {offset}')
        self._offset = self.offset
        self.offset_signal.emit(self.offset)

    @property
    def phase(self) -> int:
        phase = self.instrument.query('PHAS?').strip()
        return int(phase)
    
    @phase.setter
    def phase(self, phase: int) -> None:
        self.instrument.write(f'PHAS {phase}')
        self._phase = self.phase
        self.phase_signal.emit(self.phase)

    @property
    def enable_rf_output(self) -> int:
        enable_rf_output = self.instrument.query('ENBR?').strip()
        return int(enable_rf_output)
    
    @enable_rf_output.setter
    def enable_rf_output(self, enable_rf_output: int) -> None:
        self.instrument.write(f'ENBR {enable_rf_output}')
        self._enable_rf_output = self.enable_rf_output

    @property
    def enable_hf_output(self) -> int:
        enable_hf_output = self.instrument.query('ENBH?').strip()
        return int(enable_hf_output)
    
    @enable_hf_output.setter
    def enable_hf_output(self, enable_hf_output: int) -> None:
        self.instrument.write(f'ENBH {enable_hf_output}')
        self._enable_hf_output = self.enable_hf_output

    @property
    def enable_lf_output(self) -> int:
        enable_lf_output = self.instrument.query('ENBL?').strip()
        return int(enable_lf_output)
    
    @enable_lf_output.setter
    def enable_lf_output(self, enable_lf_output: int) -> None:
        self.instrument.write(f'ENBL {enable_lf_output}')
        self._enable_lf_output = self.enable_lf_output

    # Modulation Commands
    @property
    def modulation_enable(self) -> int:
        modulation_enable = self.instrument.query('MODL?').strip()
        return int(modulation_enable)
    
    @modulation_enable.setter
    def modulation_enable(self, modulation_enable: int) -> None:
        self.instrument.write(f'MODL {modulation_enable}')
        self._modulation_enable = self.modulation_enable
        self.modulation_enable_signal.emit(self.modulation_enable)

    @property
    def modulation_type(self) -> int:
        modulation_type = self.instrument.query('TYPE?').strip()
        return int(modulation_type)

    @modulation_type.setter
    def modulation_type(self, modulation_type: int) -> None:
        self.instrument.write(f'TYPE {modulation_type}')
        self._modulation_type = self.modulation_type
        self.modulation_type_signal.emit(self.modulation_type)
    
    @property
    def modulation_function(self) -> int:
        command = self.modulation_function_dict[self.modulation_type]
        modulation_function = self.instrument.query(f'{command}?').strip()
        return int(modulation_function)
    
    @modulation_function.setter
    def modulation_function(self, modulation_function: int) -> None:
        command = self.modulation_function_dict[self.modulation_type]
        self.instrument.write(f'{command} {modulation_function}')
        self._modulation_function = self.modulation_function
        self.modulation_function_signal.emit(self.modulation_function)

    @property
    def modulation_rate(self) -> float:
        command = self.modulation_rate_dict[self.modulation_type]
        modulation_rate = self.instrument.query(f'{command}?').strip()
        return float(modulation_rate)
    
    @modulation_rate.setter
    def modulation_rate(self, modulation_rate: float) -> None:
        command = self.modulation_rate_dict[self.modulation_type]
        self.instrument.write(f'{command} {modulation_rate}')
        self._modulation_rate = self.modulation_rate
        self.modulation_rate_signal.emit(self.modulation_rate)
  
    @property
    def deviation(self) -> float:
        command = self.deviation_dict[self.modulation_type]
        deviation = self.instrument.query(f'{command}?').strip()
        return float(deviation)
    
    @deviation.setter
    def deviation(self, deviation: float) -> None:
        command = self.deviation_dict[self.modulation_type]
        self.instrument.write(f'{command} {deviation}')
        self._deviation = self.deviation
        self.deviation_signal.emit(self.deviation)
 
    def initialise(self):
        
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
        self.devices_signal.emit(resources)
        return resources

    def open_device(self, address: str) -> None:

        self.instrument = self.resource_manager.open_resource(address)
        id = self.instrument.query('*IDN?').strip()
        print(f'Opened device: {id}')
        return id

    def set_outputs(self, rf_output: int, hf_output: int, lf_output: int) -> None:

        self.enable_rf_output = rf_output
        self.enable_hf_output = hf_output
        self.enable_lf_output = lf_output
        self.outputs_enabled_signal.emit(
            self.enable_rf_output,
            self.enable_hf_output,
            self.enable_lf_output
        )

    def configure_frequency_sweep(
            self, frequency_centre: float, amplitude: float,
            sweep_deviation: float, modulation_rate: float = 1,
            sweep_modulation_function: int = 1
    ) -> None:

        print('Configuring frequency sweep')
        self.modulation_enable = 1
        self.modulation_type = 3 # Frequency sweep
        self.frequency = frequency_centre
        self.amplitude = amplitude
        self.deviation = sweep_deviation
        self.modulation_rate = modulation_rate
        self.modulation_function = sweep_modulation_function
        self.enable_rf_output = 1

        print(f'Setted modulation to {self.modulation_enable}')
        print(f'Setted sweep frequency to {self.frequency} GHz')
        print(f'Setted sweep amplitude to {self.amplitude} dBm')
        print(f'Setted SG to type {self.modulation_type}')
        print(f'Setted modulation function to {self.modulation_function}')
        print(f'Setted modulation rate to {self.modulation_rate} Hz')
        print(f'Setted sweep range to {self.deviation} GHz')
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
    #    deviation=0.7,
    #    amplitude=-15,
    #    modulation_function=1,
    #    modulation_rate=1
    #)
    #print(signal_generator.frequency)
    #signal_generator.frequency = 2.85
    #signal_generator.amplitude = -8
    #signal_generator.deviation = 0.5
    #signal_generator.modulation_rate = 2
    #signal_generator.modulation_function = 1
    #signal_generator.enable_rf_output = 0

    #print(signal_generator.frequency)
    #print(signal_generator.amplitude)
    #print(signal_generator.deviation)
    #print(signal_generator.modulation_rate)
    #print(signal_generator.modulation_function)
    #print(signal_generator.enable_rf_output)