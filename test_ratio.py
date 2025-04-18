#!/usr/bin/env python3
"""Test the file size comparison logic for content matching."""

def test_size_comparison():
    """Test different file size scenarios with 20% tolerance."""
    print("Testing 20% tolerance with different file sizes:")
    
    # Define exact boundary values
    print("\nExact 20% boundary values:")
    print("1.2 ratio = 20.0% difference")
    print("A file ratio > 1.2 is outside tolerance")
    print("A file ratio ≤ 1.2 is within tolerance")
    
    # Using base value of 100,000 for easier calculation
    base = 100000
    
    # Define test scenarios with more precision
    print("\nTest cases:")
    test_cases = [
        (base, int(base * 0.9)),        # 10% smaller - should be within tolerance
        (base, int(base / 1.2)),        # Exactly 20% difference (ratio = 1.2) - should be within tolerance
        (base, int(base / 1.2) - 1),    # Just over 20% difference - should be outside tolerance
        (base, int(base * 1.1)),        # 10% larger - should be within tolerance
        (base, int(base * 1.2)),        # Exactly 20% larger - should be within tolerance
        (base, int(base * 1.2) + 1),    # Just over 20% larger - should be outside tolerance
    ]
    
    print(f"\nUsing base value: {base}")
    print("-" * 50)
    
    for i, (local, remote) in enumerate(test_cases):
        # Calculate the size ratio
        ratio = max(local, remote) / min(local, remote)
        
        # Convert to percentage difference
        pct_diff = (ratio - 1.0) * 100
        
        # Check if within 20% tolerance
        within_tolerance = ratio <= 1.20  # 20% max deviation
        
        # Determine if local or remote is larger
        comparison = "smaller" if remote < local else "larger"
        
        print(f"Test {i+1}: Remote file is {comparison} than local file")
        print(f"Local: {local} bytes, Remote: {remote} bytes")
        print(f"Ratio = {ratio:.6f}, Difference = {pct_diff:.2f}%")
        print(f"Within tolerance (≤20%): {within_tolerance}")
        print("-" * 50)
        
if __name__ == "__main__":
    test_size_comparison() 