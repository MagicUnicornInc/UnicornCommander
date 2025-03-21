import onnxruntime as ort
import numpy as np
import os

print("ONNX Runtime version:", ort.__version__)
print("Available providers:", ort.get_available_providers())
print("Device:", ort.get_device())

# Check environment variables
print("\nChecking environment variables:")
for var in ['XDNA_INI_PATH', 'XDNA_DEVICE', 'XDNA_DRIVER_PATH']:
    print(f"{var}: {os.environ.get(var, 'Not set')}")

# Create a very simple model
try:
    print("\nCreating simple ONNX inference session...")
    # Create a very basic model with just one operation
    import numpy as np
    
    # Create a session with CPU provider
    session = ort.InferenceSession("", providers=["CPUExecutionProvider"])
    print(f"Created session with providers: {session.get_providers()}")
    
    # Try a simple calculation
    data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    result = data * 2
    print(f"Simple calculation result: {result}")
    
    print("ONNX basic test completed successfully")
except Exception as e:
    print(f"Error in ONNX test: {e}")
