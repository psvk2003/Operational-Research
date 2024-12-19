import pandas as pd
from ortools.linear_solver import pywraplp
import mysql.connector
import matplotlib.pyplot as plt

# MySQL Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Mohit1234',
    'database': 'CityBudget'
}

# Load data from MySQL database
def fetch_data_from_mysql():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        query = "SELECT * FROM BudgetData"
        operating_budget_df = pd.read_sql(query, connection)
        connection.close()
        
        # Convert numeric columns
        operating_budget_df['FY25Budget'] = pd.to_numeric(operating_budget_df['FY25Budget'], errors='coerce').fillna(0)
        operating_budget_df['FY24Appropriation'] = pd.to_numeric(operating_budget_df['FY24Appropriation'], errors='coerce').fillna(0)
        operating_budget_df['FY23ActualExpense'] = pd.to_numeric(operating_budget_df['FY23ActualExpense'], errors='coerce').fillna(0)
        return operating_budget_df
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Extract data from the database
operating_budget_df = fetch_data_from_mysql()
if operating_budget_df is None:
    print("Data could not be loaded. Please check your database connection.")
    exit()

programs = operating_budget_df['Program'].unique()
expense_categories = operating_budget_df['ExpenseCategory'].unique()

# Function to initialize solver and decision variables
def initialize_solver():
    solver = pywraplp.Solver.CreateSolver('SCIP')
    budget_vars = {}
    for _, row in operating_budget_df.iterrows():
        program = row['Program']
        expense_category = row['ExpenseCategory']
        fy25_budget = float(row['FY25Budget'])
        var = solver.NumVar(0, fy25_budget, f"{program}_{expense_category}")
        budget_vars[(program, expense_category)] = var
    return solver, budget_vars

# Function to solve and save results
def solve_and_save(solver, budget_vars, scenario_name):
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        results = [(program, category, budget_vars[(program, category)].solution_value())
                   for (program, category) in budget_vars]
        results_df = pd.DataFrame(results, columns=['Program', 'ExpenseCategory', 'FY25Allocation'])
        results_df.to_csv(f"optimized_budget_allocation_{scenario_name}.csv", index=False)
        print(f"Optimization successful. Results saved to 'optimized_budget_allocation_{scenario_name}.csv'.")
        plot_results(results_df, scenario_name)
    else:
        print(f"No optimal solution found for {scenario_name}. Check constraints.")

# Function to plot results
def plot_results(results_df, scenario_name):
    non_zero_allocations = results_df[results_df['FY25Allocation'] > 0]

    # Group by Program
    program_allocations = non_zero_allocations.groupby('Program')['FY25Allocation'].sum()
    program_allocations.plot(kind='bar', figsize=(10, 6), title=f"{scenario_name}: FY25 Allocations by Program", color='cornflowerblue')
    plt.ylabel("Allocation Amount")
    plt.tight_layout()
    plt.savefig(f"{scenario_name}_program_allocations.png")
    plt.show()

    # Group by Expense Category
    category_allocations = non_zero_allocations.groupby('ExpenseCategory')['FY25Allocation'].sum()
    category_allocations.plot(kind='pie', figsize=(8, 8), title=f"{scenario_name}: FY25 Allocations by Expense Category", autopct='%1.1f%%')
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(f"{scenario_name}_category_allocations.png")
    plt.show()

# # Define each scenario
# def scenario_1():
#     solver, budget_vars = initialize_solver()
#     objective = solver.Objective()
#     for var in budget_vars.values():
#         objective.SetCoefficient(var, 1)
#     objective.SetMaximization()

#     # Constraints
#     total_fy25_budget = operating_budget_df['FY25Budget'].sum()
#     solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars) <= total_fy25_budget)

#     solve_and_save(solver, budget_vars, "Scenario_1")

# def scenario_2():
#     solver, budget_vars = initialize_solver()
#     objective = solver.Objective()
#     for var in budget_vars.values():
#         objective.SetCoefficient(var, 1)
#     objective.SetMaximization()

#     # Constraints
#     solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars) <= 
#                operating_budget_df['FY25Budget'].sum())

#     # Ensure no department exceeds 110% of its FY24 Appropriation
#     dept_limits = operating_budget_df.groupby('Dept')['FY24Appropriation'].sum().to_dict()
#     for dept, appropriation in dept_limits.items():
#         solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars 
#                        if operating_budget_df[(operating_budget_df['Program'] == program) & 
#                                               (operating_budget_df['ExpenseCategory'] == category)]['Dept'].values[0] == dept) <= 1.1 * appropriation)

#     solve_and_save(solver, budget_vars, "Scenario_2")

# Define each scenario

def scenario_1():
    solver, budget_vars = initialize_solver()
    objective = solver.Objective()
    for var in budget_vars.values():
        objective.SetCoefficient(var, 1)
    objective.SetMaximization()

    # Constraints
    total_fy25_budget = operating_budget_df['FY25Budget'].sum()
    solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars) <= total_fy25_budget)

    solve_and_save(solver, budget_vars, "Scenario_1")


def scenario_2():
    solver, budget_vars = initialize_solver()
    objective = solver.Objective()
    for var in budget_vars.values():
        objective.SetCoefficient(var, 1)
    objective.SetMaximization()

    # Constraints
    solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars) <= 
               operating_budget_df['FY25Budget'].sum())

    # Ensure no department exceeds 110% of its FY24 Appropriation
    dept_limits = operating_budget_df.groupby('Dept')['FY24Appropriation'].sum().to_dict()
    for dept, appropriation in dept_limits.items():
        solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars 
                       if operating_budget_df[(operating_budget_df['Program'] == program) & 
                                              (operating_budget_df['ExpenseCategory'] == category)]['Dept'].values[0] == dept) <= 1.1 * appropriation)

    solve_and_save(solver, budget_vars, "Scenario_2")


def scenario_3():
    solver, budget_vars = initialize_solver()
    objective = solver.Objective()
    for var in budget_vars.values():
        objective.SetCoefficient(var, 1)
    objective.SetMaximization()

    # Constraints
    total_fy25_budget = operating_budget_df['FY25Budget'].sum()
    solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars) <= total_fy25_budget)

    # Ensure that no expense category exceeds 10% of the total FY25 budget
    category_limits = operating_budget_df.groupby('ExpenseCategory')['FY25Budget'].sum().to_dict()
    for category, category_budget in category_limits.items():
        solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars if category == category) <= 0.1 * total_fy25_budget)

    solve_and_save(solver, budget_vars, "Scenario_3")


def scenario_4():
    solver, budget_vars = initialize_solver()
    objective = solver.Objective()
    for var in budget_vars.values():
        objective.SetCoefficient(var, 1)
    objective.SetMaximization()

    # Constraints
    total_fy25_budget = operating_budget_df['FY25Budget'].sum()
    solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars) <= total_fy25_budget)

    # Max allocation for each department based on their FY24 appropriation
    dept_limits = operating_budget_df.groupby('Dept')['FY24Appropriation'].sum().to_dict()
    for dept, appropriation in dept_limits.items():
        solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars 
                       if operating_budget_df[(operating_budget_df['Program'] == program) & 
                                              (operating_budget_df['ExpenseCategory'] == category)]['Dept'].values[0] == dept) <= appropriation)

    solve_and_save(solver, budget_vars, "Scenario_4")


def scenario_5():
    solver, budget_vars = initialize_solver()
    objective = solver.Objective()
    for var in budget_vars.values():
        objective.SetCoefficient(var, 1)
    objective.SetMaximization()

    # Constraints
    total_fy25_budget = operating_budget_df['FY25Budget'].sum()
    solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars) <= total_fy25_budget)

    # Max allocation for each department based on their FY24 appropriation, with additional 5% flexibility
    dept_limits = operating_budget_df.groupby('Dept')['FY24Appropriation'].sum().to_dict()
    for dept, appropriation in dept_limits.items():
        solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars 
                       if operating_budget_df[(operating_budget_df['Program'] == program) & 
                                              (operating_budget_df['ExpenseCategory'] == category)]['Dept'].values[0] == dept) <= 1.05 * appropriation)

    solve_and_save(solver, budget_vars, "Scenario_5")


def scenario_6():
    solver, budget_vars = initialize_solver()
    objective = solver.Objective()
    for var in budget_vars.values():
        objective.SetCoefficient(var, 1)
    objective.SetMaximization()

    # Constraints
    total_fy25_budget = operating_budget_df['FY25Budget'].sum()
    solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars) <= total_fy25_budget)

    # Limit total allocation per expense category to 30% of the overall FY25 budget
    category_limits = operating_budget_df.groupby('ExpenseCategory')['FY25Budget'].sum().to_dict()
    for category, category_budget in category_limits.items():
        solver.Add(sum(budget_vars[(program, category)] for (program, category) in budget_vars if category == category) <= 0.3 * total_fy25_budget)

    solve_and_save(solver, budget_vars, "Scenario_6")

# scenario_1()
# scenario_2()
# scenario_3()
# scenario_4()
# scenario_5()
# scenario_6()
