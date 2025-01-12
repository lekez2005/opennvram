from base import unique_meta, contact, utils
from base.design import design, PIMP, NIMP, NWELL, ACTIVE, METAL1, PWELL
from base.vector import vector
from modules.horizontal.pgate_horizontal import pgate_horizontal
from tech import drc


class pgate_horizontal_tap(design, metaclass=unique_meta.Unique):
    @classmethod
    def get_name(cls, pgate_mod: pgate_horizontal):
        name = "pgate_push_tap_{}".format(pgate_mod.max_tx_mults)
        return name

    def __init__(self, pgate_mod: pgate_horizontal):
        design.__init__(self, self.name)
        if pgate_mod.num_instances > 1:
            pgate_mod = pgate_mod.instances_mod
        self.pgate_mod = pgate_mod
        self.create_layout()

    def create_layout(self):
        self.add_implants()
        self.add_contacts()
        self.add_rect("boundary", offset=vector(0, 0), width=self.width, height=self.height)

    def add_implants(self):
        dut_layers = [NIMP, PIMP]

        tap_layers = [PIMP, NIMP]

        wells = [PWELL, NWELL]

        implant_space = self.implant_space

        tap_rect = None

        # prevent contact clash with z pin
        z_pin = self.pgate_mod.get_pin("Z")
        contact_mid = (-(self.pgate_mod.width - z_pin.rx()) +
                       self.get_parallel_space(METAL1) +
                       0.5 * contact.well.second_layer_width)
        # make implant cover contact active
        min_implant_width = contact.well.first_layer_width + 2 * self.implant_enclose_active

        for i in range(2):
            dut_rect = self.pgate_mod.get_layer_shapes(dut_layers[i])[0]
            dut_rect_height = dut_rect.uy() if i == 0 else (self.pgate_mod.height - dut_rect.by())
            tap_implant_height = dut_rect_height - implant_space
            min_area = drc.get("minarea_implant", 0)
            tap_implant_width = utils.ceil(max(self.implant_width,
                                               min_area / tap_implant_height,
                                               min_implant_width))
            implant_y = 0 if i == 0 else dut_rect.by() + implant_space
            implant_x = max(dut_rect.rx() - self.pgate_mod.width,
                            contact_mid - 0.5 * tap_implant_width)

            tap_rect = self.add_rect(tap_layers[i], offset=vector(implant_x, implant_y),
                                     width=tap_implant_width, height=tap_implant_height)
            if i == 1 or self.has_pwell:
                well_rect = self.pgate_mod.get_max_shape(wells[i], "lx")
                well_right = tap_rect.rx() + (self.well_enclose_active - self.implant_enclose_active)

                well_left = min(0, tap_rect.lx() - (self.well_enclose_active - self.implant_enclose_active))
                self.add_rect(wells[i], offset=vector(well_left, well_rect.by()),
                              width=well_right - well_left, height=well_rect.height)

        self.width = tap_rect.rx() + tap_rect.lx()  # prevent right adjacent implant overlap
        self.height = self.pgate_mod.height

    def add_contacts(self):
        active_enclosure = self.implant_enclose_active
        poly_extension = self.poly_to_active - 0.5 * self.poly_to_field_poly

        tap_layers = [PIMP, NIMP]
        pin_names = ["gnd", "vdd"]

        for i in range(2):
            implant = self.get_layer_shapes(tap_layers[i])[0]

            # avoid clash with poly

            active_left = max(implant.lx() + active_enclosure, poly_extension)
            active_right = self.width - active_left
            active_width = active_right - active_left

            active_space = self.get_space_by_width_and_length(ACTIVE, max_width=active_width)

            if i == 0:
                active_top = implant.uy() - active_enclosure
                active_bottom = implant.by() + 0.5 * active_space
            else:
                active_top = self.height - max(0.5 * active_space, self.well_enclose_active)
                active_bottom = implant.by() + active_enclosure

            active_height = active_top - active_bottom

            offset = vector(0.5 * (active_right + active_left),
                            0.5 * (active_top + active_bottom))

            self.add_rect_center(ACTIVE, offset=offset, width=active_width, height=active_height)

            num_contacts = self.calculate_num_contacts(active_height)
            self.add_contact_center(contact.well.layer_stack, offset=offset,
                                    size=[1, num_contacts])

            target_pin = self.pgate_mod.get_pin(pin_names[i])
            self.add_rect(target_pin.layer, offset=vector(0, target_pin.by()),
                          width=self.width, height=target_pin.height())
            self.add_rect(METAL1, offset=vector(offset.x - 0.5 * self.m1_width,
                                                offset.y), height=target_pin.cy() - offset.y)
