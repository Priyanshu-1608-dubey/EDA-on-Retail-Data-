# 📊 Retail Sales EDA Project

**A Complete Exploratory Data Analysis Project for Retail Sales Dataset**

---

## 📘 Project Overview

This project focuses on analyzing retail sales data to understand customer behavior, product performance, revenue patterns, and trends.  
It includes:

- Automatic EDA report generation
- Visualizations
- Data cleaning
- Pattern observation
- HTML-based dashboard reports
- No Streamlit / No Jupyter — runs directly in VS Code

This project is specially designed to run using **VS Code + Python** without any additional frameworks.

---

## 🗂 Features

# 1. Load Sales Dataset Safely

Handles:

- Corrupted rows
- Large CSV files
- Tokenizing issues
- Missing values

# 2. Automated EDA Report

Using **ydata-profiling**, a complete HTML report is generated, containing:

- Overview summary
- Missing values
- Correlation heatmaps
- Histogram distribution
- Interaction plots
- Variable analysis

# 3. Interactive Charts

Using **Plotly**, automatically generated interactive charts including:

- Bar Charts
- Line Charts
- Time Series Graphs
- KPI analysis

# 4. HTML Dashboard Output

Project generates two output files automatically:

## Short Version (For Quick Notes in README)

# Create Virtual Environment

python -m venv venv

# Activate

venv\Scripts\activate

# Upgrade pip

python -m pip install --upgrade pip

# Install Dependencies

pip install -r requirements.txt

# Run Project

python eda.py

# or

streamlit run dashboard.py

## Run The project using this line :-

streamlit run eda.py
