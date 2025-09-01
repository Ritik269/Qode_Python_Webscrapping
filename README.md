# Market Intel

Market Intel is a Python-based framework for collecting, processing, analyzing, and visualizing financial market data.  
It supports NAV data processing, benchmark comparisons, and custom visualization with Recharts in React.

---

## 📂 Project Structure

market-intel/
├── requirements.txt # Python dependencies
├── config/
│ └── settings.yaml # Project configuration (API keys, paths, etc.)
├── data/ # Input/output datasets
├── logs/ # Log files
└── src/
├── utils.py # Helper utilities
├── schema.py # Data validation & schema definitions
├── collect.py # Data collection from APIs
├── process.py # Data cleaning and transformation
├── analyze.py # Analytics and performance metrics
└── viz.py # Visualization scripts

# To Run the code
1) Create virtual environment :
   
-python -m venv venv

-source venv/bin/activate   # Linux/Mac

-venv\Scripts\activate      # Windows

2)Install dependencies:
-pip install -r requirements.txt

3) To collect the Data:
-python -m src.collect

4) To process the Data:
-python -m src.process

5) To analyze the Data:
-python -m src.analyze

6) To visualize the Data:
-python -m src.viz

# Requirements
Python 3.9+

Dependencies listed in requirements.txt




