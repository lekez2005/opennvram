# modules
bitcell = "reram_bitcell"
bitcell_mod = "reram_bitcell"
body_tap = "reram_bitcell.body_tap"

python_path = ["modules/reram"]

precharge_array = "bitline_discharge_array.BitlineDischargeArray"

write_driver_pmos_vdd = "vdd_br"

write_driver_array = "write_driver_pgate_array.WriteDriverPgateArray"
write_driver_mod = "write_driver_pgate_sep_vdd.WriteDriverPgateSeparateVdd"

write_driver_logic_size = 1.5
write_driver_buffer_size = 6

tri_gate_array = "tri_state_pgate_array.TriStatePgateArray"
tri_gate = "tri_state_pgate.TriStatePgate"
tri_state_buffer_size = 4