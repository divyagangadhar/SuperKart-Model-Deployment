# Flask backend for the SuperKart sales forecasting service
import os
import joblib
import pandas as pd
from flask import Flask, request, jsonify

app = Flask("SuperKart Sales Forecaster")

# Load the serialized pipeline once at start-up (preprocessing + model travel together)
MODEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "superkart_sales_model_v1_0.joblib")
model = joblib.load(MODEL_FILE)

# Input contract: the same columns the pipeline was trained on
FEATURES = [
    "Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_MRP",
    "Store_Size", "Store_Location_City_Type", "Store_Type", "Product_Id_char",
    "Store_Age_Years", "Product_Type_Category",
]

@app.get("/")
def home():
    return jsonify({"service": "SuperKart Sales Forecaster", "status": "running",
                    "endpoints": ["POST /v1/sales", "POST /v1/salesbatch"]})

@app.post("/v1/sales")
def predict_single():
    """Predict sales for ONE product-store combination. Expects a JSON body with the FEATURES keys."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Send a JSON body with the product and store attributes."}), 400
    missing = [f for f in FEATURES if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400
    try:
        row = pd.DataFrame([{f: data[f] for f in FEATURES}])
        prediction = float(model.predict(row)[0])
        return jsonify({"Predicted_Product_Store_Sales_Total": round(prediction, 2)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

@app.post("/v1/salesbatch")
def predict_batch():
    """Predict sales for MANY rows. Expects a CSV upload in the form field 'file' containing the FEATURES columns."""
    if "file" not in request.files:
        return jsonify({"error": "Upload a CSV file in the form field 'file'."}), 400
    try:
        batch = pd.read_csv(request.files["file"])
        missing = [f for f in FEATURES if f not in batch.columns]
        if missing:
            return jsonify({"error": f"CSV is missing columns: {missing}"}), 400
        preds = model.predict(batch[FEATURES]).round(2)
        out = batch.copy()
        out["Predicted_Product_Store_Sales_Total"] = preds
        return jsonify(out.to_dict(orient="records"))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)), debug=False)
