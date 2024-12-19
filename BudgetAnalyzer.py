import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from flask import Flask, render_template, redirect, url_for

warnings.filterwarnings('ignore')


class BudgetAnalyzer:
    def __init__(self, db_config: dict):
        """Initialize the BudgetAnalyzer with database configuration."""
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
        """Prepare and clean the dataset for analysis."""
        expense_columns = [
            'FY22ActualExpense', 'FY23ActualExpense',
            'FY24Appropriation', 'FY25Budget'
        ]
        for col in expense_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

    def plot_fy25_budget_by_expense_category(self):
        """Plot FY25 Budget by Expense Category."""
        plt.figure(figsize=(10, 6))
        expense_trends = self.df.groupby('ExpenseCategory')['FY25Budget'].sum().sort_values(ascending=True)
        expense_trends.plot(kind='barh', color='skyblue')
        plt.title('FY25 Budget by Expense Category', fontsize=14)
        plt.xlabel('Budget Amount ($)', fontsize=12)
        plt.tight_layout()
        plt.show()

    def plot_budget_trends_by_cabinet(self):
        """Plot Budget Trends by Cabinet."""
        plt.figure(figsize=(12, 6))
        cabinet_years = self.df.groupby('Cabinet')[['FY22ActualExpense', 'FY23ActualExpense',
                                                    'FY24Appropriation', 'FY25Budget']].sum()
        cabinet_years.plot(kind='bar')
        plt.title('Budget Trends by Cabinet', fontsize=14)
        plt.xticks(range(len(cabinet_years.index)), cabinet_years.index, rotation=45, ha='right')
        plt.xlabel('Cabinet', fontsize=12)
        plt.ylabel('Amount ($)', fontsize=12)
        plt.tight_layout()
        plt.show()

    def plot_fy25_budget_distribution_by_expense_category(self):
        """Plot FY25 Budget Distribution by Expense Category."""
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=self.df, x='ExpenseCategory', y='FY25Budget')
        plt.title('FY25 Budget Distribution by Expense Category', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.xlabel('Expense Category', fontsize=12)
        plt.ylabel('Budget Amount ($)', fontsize=12)
        plt.tight_layout()
        plt.show()

    def plot_budget_growth_distribution(self):
        """Plot Distribution of Budget Growth Rates (FY22 to FY25)."""
        plt.figure(figsize=(12, 6))
        growth_rates = ((self.df['FY25Budget'] - self.df['FY22ActualExpense']) / self.df['FY22ActualExpense'] * 100)
        sns.histplot(data=growth_rates.dropna(), bins=30, kde=True, color='green')
        plt.title('Distribution of Budget Growth Rates (FY22 to FY25)', fontsize=14)
        plt.xlabel('Growth Rate (%)', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.tight_layout()
        plt.show()


# Example usage
if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'database': 'citybudget'
    }
    analyzer = BudgetAnalyzer(db_config)
    # Call individual functions as needed
    analyzer.plot_fy25_budget_by_expense_category()
    analyzer.plot_budget_trends_by_cabinet()
    analyzer.plot_fy25_budget_distribution_by_expense_category()
    analyzer.plot_budget_growth_distribution()
