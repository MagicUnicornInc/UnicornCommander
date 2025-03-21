import quark
import onnxruntime

print(f"Quark version: {quark.__version__}")
print(f"OnnxRuntime version: {onnxruntime.__version__}")
print(f"Available providers: {onnxruntime.get_available_providers()}")

try:
    print("\nTrying to detect AMD XDNA provider:")
    if "XDNAExecutionProvider" in onnxruntime.get_available_providers():
        print("AMD XDNA provider available - Your XDNA NPU is detected\!")
    else:
        print("AMD XDNA provider not available")
        
    if "ROCMExecutionProvider" in onnxruntime.get_available_providers():
        print("AMD ROCm provider available - Your AMD GPU is detected\!")
    else:
        print("AMD ROCm provider not available")
except Exception as e:
    print(f"Error checking providers: {e}")

print("\nAvailable modules in quark package:")
print(dir(quark))

try:
    # Try to import onnx module from quark
    from quark import onnx
    print("\nQuark ONNX module successfully imported")
    print(f"Available functions in quark.onnx: {dir(quark.onnx)}")
except Exception as e:
    print(f"\nError importing quark.onnx: {e}")

try:
    # Try to create a Model
    from quark import Model
    print("\nSuccessfully imported Model class")
    print(f"Model class: {Model}")
except Exception as e:
    print(f"\nError importing Model class: {e}")
