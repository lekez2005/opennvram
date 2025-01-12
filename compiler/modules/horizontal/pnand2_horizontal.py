from base import unique_meta, utils
from base.vector import vector
from modules.horizontal.pgate_horizontal import pgate_horizontal
from pgates.ptx_spice import ptx_spice


class pnand2_horizontal(pgate_horizontal, metaclass=unique_meta.Unique):
    all_pmos = True
    all_nmos = False
    num_poly_contacts = 2

    @classmethod
    def get_name(cls, size=1, beta=None):
        beta, beta_suffix = cls.get_beta(beta, size)
        name = "pnand2_horizontal_{:.3g}{}".format(size, beta_suffix).replace(".", "__")
        return name

    def add_pins(self):
        self.add_pin_list(["A", "B", "Z", "vdd", "gnd"])

    def get_power_indices(self, is_nmos):
        if is_nmos:
            return [0]
        else:
            return [0, 2]

    def get_output_indices(self, is_nmos):
        if is_nmos:
            return [2]
        else:
            return [1]

    def calculate_constraints(self):
        self.num_fingers = 2
        self.nmos_finger_width = utils.ceil(2 * self.min_tx_width * self.size)
        self.pmos_finger_width = utils.ceil(self.beta * self.min_tx_width * self.size)

    def get_ptx_connections(self):
        return [
            (self.pmos, ["vdd", "A", "Z", "vdd"]),
            (self.pmos, ["Z", "B", "vdd", "vdd"]),
            (self.nmos, ["Z", "B", "net1", "gnd"]),
            (self.nmos, ["net1", "A", "gnd", "gnd"])
        ]
