from flask import Flask, render_template, request
import joblib, os, json, pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
MODEL_PATH = 'models/elasticnet_model.pkl'
METRICS_PATH = 'models/metrics.json'
DATA_PATH = 'data/employee_productivity.csv'

model = None
metrics = {}

def load_resources():
    global model, metrics
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH,'r') as f:
            metrics = json.load(f)

@app.route('/', methods=['GET','POST'])
def index():
        if request.method == 'POST':
            form = request.form
            try:
                hours = float(form.get('hours_worked_per_week', 40))
                meetings = int(form.get('meetings_per_week', 6))
                email_time = float(form.get('avg_email_response_time_mins', 60))
                projects = int(form.get('projects_handled', 2))
                coffee = int(form.get('coffee_cups_per_day', 2))
                training = float(form.get('training_hours_per_month', 6))
                exp = float(form.get('experience_years', 3))
                remote = float(form.get('remote_work_ratio', 0.5))
                distraction = float(form.get('distraction_hours_per_week', 5))
            except Exception as e:
                return 'Invalid input: {}'.format(e), 400

            X = pd.DataFrame([{
                'hours_worked_per_week': hours,
                'meetings_per_week': meetings,
                'avg_email_response_time_mins': email_time,
                'projects_handled': projects,
                'coffee_cups_per_day': coffee,
                'training_hours_per_month': training,
                'experience_years': exp,
                'remote_work_ratio': remote,
                'distraction_hours_per_week': distraction
            }])

            if model is None:
                return 'Model not found. Run train.py first.', 500

            pred = float(model.predict(X)[0])

            # create actual vs predicted plot sample
            if os.path.exists(DATA_PATH):
                df = pd.read_csv(DATA_PATH)
                sample = df.sample(80, random_state=1)
                Xs = sample.drop(columns=['productivity_score'])
                ys = sample['productivity_score'].values
                y_preds = model.predict(Xs)

                plt.figure(figsize=(6,4))
                plt.scatter(ys, y_preds)
                plt.plot([ys.min(), ys.max()], [ys.min(), ys.max()], linewidth=2)
                plt.xlabel('Actual Score')
                plt.ylabel('Predicted Score')
                plt.title('Actual vs Predicted (sample)')
                plot_path = os.path.join('static','imgs')
                os.makedirs(plot_path, exist_ok=True)
                plt.tight_layout()
                plt.savefig(os.path.join(plot_path,'actual_vs_pred.png'))
                plt.close()

            return render_template('result.html', pred=round(pred,2), metrics=metrics)
        else:
            return render_template('index.html', metrics=metrics)

if __name__ == '__main__':
    load_resources()
    app.run(host='0.0.0.0', port=5001, debug=True)
