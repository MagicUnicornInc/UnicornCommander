export QUARK_BACKENDS="CPU,AMD_XDNA,AMD_ROCm"
export XRT_PATH="/opt/xilinx/xrt"
export XDNA_PATH="/opt/amd-xdna"
export LD_LIBRARY_PATH="$XRT_PATH/lib:$XDNA_PATH/lib:$LD_LIBRARY_PATH"
