from qudi.hardware import spinapi

spinapi.pb_select_board(0)
spinapi.pb_init()
spinapi.pb_start_programming(spinapi.PULSE_PROGRAM)

start = spinapi.pb_inst_pbonly(spinapi.ON | 0x01, spinapi.CONTINUE, 0, 200.0 * spinapi.ms)
spinapi.pb_inst_pbonly(0x00, spinapi.BRANCH, 0, 200.0 * spinapi.ms)

spinapi.pb_stop_programming()
spinapi.pb_start()
spinapi.pb_close()