import pkgutil
import quark

# Get package modules
print("Quark package structure:")
for finder, name, is_pkg in pkgutil.walk_packages(quark.__path__, quark.__name__ + '.'):
    print(f"{name} - {'package' if is_pkg else 'module'}")

print("\nChecking for the Model class:")
# Try to find the Model class
for module_name in sorted(dir(quark)):
    try:
        submodule = getattr(quark, module_name)
        if hasattr(submodule, 'Model'):
            print(f"  Found Model in quark.{module_name}")
    except:
        pass

print("\nChecking for runtime module:")
try:
    import quark.runtime
    print("  quark.runtime available")
    print(f"  Contents: {dir(quark.runtime)}")
except ImportError as e:
    print(f"  Error importing quark.runtime: {e}")

# Check for inference module
print("\nChecking for inference module:")
try:
    import quark.inference
    print("  quark.inference available")
    print(f"  Contents: {dir(quark.inference)}")
except ImportError as e:
    print(f"  Error importing quark.inference: {e}")
