import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for rendering

from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
import matplotlib.pyplot as plt
from opti import scenario_1, scenario_2, scenario_3, scenario_4, scenario_5, scenario_6

app = Flask(__name__)

# Format numerical values in DataFrame to avoid scientific notation
pd.options.display.float_format = '{:,.2f}'.format

# Directory for saving plots
PLOT_DIR = "static/plots"
if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

# Function to plot results
def plot_results(results_df, scenario_name):
    non_zero_allocations = results_df[results_df['FY25Allocation'] > 0]

    # Group by Program
    program_allocations = non_zero_allocations.groupby('Program')['FY25Allocation'].sum()
    plt.figure(figsize=(10, 6))
    program_allocations.plot(kind='bar', color='cornflowerblue', title=f"{scenario_name}: FY25 Allocations by Program")
    plt.ylabel("Allocation Amount")
    plt.tight_layout()
    program_plot_path = os.path.join(PLOT_DIR, f"{scenario_name}_program_allocations.png")
    plt.savefig(program_plot_path)
    plt.close()

    # Group by Expense Category
    category_allocations = non_zero_allocations.groupby('ExpenseCategory')['FY25Allocation'].sum()
    plt.figure(figsize=(8, 8))
    category_allocations.plot(kind='pie', autopct='%1.1f%%', title=f"{scenario_name}: FY25 Allocations by Expense Category")
    plt.ylabel("")
    plt.tight_layout()
    category_plot_path = os.path.join(PLOT_DIR, f"{scenario_name}_category_allocations.png")
    plt.savefig(category_plot_path)
    plt.close()

    return program_plot_path, category_plot_path

# Route for the homepage (home.html)
@app.route("/")
def index():
    return render_template("home.html")

# Route for the budget allocations page (budget_allocations.html)
@app.route("/budget_allocations")
def budget_allocations():
    return render_template("budget_allocations.html")

# Route for the data analysis page (data_analysis.html)
@app.route("/data_analysis")
def data_analysis():
    return render_template("data_analysis.html")

# Route for the about us page (about_us.html)
@app.route("/about_us")
def about_us():
    return render_template("about_us.html")

@app.route("/budget_analysis_summary")
def budget_analysis_summary():
    return render_template("budget_analysis_summary.html")

@app.route("/department_efficiency_analysis")
def department_efficiency_analysis():
    return render_template("department_efficiency_analysis.html")

@app.route("/budget_scenario_analysis")
def budget_scenario_analysis():
    return render_template("budget_scenario_analysis.html")

@app.route("/Budgetanysis")
def Budgetanysis():
    return render_template("Budgetanysis.html")


# Route to run scenarios
@app.route("/run_scenario", methods=["POST"])
def run_scenario():
    scenario_name = request.form.get("scenario_name")
    try:
        # Remove existing plots
        for file in os.listdir(PLOT_DIR):
            file_path = os.path.join(PLOT_DIR, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)

        # Call the appropriate scenario function
        if scenario_name == "Scenario_1":
            scenario_1()
        elif scenario_name == "Scenario_2":
            scenario_2()
        elif scenario_name == "Scenario_3":
            scenario_3()
        elif scenario_name == "Scenario_4":
            scenario_4()
        elif scenario_name == "Scenario_5":
            scenario_5()
        elif scenario_name == "Scenario_6":
            scenario_6()
        else:
            return jsonify({"error": "Invalid scenario selected"}), 400

        # Load the results DataFrame
        result_file = f"optimized_budget_allocation_{scenario_name}.csv"
        results_df = pd.read_csv(result_file)

        # Plot results
        program_plot_path, category_plot_path = plot_results(results_df, scenario_name)

        # Generate HTML table
        result_html = results_df.to_html(index=False, classes="table table-striped")

        return jsonify({
            "message": f"{scenario_name} executed successfully.",
            "result_html": result_html,
            "program_plot_path": program_plot_path,
            "category_plot_path": category_plot_path
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
