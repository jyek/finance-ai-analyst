"""
Example: Test indented header handling for financial tables.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.sheet import SheetAnalyzer


def create_test_dataframe():
    """Create a test DataFrame with indented headers to demonstrate the fix."""
    
    # Create sample data with indented headers (like in an income statement)
    # All arrays must have the same length
    data = {
        'Category': ['Revenue', '', 'Operating Revenue', 'Product Revenue', 'Service Revenue', '', 'Cost of Revenue', '', 'Gross Profit', '', 'Operating Expenses', '', 'Marketing', 'Sales', 'R&D', 'G&A', '', 'Operating Income', '', 'Net Income'],
        'Subcategory': ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        'Metric': ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        'Q1 2024': [1000000, '', 800000, 600000, 200000, '', 400000, '', 600000, '', 300000, '', 100000, 80000, 70000, 50000, '', 300000, '', 240000],
        'Q2 2024': [1100000, '', 880000, 660000, 220000, '', 440000, '', 660000, '', 330000, '', 110000, 88000, 77000, 55000, '', 330000, '', 264000],
        'Q3 2024': [1200000, '', 960000, 720000, 240000, '', 480000, '', 720000, '', 360000, '', 120000, 96000, 84000, 60000, '', 360000, '', 288000],
        'Q4 2024': [1300000, '', 1040000, 780000, 260000, '', 520000, '', 780000, '', 390000, '', 130000, 104000, 91000, 65000, '', 390000, '', 312000]
    }
    
    # Verify all arrays have the same length
    lengths = [len(v) for v in data.values()]
    if len(set(lengths)) > 1:
        print(f"Warning: Arrays have different lengths: {lengths}")
        # Find the maximum length and pad shorter arrays
        max_len = max(lengths)
        for key in data:
            if len(data[key]) < max_len:
                data[key].extend([''] * (max_len - len(data[key])))
    
    df = pd.DataFrame(data)
    return df


def test_indented_header_fix():
    """Test the indented header fixing functionality."""
    
    print("🧪 Testing Indented Header Fix")
    print("=" * 50)
    
    # Create test DataFrame
    df_original = create_test_dataframe()
    
    print("📊 Original DataFrame (with indented headers):")
    print(df_original.head(10))
    print("\n" + "="*50)
    
    # Create a mock SheetAnalyzer instance to test the method
    class MockSheetAnalyzer:
        def _fix_indented_row_headers(self, df):
            # Import the actual method from SheetAnalyzer
            analyzer = SheetAnalyzer.__new__(SheetAnalyzer)
            return analyzer._fix_indented_row_headers(df)
        
        def _find_header_column(self, df):
            analyzer = SheetAnalyzer.__new__(SheetAnalyzer)
            return analyzer._find_header_column(df)
        
        def _is_financial_metric_name(self, text):
            analyzer = SheetAnalyzer.__new__(SheetAnalyzer)
            return analyzer._is_financial_metric_name(text)
        
        def _merge_indented_headers(self, df, header_col_idx):
            analyzer = SheetAnalyzer.__new__(SheetAnalyzer)
            return analyzer._merge_indented_headers(df, header_col_idx)
        
        def _is_sub_item(self, main_header, parent_header):
            analyzer = SheetAnalyzer.__new__(SheetAnalyzer)
            return analyzer._is_sub_item(main_header, parent_header)
    
    mock_analyzer = MockSheetAnalyzer()
    
    # Test header column detection
    print("🔍 Step 1: Finding header column...")
    header_col_idx = mock_analyzer._find_header_column(df_original)
    print(f"   Header column index: {header_col_idx}")
    print(f"   Header column name: '{df_original.columns[header_col_idx]}'")
    
    # Test financial metric name detection
    print("\n🔍 Step 2: Testing financial metric detection...")
    test_metrics = ['Revenue', 'Operating Revenue', 'Cost of Revenue', 'Marketing', 'Q1 2024', '1000000']
    for metric in test_metrics:
        is_financial = mock_analyzer._is_financial_metric_name(metric)
        print(f"   '{metric}': {'✅ Financial' if is_financial else '❌ Not Financial'}")
    
    # Test sub-item detection
    print("\n🔍 Step 3: Testing sub-item detection...")
    test_pairs = [
        ('Operating Revenue', 'Revenue'),
        ('Product Revenue', 'Operating Revenue'),
        ('Marketing', 'Operating Expenses'),
        ('Revenue', 'Marketing')  # This should be False
    ]
    for main, parent in test_pairs:
        is_sub = mock_analyzer._is_sub_item(main, parent)
        print(f"   '{main}' sub-item of '{parent}': {'✅ Yes' if is_sub else '❌ No'}")
    
    # Test the full fix
    print("\n🔍 Step 4: Applying indented header fix...")
    df_fixed = mock_analyzer._fix_indented_row_headers(df_original)
    
    print("\n📊 Fixed DataFrame (merged headers):")
    print(df_fixed.head(10))
    
    print("\n🔍 Step 5: Comparing before and after...")
    print("Original first column values:")
    for i, val in enumerate(df_original.iloc[:10, 0]):
        print(f"   {i}: '{val}'")
    
    print("\nFixed first column values:")
    for i, val in enumerate(df_fixed.iloc[:10, 0]):
        print(f"   {i}: '{val}'")
    
    # Test with a more complex example
    print("\n" + "="*50)
    print("🧪 Testing with more complex indentation...")
    
    # Create a more complex example with multiple levels of indentation
    complex_data = {
        'Level1': ['Revenue', '', 'Costs', '', 'Profit', ''],
        'Level2': ['', '', 'Direct Costs', 'Indirect Costs', '', ''],
        'Level3': ['', '', 'Materials', 'Labor', 'Overhead', 'Marketing', '', ''],
        'Metric': ['Total', 'Growth', 'Total', 'Materials', 'Labor', 'Overhead', 'Marketing', 'Total', 'Net'],
        '2023': [1000000, 0.10, 600000, 300000, 200000, 50000, 50000, 400000, 400000],
        '2024': [1100000, 0.10, 660000, 330000, 220000, 55000, 55000, 440000, 440000]
    }
    
    # Fix array lengths for complex data
    lengths = [len(v) for v in complex_data.values()]
    if len(set(lengths)) > 1:
        print(f"Warning: Complex data arrays have different lengths: {lengths}")
        max_len = max(lengths)
        for key in complex_data:
            if len(complex_data[key]) < max_len:
                complex_data[key].extend([''] * (max_len - len(complex_data[key])))
    
    df_complex = pd.DataFrame(complex_data)
    print("\n📊 Complex DataFrame (multiple indentation levels):")
    print(df_complex)
    
    df_complex_fixed = mock_analyzer._fix_indented_row_headers(df_complex)
    print("\n📊 Fixed Complex DataFrame:")
    print(df_complex_fixed)
    
    print("\n✅ Indented header fix test completed!")


if __name__ == "__main__":
    test_indented_header_fix() 