# 🚗 Kenya Motor Insurance Premium Prediction System (KMIPPS)

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)
![Scikit--Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-orange?logo=scikitlearn)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Project Overview

The **Kenya Motor Insurance Premium Prediction System (KMIPPS)** is a web-based machine learning application developed to automate the prediction of motor insurance premiums using driver and vehicle information.

The system applies machine learning techniques to estimate insurance premiums, classify customers into risk categories, and assist underwriters in making faster and more consistent pricing decisions.

This project was developed as part of the **Bachelor of Science in Data Science** programme at **KCA University**.

---

## Objectives

The project aims to:

- Predict motor insurance premiums using machine learning.
- Classify customers into Low, Medium, and High Risk categories.
- Reduce manual premium calculations.
- Improve underwriting consistency.
- Store customer and prediction records in PostgreSQL.
- Provide reports and dashboard analytics for decision-making.

---

## Features

### Authentication

- User Login
- Password Hashing
- Role-Based Access Control
- Administrator and Underwriter Roles

### Premium Prediction

- Machine Learning Premium Prediction
- Risk Classification
- Driver Information Capture
- Vehicle Information Capture

### Dashboard

- Total Predictions
- Total Drivers
- Total Vehicles
- Average Premium
- Highest Premium
- Lowest Premium
- Low Risk Drivers
- High Risk Drivers

### Charts

- Monthly Predictions
- Risk Category Distribution
- Vehicle Type Distribution
- Machine Learning Model Comparison

### Reports

- Individual Prediction PDF
- Prediction History
- Export History to PDF
- Export History to Excel

### Administration

- User Management
- Audit Logs
- System Settings
- Configurable Risk Thresholds

---

## Machine Learning Models Evaluated

| Model | MAE | RMSE | R² Score |
|------|------:|------:|------:|
| Linear Regression | 592.373 | 742.590 | **0.999695** |
| Random Forest | 1406.829 | 1797.730 | 0.998214 |
| Gradient Boosting | 884.847 | 1136.199 | 0.999287 |

**Selected Model:** Linear Regression

The Linear Regression model achieved the highest coefficient of determination (R²) and was deployed in the production system.

---

## Technologies Used

### Programming Languages

- Python
- SQL
- HTML
- CSS
- JavaScript

### Frameworks & Libraries

- Flask
- Scikit-learn
- Pandas
- NumPy
- Joblib
- ReportLab
- OpenPyXL
- Bootstrap 5
- Chart.js

### Database

- PostgreSQL

### Development Tools

- Visual Studio Code
- pgAdmin 4
- Git
- GitHub

---

## Project Structure

```text
KMIPPS/
│
├── app.py
├── db.py
├── premium_model.pkl
├── requirements.txt
├── README.md
│
├── static/
│   ├── css/
│   ├── images/
│   └── js/
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── history.html
│   ├── reports.html
│   ├── prediction_details.html
│   ├── users.html
│   ├── audit_logs.html
│   └── settings.html
│
└── dataset/
```

---

## Database Design

The application uses PostgreSQL with the following tables:

- Users
- Drivers
- Vehicles
- Predictions
- Audit Logs
- Settings

---

## Installation

Clone the repository

```bash
git clone https://github.com/abbielnl/KMIPPS.git
```

Navigate to the project directory

```bash
cd KMIPPS
```

Install dependencies

```bash
pip install -r requirements.txt
```

Configure your PostgreSQL database connection in `db.py`.

Run the application

```bash
python app.py
```

Open your browser and visit

```text
http://127.0.0.1:5000
```

---

## System Modules

- Login
- Dashboard
- Premium Prediction
- Prediction History
- Reports
- PDF Generation
- Excel Export
- User Management
- Audit Logs
- Settings

---

## Future Improvements

- Integration with real insurance company datasets.
- Deployment to a cloud platform.
- REST API for third-party integrations.
- Mobile application.
- Deep learning-based premium prediction.
- Explainable AI (XAI) for model transparency.
- Multi-factor authentication.

---

## Author

**Abigail Kirimi**

Bachelor of Science in Data Science

KCA University

---

## Supervisor

Mr. Fredrick Omondi

KCA University

---

## Acknowledgements

Special appreciation to KCA University, the project supervisor, and all contributors whose guidance and support made the successful completion of this project possible.

---

## License

This project is licensed under the MIT License.
