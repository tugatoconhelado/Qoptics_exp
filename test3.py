import dataclasses


@dataclasses.dataclass
class ImplantationParameters:
    emision_current: float = 10000
    energy: float = 5000
    extractor_voltage: float = 90.01
    focus_1_voltage: float = 75.00
    focus_2_voltage: float = 0.00
    position_x: float = 0
    position_y: float = 0
    width_x: float = 0
    width_y: float = 0
    blanking_x: float = 1
    blanking_y: float = 1
    blanking_level: float = 0
    time_per_dot: float = 50
    angle_phi: float = 0
    angle_theta: float = 0
    L: float = 33000
    M: float = 11500
    deflection_x: float = 48
    deflection_y: float = 67

@dataclasses.dataclass
class ImplantationSpot:
    total_parameters: ImplantationParameters = None
    implantation_time: float = 0
    position_x: float = 0
    position_y: float = 0
    extra_parameter: dict  = None

extra_parameter = {}
parameters = ImplantationParameters()
implantation_spot = ImplantationSpot(total_parameters=parameters, extra_parameter=extra_parameter)
print(implantation_spot)