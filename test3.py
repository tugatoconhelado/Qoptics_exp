import dataclasses

@dataclasses.dataclass
class ImplantationSpot:
    implantation_time: float = 0
    position_x: float = 0
    position_y: float = 0

ip = ImplantationSpot(1,2,3)
setattr(ip, 'wibble', 5)
print(ip)

