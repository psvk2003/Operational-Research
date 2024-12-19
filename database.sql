create database CityBudget;
use CityBudget;

CREATE TABLE BudgetData (
    _id INT PRIMARY KEY,
    Cabinet VARCHAR(255),
    Dept VARCHAR(255),
    Program VARCHAR(255),
    ExpenseCategory VARCHAR(255),
    FY22ActualExpense DECIMAL(15, 2),
    FY23ActualExpense DECIMAL(15, 2),
    FY24Appropriation DECIMAL(15, 2),
    FY25Budget DECIMAL(15, 2)
);


LOAD DATA INFILE 'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\Uploads\\operating_budget.csv'
INTO TABLE projects
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;