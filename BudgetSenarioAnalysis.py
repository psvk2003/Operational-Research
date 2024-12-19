import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ortools.linear_solver import pywraplp
import mysql.connector


class BudgetScenarioAnalyzer:
    def __init__(self, db_config: dict):
        """Initialize with SQL database connection configuration and prepare data."""
        self.connection = mysql.connector.connect(**db_config)
        self.df = self.fetch_data()
        self.prepare_data()

    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from the BudgetData table in the SQL database."""
        query = """
        SELECT 
            Cabinet, 
            Dept, 
            Program, 
            ExpenseCategory, 
            FY22ActualExpense, 
            FY23ActualExpense, 
            FY24Appropriation, 
            FY25Budget 
        FROM BudgetData
        """
        return pd.read_sql(query, self.connection)

    def prepare_data(self):
        """Prepare and clean the dataset."""
        # Convert budget columns to numeric
        budget_columns = ['FY25Budget', 'FY24Appropriation', 'FY23ActualExpense']
        for col in budget_columns:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Extract unique programs and categories
        self.programs = self.df['Program'].unique()
        self.expense_categories = self.df['ExpenseCategory'].unique()

    def initialize_solver(self):
        """Initialize solver and decision variables."""
        solver = pywraplp.Solver.CreateSolver('SCIP')
        budget_vars = {}
        for _, row in self.df.iterrows():
            program = row['Program']
            expense_category = row['ExpenseCategory']
            fy25_budget = float(row['FY25Budget'])
            var = solver.NumVar(0, fy25_budget, f"{program}_{expense_category}")
            budget_vars[(program, expense_category)] = var
        return solver, budget_vars

    def solve_scenario(self, scenario_func) -> pd.DataFrame:
        """Solve a specific scenario and return results as DataFrame."""
        solver, budget_vars = self.initialize_solver()
        scenario_func(solver, budget_vars)
        
        if solver.Solve() == pywraplp.Solver.OPTIMAL:
            results = []
            for (program, category) in budget_vars:
                results.append({
                    'Program': program,
                    'Expense Category': category,
                    'Allocated Budget': budget_vars[(program, category)].solution_value()
                })
            return pd.DataFrame(results)
        return pd.DataFrame()

    def scenario_1(self, solver, budget_vars):
        """Total FY25 Budget + Departmental Limits"""
        objective = solver.Objective()
        for var in budget_vars.values():
            objective.SetCoefficient(var, 1)
        objective.SetMaximization()

        # Total Budget Constraint
        total_fy25_budget = self.df['FY25Budget'].sum()
        solver.Add(sum(budget_vars.values()) <= total_fy25_budget)

        # Departmental Limits
        department_limits = self.df.groupby('Dept')['FY23ActualExpense'].sum()
        for dept, limit in department_limits.items():
            dept_vars = [budget_vars[(program, category)] 
                        for program, category in budget_vars.keys()
                        if self.df[(self.df['Program'] == program) & 
                                 (self.df['ExpenseCategory'] == category)]['Dept'].values[0] == dept]
            if dept_vars:
                solver.Add(sum(dept_vars) <= limit)

    def scenario_2(self, solver, budget_vars):
        """Total FY25 Budget + Departmental Limits + Category Spending Limit"""
        self.scenario_1(solver, budget_vars)
        
        # Category Spending Limits
        category_limits = self.df.groupby('ExpenseCategory')['FY23ActualExpense'].mean()
        for category, limit in category_limits.items():
            category_vars = [budget_vars[(program, category)] 
                           for program in self.programs 
                           if (program, category) in budget_vars]
            if category_vars:
                solver.Add(sum(category_vars) <= limit)

    def scenario_3(self, solver, budget_vars):
        """Total FY25 Budget + Departmental Limits + Key Program Minimum Funding"""
        self.scenario_1(solver, budget_vars)
        
        # Minimum Funding for Key Programs
        key_programs = ["Mayor's Administration", "Public Safety"]
        min_funding_perc = 0.5
        for program in key_programs:
            program_data = self.df[self.df['Program'] == program]
            for _, row in program_data .iterrows():
                category = row['ExpenseCategory']
                if (program, category) in budget_vars:
                    solver.Add(budget_vars[(program, category)] >= 
                             min_funding_perc * float(row['FY24Appropriation']))

    def scenario_4(self, solver, budget_vars):
        """Combining all constraints"""
        self.scenario_2(solver, budget_vars)
        
        # Add Key Program Minimum Funding
        key_programs = ["Mayor's Administration", "Public Safety"]
        min_funding_perc = 0.5
        for program in key_programs:
            program_data = self.df[self.df['Program'] == program]
            for _, row in program_data.iterrows():
                category = row['ExpenseCategory']
                if (program, category) in budget_vars:
                    solver.Add(budget_vars[(program, category)] >= 
                             min_funding_perc * float(row['FY24Appropriation']))

    def analyze_all_scenarios(self):
        """Run all scenarios and create visualizations."""
        scenarios = {
            'Basic': self.scenario_1,
            'Category Limits': self.scenario_2,
            'Key Programs': self.scenario_3,
            'Combined': self.scenario_4
        }
        
        results = {}
        for name, scenario_func in scenarios.items():
            results[name] = self.solve_scenario(scenario_func)
        
        self.plot_total_budget_allocation(results)
        self.plot_budget_distribution_by_category(results)
        self.plot_key_programs_budget_allocation(results)
        self.plot_department_distribution_heatmap(results)
        return results

    def plot_total_budget_allocation(self, results):
        """Plot total budget allocation by scenario."""
        plt.figure(figsize=(10, 6))
        scenario_totals = {name: df['Allocated Budget'].sum() 
                          for name, df in results.items()}
        plt.bar(scenario_totals.keys(), scenario_totals.values())
        plt.title('Total Budget Allocation by Scenario')
        plt.xticks(rotation=45)
        plt.ylabel('Total Budget')
        plt.tight_layout()
        plt.savefig('total_budget_allocation.png')
        plt.close()

    def plot_budget_distribution_by_category(self, results):
        """Plot budget distribution by category for each scenario."""
        plt.figure(figsize=(10, 6))
        category_data = []
        for scenario, df in results.items():
            category_sums = df.groupby('Expense Category')['Allocated Budget'].sum()
            for category, amount in category_sums.items():
                category_data.append({
                    'Scenario': scenario,
                    'Category': category,
                    'Amount': amount
                })
        category_df = pd.DataFrame(category_data)
        sns.barplot(data=category_df, x='Scenario', y='Amount', hue='Category')
        plt.title('Budget Distribution by Category')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('budget_distribution_by_category.png')
        plt.close()

    def plot_key_programs_budget_allocation(self, results):
        """Plot key programs budget allocation for each scenario."""
        plt.figure(figsize=(10, 6))
        key_programs = ["Mayor's Administration", "Public Safety"]
        key_program_data = []
        for scenario, df in results.items():
            for program in key_programs:
                amount = df[df['Program'] == program]['Allocated Budget'].sum()
                key_program_data.append({
                    'Scenario': scenario,
                    'Program': program,
                    'Amount': amount
                })
        key_program_df = pd.DataFrame(key_program_data)
        sns.barplot(data=key_program_df, x='Scenario', y='Amount', hue='Program')
        plt.title('Key Programs Budget Allocation')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('key_programs_budget_allocation.png')
        plt.close()

    def plot_department_distribution_heatmap(self, results):
        """Plot department distribution heatmap for scenario correlations."""
        plt.figure(figsize=(10, 6))
        dept_scenario_matrix = pd.DataFrame()
        for scenario, df in results.items():
            dept_sums = df.groupby('Program')['Allocated Budget'].sum()
            dept_scenario_matrix[scenario] = dept_sums
        sns.heatmap(dept_scenario_matrix.corr(), annot=True, cmap='coolwarm')
        plt.title('Scenario Correlation Matrix')
        plt.tight_layout()
        plt.savefig('department_distribution_heatmap.png')
        plt.close()


# Example usage
if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'database': 'citybudget'
    }
    analyzer = BudgetScenarioAnalyzer(db_config)
    results = analyzer.analyze_all_scenarios()