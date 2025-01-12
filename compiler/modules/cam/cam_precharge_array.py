from base.geometry import NO_MIRROR, MIRROR_Y_AXIS
from base.vector import vector
from base.well_implant_fills import create_wells_and_implants_fills
from globals import OPTS
from modules.precharge_array import precharge_array


class CamPrechargeArray(precharge_array):

    def __init__(self, columns, size=1, has_precharge=True):
        self.has_precharge = has_precharge
        super().__init__(columns, size)

    def add_pins(self):
        """Adds pins for spice file"""
        for i in range(self.columns):
            self.add_pin("bl[{0}]".format(i))
            self.add_pin("br[{0}]".format(i))
        self.add_pin_list(self.control_pins)

    def get_cell_offset(self, column):
        offset = vector(self.bitcell_offsets[column], 0)
        if OPTS.symmetric_bitcell:
            mirror = NO_MIRROR
        else:
            offset.x += self.pc_cell.width
            mirror = MIRROR_Y_AXIS
        return offset, mirror

    def connect_inst(self, args, check=True):
        if self.insts[-1].mod == self.pc_cell:
            args = args[:2] + self.control_pins
        super().connect_inst(args, check)

    def create_modules(self):
        self.pc_cell = self.create_mod_from_str(OPTS.precharge, name="precharge",
                                                size=self.size,
                                                has_precharge=self.has_precharge)
        self.control_pins = self.pc_cell.pins[2:]
        self.child_mod = self.pc_cell
        self.body_tap = None

    def create_layout(self):
        self.add_insts()
        self.extend_pins()

    def extend_pins(self):
        for pin_name in self.control_pins:
            for pin in self.pc_cell.get_pins(pin_name):
                offset = pin.ll() + self.child_insts[0].ll()
                width = pin.rx() + self.child_insts[-1].lx() - offset.x
                self.add_layout_pin(pin_name, pin.layer, offset=offset, height=pin.height(),
                                    width=width)

    def extend_wells(self):
        for fill in create_wells_and_implants_fills(self.child_insts[0], self.child_insts[0]):
            layer, rect_bottom, rect_top, left_mod_rect, _ = fill
            offset = left_mod_rect.ll()
            width = left_mod_rect.rx() + self.child_insts[-1].lx() - offset.x
            self.add_rect(layer, offset=offset, width=width,
                          height=left_mod_rect.uy() - left_mod_rect.by())
