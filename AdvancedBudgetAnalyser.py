import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
import mysql.connector
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class AdvancedBudgetAnalyzer:
    def __init__(self, db_config: Dict[str, str], table_name: str):
        """Initialize with database configuration and table name."""
        self.db_config = db_config
        self.table_name = table_name
        self.df = self.load_data_from_db()
        self.prepare_data()

    def load_data_from_db(self) -> pd.DataFrame:
        """Load data from SQL database."""
        conn = mysql.connector.connect(**self.db_config)
        query = f"SELECT * FROM {self.table_name}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def prepare_data(self):
        """Prepare and clean the dataset."""
        expense_columns = ['FY22ActualExpense', 'FY23ActualExpense', 
                           'FY24Appropriation', 'FY25Budget']
        for col in expense_columns:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

    def analyze_expense_efficiency(self) -> pd.DataFrame:
        """Analyze expense efficiency."""
        efficiency_df = self.df.groupby(['Cabinet', 'Dept']).agg({
            'FY22ActualExpense': 'sum',
            'FY23ActualExpense': 'sum',
            'FY24Appropriation': 'sum',
            'FY25Budget': 'sum'
        }).round(2)
        efficiency_df['FY23_Efficiency'] = (efficiency_df['FY23ActualExpense'] /
                                            efficiency_df['FY24Appropriation'] * 100)
        efficiency_df['Spending_Pattern'] = pd.cut(
            efficiency_df['FY23_Efficiency'],
            bins=[0, 85, 95, 105, float('inf')],
            labels=['Under Spender', 'Efficient', 'Slight Overspend', 'Major Overspend']
        )
        return efficiency_df

    def identify_optimization_clusters(self) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        """Identify optimization clusters using K-means clustering."""
        cluster_data = self.df.groupby('Dept').agg({
            'FY22ActualExpense': 'sum',
            'FY23ActualExpense': 'sum',
            'FY24Appropriation': 'sum',
            'FY25Budget': 'sum'
        })
        cluster_data['Growth_Rate'] = ((cluster_data['FY25Budget'] - 
                                       cluster_data['FY22ActualExpense']) / 
                                      cluster_data['FY22ActualExpense'] * 100).replace([np.inf, -np.inf], np.nan)
        cluster_data['Budget_Size'] = cluster_data['FY25Budget']
        X = cluster_data[['Growth_Rate', 'Budget_Size']].copy()
        X.replace([np.inf, -np.inf], np.nan, inplace=True)
        imputer = SimpleImputer(strategy='mean')
        X_imputed = imputer.fit_transform(X)
        X_imputed = np.clip(X_imputed, -1e6, 1e6)
        kmeans = KMeans(n_clusters=4, random_state=42)
        cluster_data['Cluster'] = kmeans.fit_predict(X_imputed)
        recommendations = {}
        for cluster in range(4):
            cluster_deps = cluster_data[cluster_data['Cluster'] == cluster]
            avg_growth = cluster_deps['Growth_Rate'].mean()
            avg_budget = cluster_deps['Budget_Size'].mean()
            recs = []
            if avg_growth > 20:
                recs.append("High growth rate detected. Consider implementing growth controls.")
            if avg_growth < 0:
                recs.append("Negative growth trend. Review for potential resource constraints.")
            if avg_budget > cluster_data['Budget_Size'].mean():
                recs.append("Large budget allocation. Explore efficiency opportunities.")
            recommendations[f'Cluster_{cluster}'] = recs
        return cluster_data, recommendations

    def simulate_budget_scenarios(self, num_scenarios: int = 3) -> pd.DataFrame:
        """Simulate different budget scenarios based on historical patterns and external factors."""
        scenarios = []
        base_budget = self.df.groupby('ExpenseCategory')['FY25Budget'].sum()
        
        # Scenario 1: Conservative Growth
        conservative = base_budget * np.random.uniform(0.98, 1.02, len(base_budget))
        scenarios.append(('Conservative', conservative))
        
        # Scenario 2: Aggressive Optimization
        optimization_targets = {
            'Personnel Services': 0.95,
            'Contractual Services': 0.90,
            'Supplies & Materials': 0.93,
            'Equipment': 0.92,
            'Current Charges & Obligations': 0.97
        }
        aggressive = base_budget.copy()
        for category, target in optimization_targets.items():
            if category in aggressive.index:
                aggressive[category] *= target
        scenarios.append(('Aggressive', aggressive))
        
        # Scenario 3: Strategic Investment
        strategic = base_budget.copy()
        investment_areas = ['Equipment', 'Contractual Services']
        for area in investment_areas:
            if area in strategic.index:
                strategic[area] *= 1.15
        scenarios.append(('Strategic', strategic))
        
        # Create comparison DataFrame
        scenario_df = pd.DataFrame({name: data for name, data in scenarios})
        scenario_df['Current'] = base_budget
        scenario_df['Max_Savings'] = scenario_df[['Conservative', 'Aggressive', 'Strategic']].min(axis=1)
        
        return scenario_df

    def plot_efficiency_distribution(self):
        """Plot the distribution of efficiency scores and save as an image."""
        efficiency_scores = self.analyze_expense_efficiency()
        plt.figure(figsize=(10, 6))
        sns.histplot(data=efficiency_scores['FY23_Efficiency'], bins=20)
        plt.title('Distribution of Department Efficiency Scores')
        plt.xlabel('Efficiency Score (Lower is Better)')
        plt.ylabel('Frequency')
        plt.tight_layout()
        plt.savefig('efficiency_distribution.png')
        plt.close()

    def plot_budget_scenarios_comparison(self):
        """Plot budget scenarios comparison and save as an image."""
        scenarios = self.simulate_budget_scenarios()
        plt.figure(figsize=(10, 6))
        scenarios.plot(kind='bar', rot=45)
        plt.title('Budget Scenarios Comparison')
        plt.xlabel('Expense Category')
        plt.ylabel('Budget Amount')
        plt.tight_layout()
        plt.savefig('budget_scenarios_comparison.png')
        plt.close()

    def plot_department_clusters(self):
        """Plot department clusters by growth and budget and save as an image."""
        cluster_data, _ = self.identify_optimization_clusters()
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=cluster_data, x='Growth_Rate', y='Budget_Size', hue='Cluster', palette='deep')
        plt.title('Department Clusters by Growth and Budget')
        plt.xlabel('Growth Rate')
        plt.ylabel('Budget Size')
        plt.tight_layout()
        plt.savefig('department_clusters.png')
        plt.close()

    def plot_expense_category_correlations(self):
        """Plot expense category correlations and save as an image."""
        pivot_df = self.df.pivot_table(index='Dept', columns='ExpenseCategory', values='FY25Budget', aggfunc='sum').fillna(0)
        plt.figure(figsize=(10, 6))
        sns.heatmap(pivot_df.corr(), annot=True, cmap='coolwarm', center=0)
        plt.title('Expense Category Correlations')
        plt.tight_layout()
        plt.savefig('expense_category_correlations.png')
        plt.close()

# Example usage
if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'database': 'citybudget'
    }
    analyzer = AdvancedBudgetAnalyzer(db_config, 'BudgetData')
    print("Department Efficiency Analysis:")
    print(analyzer.analyze_expense_efficiency().head())
    cluster_data, recommendations = analyzer.identify_optimization_clusters()
    print("\nCluster Recommendations:")
    for cluster, recs in recommendations.items():
        print(f"\n{cluster}:")
        for rec in recs:
            print(f"- {rec}")
    analyzer.plot_efficiency_distribution()
    analyzer.plot_budget_scenarios_comparison()
    analyzer.plot_department_clusters()
    analyzer.plot_expense_category_correlations()