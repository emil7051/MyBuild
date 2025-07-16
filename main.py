"""
Main script to run the TCO analysis and generate outputs.
"""
from output.charts import generate_all_charts, generate_all_csv


def main():
    """
    This function runs the entire TCO analysis pipeline.
    
    It generates:
    1. Paired vehicle comparison charts (cost per km and waterfall).
    2. Class average comparison charts.
    3. A detailed CSV file with TCO data for all vehicles and class averages.
    """
    print("Starting TCO analysis...")
    
    # Generate all visualisations
    generate_all_charts()
    
    # Generate the detailed CSV data
    generate_all_csv()
    
    print("TCO analysis complete. Outputs are in the 'output/charts' directory.")

if __name__ == '__main__':
    main() 