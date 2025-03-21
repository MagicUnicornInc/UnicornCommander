from optimum.amd import AmtModel, AmtConfig

print("Successfully imported optimum.amd.AmtModel and AmtConfig")

# Check for ORT integration
try:
    from optimum.amd.ort import ORTConfig, ORTOptimizer
    print("Successfully imported optimum.amd.ort modules")
    print(f"ORTConfig methods: {dir(ORTConfig)}")
except ImportError as e:
    print(f"Error importing optimum.amd.ort: {e}")

# Check for XDNA Provider
try:
    import onnxruntime as ort
    print(f"Available ORT providers: {ort.get_available_providers()}")
    
    if "XDNAExecutionProvider" in ort.get_available_providers():
        print("XDNA acceleration available\!")
    else:
        print("XDNA provider not found in available providers.")
except Exception as e:
    print(f"Error checking ORT providers: {e}")
