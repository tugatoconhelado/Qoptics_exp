import nidaqmx
import time

def test_func(steps, direction):
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan('Dev2/port1/line0:2',  line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)
        task.start()

        for i in range(steps):
            interval = 0.0001
            if direction == 'Forward':
                #print('Moving forward...')
                #Retrocede solo si en ambas ocasiones DIR es True
                task.write([True, True, True])
                time.sleep(interval)
                task.write([False, False, False])
                time.sleep(interval)

            else:
                #print('Moving backward...')
                task.write([True, True, True])
                time.sleep(interval)
                task.write([False, True, False])
                time.sleep(interval)
        return True
    
class StepperMotorHardware:


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_position = 0


    def move_by_steps(self, steps, direction):

        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan('Dev2/port1/line0:2',  line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)
            task.start()

            for i in range(steps):
                interval = 0.0001
                if direction == 'Forward':
                    #print('Moving forward...')
                    #Retrocede solo si en ambas ocasiones DIR es True
                    task.write([True, True, True])
                    time.sleep(interval)
                    task.write([False, False, False])
                    time.sleep(interval)
                    self.current_position += 1

                else:
                    #print('Moving backward...')
                    task.write([True, True, True])
                    time.sleep(interval)
                    task.write([False, True, False])
                    time.sleep(interval)
                    self.current_position -= 1
        
    def go_to_position(self, position):
        
        steps = position - self.current_position
        direction = 'Forward' if steps > 0 else 'Backward'
        self.move_by_steps(abs(steps), direction)