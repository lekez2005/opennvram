#!/usr/bin/env python3

from char_test_base import CharTestBase


class TriStateIn(CharTestBase):
    instantiate_dummy = True

    def runTest(self):
        import debug
        from globals import OPTS

        from modules.tri_gate_array import tri_gate_array

        OPTS.check_lvsdrc = False
        self.run_drc_lvs = False

        cols = 64
        pin = "en"

        load = tri_gate_array(columns=cols, word_size=cols)

        self.load_pex = self.run_pex_extraction(load, "tristate")
        self.dut_name = load.name

        self.period = "800ps"

        dut_instance = "X4 "

        for col in range(cols):
            dut_instance += " in[{0}] ".format(col)
        for col in range(cols):
            dut_instance += " out[{0}] ".format(col)

        # en pin is just before en_bar pin
        if pin == "en":
            dut_instance += " d d_dummy "
        else:
            dut_instance += " d_dummy d "

        dut_instance += " vdd gnd tri_gate_array \n"

        self.dut_instance = dut_instance

        self.run_optimization()

        with open(self.stim_file_name.replace(".sp", ".log"), "r") as log_file:
            for line in log_file:
                if line.startswith("Optimization completed"):
                    cap_val = float(line.split()[-1])
                    debug.info(1, "Cap = {:2g}fF".format(cap_val*1e15))
                    debug.info(1, "Cap per tri state_en = {:2g}fF".format(cap_val*1e15/cols))


TriStateIn.run_tests(__name__)