import pandas as pd

# Load the data
file_path = 'data/operating_budget.csv'
data = pd.read_csv(file_path)

# List of budget columns
budget_columns = ["FY22 Actual Expense", "FY23 Actual Expense", "FY24 Appropriation", "FY25 Budget"]

# Replace '#Missing' with NaN for numeric computation
data[budget_columns] = data[budget_columns].replace('#Missing', pd.NA)

# Convert to numeric, ensuring that invalid parsing results in NaN
data[budget_columns] = data[budget_columns].apply(pd.to_numeric, errors='coerce')

# Function to replace missing values with the mean of other budget columns for the same row
def replace_with_row_mean(row):
    row_mean = row[budget_columns].mean(skipna=True)  # Calculate mean ignoring NaN
    return row[budget_columns].fillna(row_mean)  # Fill NaN with the row mean

# Apply the function row-wise
data[budget_columns] = data.apply(replace_with_row_mean, axis=1)

# Save the updated data back to a CSV file
updated_file_path = 'data/mean_filled_operating_budget.csv'
data.to_csv(updated_file_path, index=False)

print(f"Data with missing values replaced saved to {updated_file_path}")
