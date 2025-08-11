import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib, os, json

os.makedirs('data', exist_ok=True)
os.makedirs('models', exist_ok=True)
np.random.seed(42)

N = 920  # number of synthetic employees

# Features
hours_worked_per_week = np.random.normal(40, 8, N).clip(10, 80)
meetings_per_week = np.random.poisson(6, N)
avg_email_response_time = np.random.exponential(60, N).clip(5, 1000)  # in minutes
projects_handled = np.random.poisson(2, N) + 1
coffee_cups_per_day = np.random.poisson(2, N)
training_hours_per_month = np.random.normal(6, 4, N).clip(0, 60)
experience_years = np.random.normal(4, 3, N).clip(0, 30)
remote_work_ratio = np.random.beta(2,2, N)  # between 0 and 1
distraction_hours_per_week = np.random.normal(5, 3, N).clip(0, 40)

# Introduce some correlated features intentionally
meetings_per_week = (0.6 * meetings_per_week + 0.4 * (projects_handled*2)).astype(int)

# Base productivity (0-100 scale) from a made-up linear combination + non-linear effects
base = (
    hours_worked_per_week * 0.8
    - meetings_per_week * 0.9
    - avg_email_response_time * 0.02
    + projects_handled * 3.5
    + training_hours_per_month * 0.6
    + experience_years * 1.2
    - distraction_hours_per_week * 1.5
    + (remote_work_ratio - 0.5) * 5  # slight effect
    + coffee_cups_per_day * 0.4
)

# Non-linear boost for some (e.g., too many hours reduces productivity after threshold)
base += -0.02 * np.maximum(0, hours_worked_per_week - 55)**2 / 10.0

# Map to 0-100 and add noise
productivity_score = 50 + (base - base.mean()) / (base.std() + 1e-9) * 10
productivity_score += np.random.normal(0, 6, N)
productivity_score = np.clip(productivity_score, 0, 100)

df = pd.DataFrame({
    'hours_worked_per_week': hours_worked_per_week.round(1),
    'meetings_per_week': meetings_per_week,
    'avg_email_response_time_mins': avg_email_response_time.round(1),
    'projects_handled': projects_handled,
    'coffee_cups_per_day': coffee_cups_per_day,
    'training_hours_per_month': training_hours_per_month.round(1),
    'experience_years': experience_years.round(1),
    'remote_work_ratio': remote_work_ratio.round(2),
    'distraction_hours_per_week': distraction_hours_per_week.round(1),
    'productivity_score': productivity_score.round(2)
})

df.to_csv('data/employee_productivity.csv', index=False)

# Features and target
X = df.drop(columns=['productivity_score'])
y = df['productivity_score']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a single ElasticNet (fast)
model = ElasticNet(alpha=1.0, l1_ratio=0.5, max_iter=5000, random_state=42)
model.fit(X_train, y_train)

preds = model.predict(X_test)
rmse = mean_squared_error(y_test, preds, squared=False)
r2 = r2_score(y_test, preds)

print(f'Test RMSE: {rmse:.3f}')
print(f'Test R2: {r2:.4f}')

joblib.dump(model, 'models/elasticnet_model.pkl')

with open('models/metrics.json', 'w') as f:
    json.dump({'rmse': float(rmse), 'r2': float(r2), 'alpha': 1.0, 'l1_ratio': 0.5}, f)

print('Saved model and dataset.')
