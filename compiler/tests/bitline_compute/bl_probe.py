from subprocess import CalledProcessError

import debug
from base import utils
from characterizer.sram_probe import SramProbe
from globals import OPTS


class BlProbe(SramProbe):
    """
    Adds probe labels to the sram such that the label names are partially retained post extraction
    The actual post extraction label is obtained using regex
    """

    def __init__(self, sram, pex_file=None):
        super().__init__(sram, pex_file)

        self.state_probes = {}
        self.sense_amp_probes = {}
        self.and_probes = {}
        self.nor_probes = {}
        self.decoder_probes = {}
        self.dout_probes = {}

    def probe_bitlines(self, bank):
        bank_inst = self.sram.bank_inst
        num_rows = self.sram.num_rows
        for col in range(self.sram.num_cols):

            if OPTS.use_pex:
                for pin_name in ["BL", "BR"]:
                    pin = utils.get_libcell_pins([pin_name], "cell_6t").get(pin_name)[0]
                    pin_label = "{}_c{}".format(pin_name, col)
                    self.add_pin_label(pin, [bank_inst, bank_inst.mod.bitcell_array_inst,
                                             bank_inst.mod.bitcell_array_inst.mod.cell_inst[num_rows-1, col]],
                                       pin_label)
                    self.probe_labels.add(pin_label)
                    if pin_name == "BL":
                        self.bitline_probes[col] = pin_label
            else:
                for pin_name in ["bl", "br"]:
                    pin_label = "Xsram.Xbank{}.{}[{}]".format(bank, pin_name, col)
                    self.probe_labels.add(pin_label)
                    if pin_name == "bl":
                        self.bitline_probes[col] = pin_label

    def probe_misc_bank(self, bank):
        bank_inst = self.sram.bank_inst

        nets = ["clk_buf", "wordline_en", "precharge_en", "write_en", "sense_en", "sense_en_bar"]

        if OPTS.use_pex:
            for net in nets:
                pin = bank_inst.mod.control_buffers.get_pin(net)
                pin_label = "{}".format(net)
                self.add_pin_label(pin, [bank_inst, bank_inst.mod.control_buffers_inst], pin_label)
                self.probe_labels.add(pin_label)
        else:
            for net in nets:
                self.probe_labels.add("Xsram.Xbank{}.{}".format(bank, net))

    def probe_address(self, address, pin_name="Q"):

        pin = utils.get_libcell_pins([pin_name], "cell_6t").get(pin_name)[0]

        address = self.address_to_vector(address)
        address_int = self.address_to_int(address)

        bank_index, bank_inst, row, col_index = self.decode_address(address)

        if OPTS.use_pex:
            decoder_label = "dec_r{}".format(row)
            if OPTS.baseline:
                decoder_pin = bank_inst.mod.decoder.get_pin("decode[{}]".format(row))
                self.add_pin_label(decoder_pin, [bank_inst, bank_inst.mod.right_decoder_inst], decoder_label)
            else:
                decoder_pin = bank_inst.mod.decoder_logic_mod.get_pin("out[{}]".format(row))
                self.add_pin_label(decoder_pin, [bank_inst, bank_inst.mod.decoder_logic_inst], decoder_label)
        else:
            if OPTS.baseline:
                decoder_label = "Xsram.Xbank{}.dec_out_0[{}]".format(bank_index, row)
            else:
                decoder_label = "Xsram.Xbank{}.wl_in[{}]".format(bank_index, row)
        self.decoder_probes[address_int] = decoder_label
        self.probe_labels.add(decoder_label)

        if OPTS.use_pex:
            wl_pin = utils.get_libcell_pins(["WL"], "cell_6t").get("WL")[0]
            wl_label = "wl_r{}".format(row)
            self.add_pin_label(wl_pin, [bank_inst, bank_inst.mod.bitcell_array_inst,
                                        bank_inst.mod.bitcell_array_inst.mod.cell_inst[row, self.sram.num_cols - 1]],
                               wl_label)
            self.wordline_probes[address_int] = wl_label
            self.probe_labels.add(wl_label)
        else:
            wl_label = "Xsram.Xbank{}.wl[{}]".format(bank_index, row)
            self.wordline_probes[address_int] = wl_label
            self.probe_labels.add(wl_label)

        pin_labels = [""] * self.sram.word_size
        for col in range(self.sram.num_cols):
            if OPTS.use_pex:
                pin_label = "{}r{}c{}".format(pin_name, row, col)
                self.add_pin_label(pin, [bank_inst, bank_inst.mod.bitcell_array_inst,
                                         bank_inst.mod.bitcell_array_inst.mod.cell_inst[row, col]], pin_label)
                pin_labels[col] = pin_label
            else:
                pin_labels[col] = "Xsram.Xbank{}.Xbitcell_array.Xbit_r{}_c{}.{}".format(bank_index, row, col, pin_name)

        self.probe_labels.update(pin_labels)
        self.state_probes[address_int] = pin_labels

    def probe_outputs(self):
        """Probes for sense amp outputs and, nor"""
        bank_inst = self.sram.bank_inst
        for col in range(self.sram.num_cols):
            # dout label
            dout_label = "D[{}]".format(col)
            self.dout_probes[col] = dout_label

            if not OPTS.baseline:
                if OPTS.use_pex:
                    and_pin = bank_inst.mod.sense_amp_array_inst.get_pin("and[{}]".format(col))
                    pin_label = "and_c{}".format(col)
                    self.add_pin_label(and_pin, [bank_inst, bank_inst.mod.sense_amp_array_inst], pin_label)
                    self.probe_labels.add(pin_label)
                    self.and_probes[col] = pin_label

                    nor_pin = bank_inst.mod.sense_amp_array_inst.get_pin("nor[{}]".format(col))
                    pin_label = "nor_c{}".format(col)
                    self.add_pin_label(nor_pin, [bank_inst, bank_inst.mod.sense_amp_array_inst], pin_label)
                    self.probe_labels.add(pin_label)
                    self.nor_probes[col] = pin_label
                else:
                    and_label = "Xsram.Xbank0.and_out[{}]".format(col)
                    self.and_probes[col] = and_label
                    self.probe_labels.add(and_label)

                    nor_label = "Xsram.Xbank0.nor_out[{}]".format(col)
                    self.nor_probes[col] = nor_label
                    self.probe_labels.add(nor_label)

    def add_pin_label(self, pin, module_insts, label_key):
        ll, ur = utils.get_pin_rect(pin, module_insts)
        pin_loc = [0.5 * (ll[0] + ur[0]), 0.5 * (ll[1] + ur[1])]
        # self.sram.add_rect(pin.layer, offset=ll, width=pin.width(), height=pin.height())
        self.sram.add_label(label_key, pin.layer, pin_loc)

    def extract_probes(self):
        """Extract probes from extracted pex file"""
        if OPTS.use_pex:
            self.saved_nodes = set()
            for label in self.probe_labels:
                try:
                    self.saved_nodes.add(self.extract_from_pex(label))
                except CalledProcessError:
                    debug.warning("Probe {} not found in extracted netlist".format(label))
            try:
                for col, col_label in self.and_probes.items():
                    self.and_probes[col] = self.extract_from_pex(col_label)
                for col, col_label in self.nor_probes.items():
                    self.nor_probes[col] = self.extract_from_pex(col_label)
                for col, col_label in self.bitline_probes.items():
                    self.bitline_probes[col] = self.extract_from_pex(col_label)
                for address, address_label in self.decoder_probes.items():
                    self.decoder_probes[address] = self.extract_from_pex(address_label)
                for address, address_labels in self.state_probes.items():
                    self.state_probes[address] = [self.extract_from_pex(address_label)
                                                  for address_label in address_labels]
            except CalledProcessError:  # ignore missing probe errors
                pass
        else:
            self.saved_nodes = set(self.probe_labels)