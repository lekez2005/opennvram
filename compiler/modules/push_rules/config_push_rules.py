import os

python_path = ["modules/push_rules", "modules/horizontal"]

baseline = False
mram = False
push = True

cells_per_group = 2
use_y_body_taps = True
use_x_body_taps = False
mirror_bitcell_y_axis = True
symmetric_bitcell = False
export_dummy_bitcell_pins = False
num_bitcell_dummies = 1

sram_class = "horizontal_sram.HorizontalSram"
bank_class = "horizontal_bank.HorizontalBank"
control_optimizer = "push_rules_optimizer.PushRulesOptimizer"
probe_class = "push_rules_probe.PushRulesProbe"


bitcell = "push_bitcell"
body_tap = "push_bitcell_array.bitcell_tap"

predecoder_flop = "ms_flop_horz_push_rot"

decoder_and_2 = "horizontal_decoder_and.and2"
decoder_and_2_tap = "horizontal_decoder_and.and2_tap"
decoder_and_3 = "horizontal_decoder_and.and3"
decoder_and_3_tap = "horizontal_decoder_and.and3_tap"
precharge = "precharge_horizontal"

tri_gate_class = "tri_gate_array_horizontal.tri_gate"

flop_class = "flop_array_horizontal.flop"

write_driver = "write_driver_array_horizontal.driver"
sense_amp_class = "sense_amp_array_horizontal.amp"

column_mux = "column_mux_array_horizontal.column_mux"
column_mux_array = "column_mux_array_horizontal.ColumnMuxArrayHorizontal"

control_buffers_class = "latched_control_logic.LatchedControlLogic"

# modules
decoder_flops = True
separate_vdd = False

bitcell_array = "push_bitcell_array"
wordline_driver = "wordline_buffer_no_enable_array"
decoder = "row_decoder_with_enable"
ms_flop_array = "flop_array_horizontal.FlopArray"
sense_amp_array = "sense_amp_array_horizontal.SenseAmpArray"
write_driver_array = "write_driver_array_horizontal.WriteDriverArray"
precharge_array = "precharge_array_horizontal.PrechargeArray"
tri_gate_array = "tri_gate_array_horizontal.TriGateArray"

control_flop = "ms_flop_horz_push_rot.ms_flop_horz_push"
flop_buffer = "flop_buffer_horizontal.FlopBufferHorizontal"

control_flop_buffers = [4]

run_optimizations = False

logic_buffers_height = 1.4

num_buffers = 5

max_buf_size = 60

num_clk_buf_stages = 5
max_clk_buffers = max_buf_size

num_wordline_en_stages = 4
max_wordline_en_buffers = max_buf_size

num_write_en_stages = 5
max_write_buffers = max_buf_size

num_sense_en_stages = 3
max_sense_en_size = max_buf_size

num_precharge_stages = 4
max_precharge_en_size = max_buf_size

num_wordline_driver_stages = 3
max_wordline_buffers = 20

num_predecoder_stages = 1
max_predecoder_inv_size = 20
max_predecoder_nand = 1.2

wordline_buffers = [5, 15]
wordline_beta = [0.9, 2.2]  # critical path is for Low to High

predecode_sizes = [1.2, 4]

sense_amp_type = "latched_sense_amp"

write_buffers = [1, 3.7, 13.6, 50]
wordline_en_buffers = [1, 3.7, 13.6, 50]

clk_buffers = [1, 5, 20, 65, 30]  # clk only used by decoders (no latches)
sampleb_buffers = [1, 3.7, 13.6, 50]

sense_amp_buffers = [1, 2.6, 6.7, 17.4, 45]
tri_en_buffers = [1, 2.6, 6.7, 17.4, 45]
precharge_buffers = [1, 3.9, 15, 60]
precharge_size = 1.5

# column_decoder_buffers = [4]
column_decoder_buffers = [2, 2]

# default sizes config
word_size = 64
num_words = 64
num_banks = 1
words_per_row = 1

# simulation
slew_rate = 0.005  # in nanoseconds
c_load = 1  # femto-farads
setup_time = 0.015  # in nanoseconds
feasible_period = 1.8  # in nanoseconds
duty_cycle = 0.35

sense_trigger_delay = 0.5

# temp dir
openram_temp = os.path.join(os.environ["SCRATCH"], "openram", "push_rules")

# schematic simulation's positive feedback loop may be hard to break
buffer_repeater_sizes = [
    ("clk_bar", ["clk_buf", "clk_bar"], [20, 20]),
    ("sense_en", ["sense_en"], [5, 15]),
    ("write_en", ["write_en"], [5, 15]),
    # ("sample_en_bar", ["sample_en_bar"], [5, 15]),
    ("tri_en", ["tri_en"], [5, 15]),
    ("precharge_en_bar", ["precharge_en_bar"], [10, 20]),
]
buffer_repeaters_col_threshold = 128


def configure_modules(bank, OPTS):
    num_rows = bank.num_rows
    num_cols = bank.num_cols
    if num_rows > 127:
        OPTS.max_wordline_en_buffers = 60
    else:
        OPTS.max_wordline_en_buffers = 30

    if num_cols < 100:
        OPTS.num_clk_buf_stages = 4
        OPTS.num_write_en_stages = 4
        OPTS.max_clk_buffers = 40
        OPTS.max_write_buffers = 40
        OPTS.precharge_size = 1.5
        # OPTS.tri_en_buffers = [, 11.7, 40, 40]
    else:
        OPTS.num_clk_buf_stages = 5
        OPTS.num_write_en_stages = 5
        OPTS.max_clk_buffers = 60
        OPTS.max_write_buffers = 60
        if OPTS.num_banks == 2:
            OPTS.precharge_size = 1.75
        else:
            OPTS.precharge_size = 1.75
        OPTS.tri_en_buffers = [1, 2.6, 6.7, 17.4, 45]
