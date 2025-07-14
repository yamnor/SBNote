#!/usr/bin/env python3
"""
Test script for xyz file generation from cclib data
"""

import sys
import os
import pickle
import tempfile

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

try:
    import cclib
    from notes.file_system.file_system import _create_xyz_file
    print("✅ cclib and functions imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_xyz_file_creation():
    """Test xyz file creation with sample data"""
    print("\n🧪 Testing xyz file creation...")
    
    # Create a mock cclib data object with writexyz method
    class MockData:
        def __init__(self):
            # Sample water molecule data
            self.atomnos = [8, 1, 1]  # O, H, H
            self.atomcoords = [
                # Single coordinate set (final optimized structure)
                [
                    [0.0, 0.0, 0.0],      # O
                    [0.957, 0.0, 0.0],    # H1
                    [-0.24, 0.927, 0.0]   # H2
                ]
            ]
        
        def writexyz(self):
            """Mock writexyz method that returns xyz format string"""
            num_atoms = len(self.atomnos)
            xyz_content = f"{num_atoms}\n\n"  # Number of atoms + empty comment line
            
            # Add each atom with coordinates
            for i in range(num_atoms):
                atom_symbol = self._get_atom_symbol(self.atomnos[i])
                x, y, z = self.atomcoords[0][i]  # Use first (and only) coordinate set
                xyz_content += f"{atom_symbol} {x:.6f} {y:.6f} {z:.6f}\n"
            
            return xyz_content
        
        def _get_atom_symbol(self, atomic_number):
            """Helper method to convert atomic number to symbol"""
            atom_symbols = {1: 'H', 6: 'C', 7: 'N', 8: 'O', 15: 'P', 16: 'S'}
            return atom_symbols.get(atomic_number, f'X{atomic_number}')
    
    mock_data = MockData()
    
    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        xyz_file_path = f.name
    
    try:
        # Test xyz file creation
        success = _create_xyz_file(mock_data, xyz_file_path)
        
        if success:
            print("  ✅ xyz file created successfully")
            
            # Read and display the content
            with open(xyz_file_path, 'r') as f:
                content = f.read()
            
            print("  📄 Generated xyz file content:")
            print("  " + "-" * 40)
            for line in content.split('\n'):
                if line.strip():
                    print(f"  {line}")
            print("  " + "-" * 40)
            
        else:
            print("  ❌ Failed to create xyz file")
            
    except Exception as e:
        print(f"  ❌ Error during xyz file creation: {e}")
    
    finally:
        # Clean up
        if os.path.exists(xyz_file_path):
            os.unlink(xyz_file_path)

def test_missing_data_handling():
    """Test handling of missing writexyz method"""
    print("\n🧪 Testing missing data handling...")
    
    # Test with missing writexyz method
    class MockDataNoWritexyz:
        def __init__(self):
            self.atomnos = [8, 1, 1]
            self.atomcoords = [[[0.0, 0.0, 0.0], [0.957, 0.0, 0.0], [-0.24, 0.927, 0.0]]]
            # No writexyz method
    
    mock_data = MockDataNoWritexyz()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        xyz_file_path = f.name
    
    try:
        success = _create_xyz_file(mock_data, xyz_file_path)
        print(f"  {'✅' if not success else '❌'} Correctly handled missing writexyz method")
    finally:
        if os.path.exists(xyz_file_path):
            os.unlink(xyz_file_path)

if __name__ == "__main__":
    print("🚀 Starting xyz file generation tests...")
    
    test_xyz_file_creation()
    test_missing_data_handling()
    
    print("\n✨ All tests completed!") 