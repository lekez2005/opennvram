import numpy as np

from globals import OPTS
from mram_probe import MramProbe
from sim_steps_generator import SimStepsGenerator


class MramSimStepsGenerator(SimStepsGenerator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.control_sigs.append("write_trig")
        self.write_trig = self.prev_write_trig = 0

    def create_probe(self):
        self.probe = MramProbe(self.sram, OPTS.pex_spice)

    def initialize_sram(self, probe, existing_data):
        super().initialize_sram(probe, existing_data)
        if not OPTS.mram == "sot":
            return

        # initialize reference cells
        with open(OPTS.ic_file, "a") as ic:
            for bank_index in range(self.sram.num_banks):
                bank = self.sram.bank_insts[bank_index].mod
                pattern = self.probe.get_storage_node_pattern()
                pattern = pattern.replace("Xbit_r", "Xref_r")

                data = [0, 1]

                num_rows = bank.num_rows
                for i in range(0, OPTS.num_reference_cells, 2):
                    for ref_offset in range(2):
                        col_voltage = self.binary_to_voltage(data[ref_offset])
                        col = i * 2 + ref_offset
                        for row in range(num_rows):
                            col_node = pattern.format(bank=bank_index, row=row, col=col,
                                                      name="Xref")
                            self.write_ic(ic, col_node, col_voltage)
            ic.flush()

    def update_output(self, increment_time=True):
        if increment_time and not self.read:
            self.write_pwl("write_trig", 0, 1)

        super().update_output(increment_time)

        if increment_time and not self.read:
            self.write_pwl("write_trig", 1, 0)

    def get_setup_time(self, key, prev_val, curr_val):
        if key == "write_trig":
            if prev_val == 0:
                setup_time = self.slew
            else:
                trigger_delay = OPTS.write_trigger_delay
                setup_time = self.period - (self.duty_cycle * self.period + trigger_delay)
            return setup_time
        else:
            return super().get_setup_time(key, prev_val, curr_val)

    def binary_to_voltage(self, x):
        return 0.995 * ((x * 2) - 1)  # close to +-1 but not exactly equal for convergence reasons

    def write_ic(self, ic, col_node, col_voltage):
        phi = 0.1 * OPTS.llg_prescale
        theta = np.arccos(col_voltage) * OPTS.llg_prescale

        phi_node = col_node.replace(".state", ".phi")
        theta_node = col_node.replace(".state", ".theta")

        ic.write(".ic V({})={} \n".format(phi_node, phi))
        ic.write(".ic V({})={} \n".format(theta_node, theta))
