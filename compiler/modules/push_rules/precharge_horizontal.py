import tech
from base import contact, utils
from base.contact import m1m2, m2m3
from base.design import METAL1, PO_DUMMY, ACTIVE, POLY, PIMP, NIMP, NWELL, CONTACT, METAL2, METAL3
from base.hierarchy_layout import GDS_ROT_270
from base.vector import vector
from base.well_active_contacts import get_max_contact
from base.well_implant_fills import calculate_tx_metal_fill
from modules.precharge import precharge
from modules.push_rules.push_bitcell_array import push_bitcell_array
from tech import drc, layer as tech_layers


class precharge_horizontal(precharge):
    rotation_for_drc = GDS_ROT_270

    def set_layout_constants(self):
        # Initially calculate offsets assuming max active will be used and there will be space between poly
        self.poly_x_offset = 0.5 * self.poly_to_field_poly
        poly_to_mid_contact = 0.5 * contact.poly.first_layer_height

        self.gate_contact_x = (self.poly_x_offset + poly_to_mid_contact
                               - 0.5 * self.contact_width)
        self.pin_right_x = self.gate_contact_x + 0.5 * self.contact_width + 0.5 * self.m1_width
        self.active_x = self.pin_right_x + self.get_line_end_space(METAL1)

        poly_to_active_x = self.active_x - self.poly_x_offset

        max_poly_right = self.width - self.poly_x_offset
        max_active_right = max_poly_right - self.poly_extend_active
        max_width = max_active_right - self.active_x

        if self.ptx_width > max_width:
            # re-calculate assuming no space between poly
            self.poly_x_offset = - poly_to_mid_contact
            self.active_x = self.poly_x_offset + poly_to_active_x
            max_active_right = self.width - 0.5 * self.poly_extend_active
            max_width = max_active_right - self.active_x
            has_poly_space = False
        else:
            has_poly_space = True

        assert max_width > self.ptx_width, "Maximum size supported is {:.3g}".format(
            max_width / self.min_tx_width / self.beta)

        # centralize active and recalculate poly and active offsets
        self.mid_x = 0.5 * self.width
        self.active_x = utils.round_to_grid(self.mid_x - 0.5 * self.ptx_width)
        self.active_right = self.active_x + self.ptx_width

        if has_poly_space:
            self.poly_x_offset = self.active_x - poly_to_active_x
            self.gate_contact_x = (self.poly_x_offset + poly_to_mid_contact
                                   - 0.5 * self.contact_width)
            self.poly_right_x = self.active_right + self.poly_extend_active
        else:
            self.poly_right_x = max(self.width, self.active_right + self.poly_extend_active)
            self.gate_contact_x = -0.5 * self.contact_width
        self.has_poly_space = has_poly_space

        self.implant_x = min(0, self.poly_x_offset - self.implant_enclose_poly)
        self.implant_right = max(self.width, self.poly_right_x + self.implant_enclose_poly)

        # Calculate active y offsets
        active_to_poly = (drc["active_enclosure_contact"] + self.contact_width
                          + self.contact_to_gate)
        self.insert_poly_dummies = PO_DUMMY in tech_layers
        if self.insert_poly_dummies:
            self.dummy_y = -0.5 * self.poly_width
            self.poly_y = self.dummy_y + 2 * self.poly_pitch
            self.active_y = self.poly_y - active_to_poly
        else:
            self.active_y = 0.5 * self.get_wide_space(ACTIVE)
            self.poly_y = self.active_y + active_to_poly

        self.poly_top = self.poly_y + 2 * self.poly_pitch + self.poly_width
        self.active_top = self.poly_top + active_to_poly
        self.active_mid_y = 0.5 * (self.active_y + self.active_top)
        self.implant_bottom = min(0, self.active_y - self.implant_enclose_ptx_active)
        # Calculate well contacts offsets
        if self.insert_poly_dummies:
            self.dummy_top = self.poly_y + 4 * self.poly_pitch + self.poly_width
            self.contact_active_y = self.dummy_top + drc["poly_dummy_to_active"]
            self.implant_top = self.contact_active_y - self.implant_enclose_active
        else:
            self.implant_top = self.active_top + self.implant_enclose_ptx_active
            self.contact_active_y = self.implant_top + self.implant_enclose_active
        self.contact_implant_top = self.implant_top + self.implant_width
        self.contact_active_top = max(contact.well.first_layer_height,
                                      self.contact_implant_top - self.implant_enclose_active)
        self.contact_implant_top = max(self.contact_implant_top, self.contact_active_top
                                       + self.implant_enclose_active)
        self.height = self.contact_implant_top

    def create_ptx(self):
        # add active
        self.active_rect = self.add_rect(ACTIVE, offset=vector(self.active_x, self.active_y),
                                         width=self.ptx_width, height=self.active_top - self.active_y)
        # add poly
        poly_width = self.poly_right_x - self.poly_x_offset
        if self.insert_poly_dummies:
            layers = [PO_DUMMY, PO_DUMMY, POLY, POLY, POLY, PO_DUMMY, PO_DUMMY]
            y_offset = self.dummy_y
            poly_width = max(drc["po_dummy_min_height"], poly_width)
        else:
            layers = [POLY] * 3
            y_offset = self.poly_y
        for i in range(len(layers)):
            self.add_rect(layers[i], offset=vector(self.poly_x_offset,
                                                   y_offset + i * self.poly_pitch),
                          height=self.poly_width, width=poly_width)
        # add implants
        layers = [PIMP, NIMP]
        y_offsets = [[self.implant_bottom, self.implant_top],
                     [self.implant_top, self.contact_implant_top]]
        x_offsets = [[self.implant_x, self.implant_right],
                     [min(self.implant_x, -self.implant_enclose_active),
                      self.width + self.implant_enclose_active]]
        for i in range(2):
            self.add_rect(layers[i], offset=vector(x_offsets[i][0], y_offsets[i][0]),
                          width=x_offsets[i][1] - x_offsets[i][0],
                          height=y_offsets[i][1] - y_offsets[i][0])

        # Add Nwell
        nwell_top = self.contact_implant_top + self.well_enclose_active
        nwell_left = min(- self.well_enclose_active, self.implant_x)
        nwell_right = max(self.width + self.well_enclose_active, self.implant_right)
        self.add_rect(NWELL, offset=vector(nwell_left, 0), height=nwell_top,
                      width=nwell_right - nwell_left)

        if hasattr(tech, "add_tech_layers"):
            tech.add_tech_layers(self)

    def connect_input_gates(self):
        # add en pin
        pin_height = self.bus_width
        pin_x = - 0.5 * m2m3.second_layer_width
        en_pin = self.add_layout_pin("en", METAL3, offset=vector(pin_x, 0),
                                     width=self.width - pin_x, height=pin_height)
        # add vias to M3 and fill m2
        bl_pin = self.bitcell.get_pin("bl")
        fill_width = min(m2m3.height, 2 * (bl_pin.lx() - self.get_parallel_space(METAL2)))
        _, fill_height = self.calculate_min_area_fill(fill_width, layer=METAL2)
        if fill_height:
            self.add_rect(METAL2, offset=vector(-0.5 * fill_width, 0), width=fill_width,
                          height=fill_height)
        via_offset = vector(0, 0.5 * m2m3.height)
        for via in [m1m2, m2m3]:
            self.add_contact_center(via.layer_stack, offset=via_offset)
        # connect poly with M1
        poly_contact_y = 0
        for i in range(3):
            poly_contact_y = (self.poly_y + i * self.poly_pitch + 0.5 * self.poly_width
                              - 0.5 * self.contact_width)
            self.add_rect(CONTACT, offset=vector(self.gate_contact_x, poly_contact_y))
        m1_extension = utils.round_to_grid(0.5 * (contact.poly.second_layer_height
                                                  - contact.poly.contact_width))

        x_offset = self.gate_contact_x + 0.5 * self.contact_width - 0.5 * self.m1_width
        y_offset = self.poly_y + 0.5 * self.contact_width - 0.5 * contact.poly.second_layer_height
        y_top = poly_contact_y + self.contact_width + m1_extension
        self.add_rect(METAL1, offset=vector(x_offset, y_offset),
                      height=y_top - y_offset)
        self.add_rect(METAL1, offset=vector(-0.5 * self.m1_width, y_offset),
                      width=x_offset - (-0.5 * self.m1_width), height=self.m1_width)
        self.add_rect(METAL1, offset=vector(-0.5 * self.m1_width, 0), height=y_offset,
                      width=self.m1_width)

    def add_nwell_contacts(self):
        num_contacts = self.calculate_num_contacts(self.width - self.contact_spacing)
        active_rect = self.add_rect(ACTIVE, offset=vector(0, self.contact_active_y),
                                    width=self.width,
                                    height=self.contact_active_top - self.contact_active_y)
        contact_pitch = self.contact_width + self.contact_spacing
        total_contact = (contact_pitch * (num_contacts - 1)
                         + self.contact_width)
        x_offset = self.mid_x - 0.5 * total_contact
        y_offset = active_rect.cy() - 0.5 * self.contact_width
        for i in range(num_contacts):
            self.add_rect(CONTACT, offset=vector(x_offset, y_offset))
            x_offset += contact_pitch

        pin_height = max(self.rail_height, 2 * (self.height - active_rect.cy()))
        pin_top = min(self.height, active_rect.cy() + 0.5 * pin_height)
        self.add_layout_pin("vdd", METAL1, offset=vector(-0.5 * self.m1_width, pin_top - pin_height),
                            width=self.width + self.m1_width, height=pin_height)

    def get_mid_contact_y(self, source_drain_index):
        """Get y offset of active contact for given source_drain_index"""
        base_y = self.poly_y - self.contact_to_gate - self.contact_width
        return base_y + source_drain_index * self.poly_pitch + 0.5 * self.contact_width

    def add_active_contacts(self):
        tx_width = self.ptx_width
        if not self.has_poly_space:
            space = self.get_line_end_space(METAL1)
            # leave space for poly_m1 on the left and and vdd on the right
            tx_width = min(tx_width, self.width - 2 * (0.5 * self.m1_width + space))
        sample_contact = self.calculate_num_contacts(tx_width, return_sample=True)
        self.sample_contact = sample_contact

        # calculate fill
        _, fill_width = self.calculate_min_area_fill(sample_contact.second_layer_width, layer=METAL1)
        if fill_width > sample_contact.second_layer_height:
            # fill height based on adjacent vdd (min width fill)
            parallel_space = self.get_parallel_space(METAL1)
            fill_top = self.poly_pitch - parallel_space - 0.5 * sample_contact.second_layer_width
            # fill height based on adjacent bl br fills
            fill_bottom = 0.5 * (self.poly_pitch - parallel_space)
            _, fill_width = self.calculate_min_area_fill(fill_top + fill_bottom, layer=METAL1)
            fill_width = max(fill_width, sample_contact.second_layer_height)
        else:
            fill_width = fill_top = fill_bottom = None

        vdd_rail_x = max(self.width - 0.5 * self.bus_width,
                         self.active_rect.cx() + 0.5 * sample_contact.second_layer_height +
                         self.get_line_end_space(METAL1))

        self.fill_rects = []

        for i in range(4):
            y_offset = self.get_mid_contact_y(i)
            self.add_contact_center(layers=sample_contact.layer_stack,
                                    size=sample_contact.dimensions,
                                    offset=vector(self.active_rect.cx(), y_offset),
                                    rotate=90)
            if i in [0, 3]:
                if i == 0:
                    rail_y = y_offset + 0.5 * sample_contact.second_layer_width - self.bus_width
                else:
                    rail_y = y_offset - 0.5 * sample_contact.second_layer_width
                rail_x = self.active_rect.cx() - 0.5 * sample_contact.second_layer_height
                self.add_rect(METAL1, offset=vector(rail_x, rail_y), height=self.bus_width,
                              width=vdd_rail_x - rail_x)
            else:
                fill_x = self.active_rect.cx() - 0.5 * sample_contact.height
                if fill_width:
                    if i == 1:
                        fill_y = y_offset - fill_top
                    else:
                        fill_y = y_offset - fill_bottom
                    fill_height = fill_top + fill_bottom
                else:
                    fill_height = sample_contact.second_layer_width
                    fill_y = y_offset - 0.5 * fill_height
                rect = self.add_rect(METAL1, offset=vector(fill_x, fill_y),
                                     width=fill_width, height=fill_height)
                self.fill_rects.append(rect)

        rail_y = self.get_mid_contact_y(0) + 0.5 * sample_contact.second_layer_width - self.bus_width
        rail_width = 2 * (self.width - vdd_rail_x)
        self.add_rect(METAL1, offset=vector(vdd_rail_x, rail_y), height=self.height - rail_y,
                      width=rail_width)

    def connect_bitlines(self):
        en_pin = self.get_pin("en")
        bitline_y = en_pin.uy() + self.get_line_end_space(METAL3)
        drain_indices = [1, 2]
        pin_names = ["BL", "BR"]
        adjacent_names = ["BR", "BL"]
        for i in range(2):
            bitcell_pin = self.bitcell.get_pin(pin_names[i])
            adjacent_pin = self.bitcell.get_pin(adjacent_names[i])
            if i == 0:
                max_x = adjacent_pin.lx() - self.get_line_end_space(METAL2)
                min_x = max(bitcell_pin.lx(), self.active_rect.lx())
            else:
                min_x = adjacent_pin.rx() + self.get_line_end_space(METAL2)
                max_x = min(bitcell_pin.rx(), self.active_rect.rx())

            y_offset = self.get_mid_contact_y(drain_indices[i])
            cont = get_max_contact(m1m2.layer_stack, max_x - min_x)
            cont_inst = self.add_contact_center(m1m2.layer_stack,
                                                size=cont.dimensions,
                                                offset=vector(0.5 * (min_x + max_x), y_offset),
                                                rotate=90)
            fill_rect = self.fill_rects[i]
            if i == 0:
                x_offset = min(self.active_rect.cx(), cont_inst.lx())
                self.add_rect(METAL1, vector(x_offset, fill_rect.by()),
                              height=fill_rect.height,
                              width=cont_inst.rx() - x_offset)
            else:
                right_x = max(self.active_rect.cx(), cont_inst.rx())
                self.add_rect(METAL1, vector(cont_inst.lx(), fill_rect.by()), height=fill_rect.height,
                              width=right_x - cont_inst.lx())

            self.add_rect(METAL2, offset=vector(bitcell_pin.lx(), y_offset - 0.5 * self.m2_width),
                          width=self.mid_x - bitcell_pin.lx())

            self.add_layout_pin(pin_names[i].lower(), METAL2, offset=vector(bitcell_pin.lx(), bitline_y),
                                width=bitcell_pin.width(),
                                height=self.height - bitline_y)

    def drc_fill(self):
        pass