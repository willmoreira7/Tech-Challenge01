import os
import mlflow
import mlflow.sklearn
import numpy as np
from flask import Flask, jsonify, request
from sklearn.linear_model import LinearRegression

app = Flask(__name__)

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("flask-demo")

# Modelo em memória (substitua pelo seu modelo real)
_model = LinearRegression()
_model.fit([[1], [2], [3]], [2, 4, 6])  # y = 2x de exemplo


@app.route("/health")
def health():
    return jsonify({"status": "ok", "mlflow_uri": MLFLOW_URI})


@app.route("/train", methods=["POST"])
def train():
    """Treina um modelo simples e loga no MLflow."""
    body = request.get_json(force=True)
    X = np.array(body["X"]).reshape(-1, 1)
    y = np.array(body["y"])

    with mlflow.start_run() as run:
        model = LinearRegression()
        model.fit(X, y)

        score = model.score(X, y)
        mlflow.log_param("n_samples", len(X))
        mlflow.log_metric("r2_score", score)
        mlflow.sklearn.log_model(model, "model")

        global _model
        _model = model

        return jsonify({
            "run_id": run.info.run_id,
            "r2_score": score,
        })


@app.route("/predict", methods=["POST"])
def predict():
    """Faz predição com o modelo em memória."""
    body = request.get_json(force=True)
    X = np.array(body["X"]).reshape(-1, 1)
    predictions = _model.predict(X).tolist()

    with mlflow.start_run():
        mlflow.log_metric("predict_calls", 1)

    return jsonify({"predictions": predictions})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
