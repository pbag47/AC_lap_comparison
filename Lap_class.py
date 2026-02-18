
from SerializableObject_class import SerializableObject


class Sector(SerializableObject):
    attribute_types = dict(
        sector_number=int,
        sector_time=float,
    )

    def __init__(self,
                 number: int = 0,
                 time: float = 0,  # (s)
                 ):
        self.sector_number: int = number
        self.sector_time: float = time

    def __str__(self) -> str:
        return f"S{self.sector_number:.0f}: {self.sector_time:.3f}"

    @classmethod
    def __from_json__(cls, input_dict):
        if not input_dict["__class_name__"] == cls.__name__:
            raise TypeError(f"Unexpected class type {input_dict["__class_name__"]} when attempting to deserialize a Sector")
        del input_dict["__class_name__"]
        output = cls()
        for name, value in input_dict.items():
            setattr(output, name, cls.attribute_types[name](value))
        return output



class Lap(SerializableObject):
    attribute_types = dict(
        number=int,
        driver=str,
        lap_time=float,
        is_valid=bool,
        start_index=int,
    )

    def __init__(self,
                 number: int = 0,
                 driver: str = '_-driver-_',
                 start_index: int = 0,
                 ):
        self.number: int = number
        self.driver: str = driver
        self.lap_time: float = 0.0  # (s)
        self.is_valid: bool = False
        self.sectors: list[Sector] = []
        self.start_index: int = start_index

        #TODO: self.is_valid logic

    def set_times(self, sector_times: 3*[float]):
        self.sectors = []
        for sector_number in range(3):
            try:
                sector = Sector(
                    number=sector_number,
                    time=sector_times[sector_number]
                )
            except IndexError:
                sector = None
            self.sectors.append(sector)
        self.lap_time = sum(sector_times)

    def __str__(self) -> str:
        minutes, seconds = divmod(self.lap_time, 60)
        return f'Lap {self.number}, {minutes:.0f}:{seconds:.3f} {[str(sector) for sector in self.sectors]}'

    @classmethod
    def __from_json__(cls, input_dict):
        match input_dict["__class_name__"]:
            case "Sector":
                return Sector.__from_json__(input_dict)
            case cls.__name__:
                del input_dict["__class_name__"]
                output = cls()
                for name, value in input_dict.items():
                    try:
                        setattr(output, name, cls.attribute_types[name](value))
                    except KeyError as e:
                        if name == "sectors":
                            setattr(output, name, value)
                        else:
                            raise e
                return output
            case _:
                raise TypeError(f"Unexpected class type {input_dict["__class_name__"]} when attempting to deserialize a Lap")

