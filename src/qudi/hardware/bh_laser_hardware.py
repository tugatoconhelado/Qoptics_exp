import nidaqmx


class BHLaserHardware:


    def __init__(self) -> None:
        
        self.settings = {
            'device': 'Dev1',
            'port': 'port0',
        }
        self.freq_dict = {
            0: [True, False, False, False],
            20: [False, True, False, False],
            50: [False, False, True, False],
            80: [False, False, False, True],
            1: [False, False, False, False]
        }

        self.__frequency = 0
        self.__power = 10
        self.__on_off_status = False


    @property
    def frequency(self) -> int:
        return self.__frequency
    
    @frequency.setter
    def frequency(self, value: int) -> None:
        self.__frequency = value

        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(
                "Dev1/port0/line9:12",
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE
            )
            task.start()
            task.write(self.freq_dict[value])

    @property
    def power(self) -> int:
        return self.__power
    
    @power.setter
    def power(self, value: int) -> None:
        self.__power = value

        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                "Dev1/ao3",
                min_val=0,
                max_val=10
            )
            task.start()
            task.write(value)

    @property
    def on_off_status(self) -> bool:
        return self.__on_off_status
    
    @on_off_status.setter
    def on_off_status(self, value: bool) -> None:
        self.__on_off_status = value

        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(
                "Dev1/port0/line8",
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE
            )
            task.start()
            task.write(value)
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(
                "Dev1/port0/line13",
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE
            )
            task.start()
            task.write(value)


if __name__ == '__main__':
    laser = BHLaserHardware()
    laser.frequency = 1
    laser.power = 0
    laser.on_off_status = False
    print(laser.frequency, laser.power, laser.on_off_status)