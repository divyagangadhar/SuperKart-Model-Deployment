# Streamlit frontend for the SuperKart sales forecasting service
import os
import requests
import pandas as pd
import streamlit as st

# URL of the deployed Flask backend (set BACKEND_URL as an environment variable / Space variable)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:5000").rstrip("/")

st.set_page_config(page_title="SuperKart Sales Forecaster", layout="centered")
st.title("SuperKart Sales Forecaster")
st.caption("Forecast the sales revenue of a product in a store.")

tab_single, tab_batch = st.tabs(["Single prediction", "Batch prediction"])

# ---------------- Single prediction ----------------
with tab_single:
    st.subheader("Enter product and store details")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Product**")
        product_id_char = st.selectbox("Product group (Product_Id prefix)", ["FD", "DR", "NC"],
                                       help="FD = Food, DR = Drinks, NC = Non-consumable")
        category = st.selectbox("Product category", ["Perishables", "Non Perishables"])
        sugar = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
        weight = st.number_input("Product weight", min_value=1.0, max_value=30.0, value=12.65, step=0.1)
        area = st.number_input("Allocated display area (ratio)", min_value=0.0, max_value=0.5, value=0.056, step=0.001, format="%.3f")
        mrp = st.number_input("Product MRP", min_value=10.0, max_value=400.0, value=147.0, step=1.0)
    with c2:
        st.markdown("**Store**")
        size = st.selectbox("Store size", ["High", "Medium", "Small"])
        city = st.selectbox("City tier", ["Tier 1", "Tier 2", "Tier 3"])
        store_type = st.selectbox("Store type", ["Supermarket Type1", "Supermarket Type2", "Departmental Store", "Food Mart"])
        age = st.number_input("Store age (years)", min_value=0, max_value=60, value=17, step=1)

    if st.button("Predict sales", type="primary"):
        payload = {
            "Product_Weight": weight, "Product_Sugar_Content": sugar, "Product_Allocated_Area": area,
            "Product_MRP": mrp, "Store_Size": size, "Store_Location_City_Type": city,
            "Store_Type": store_type, "Product_Id_char": product_id_char,
            "Store_Age_Years": int(age), "Product_Type_Category": category,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/v1/sales", json=payload, timeout=30)
            if resp.status_code == 200:
                st.success(f"Predicted sales: {resp.json()['Predicted_Product_Store_Sales_Total']:,.2f}")
            else:
                st.error(f"Backend error: {resp.text}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not reach the backend at {BACKEND_URL}: {exc}")

# ---------------- Batch prediction ----------------
with tab_batch:
    st.subheader("Upload a CSV for batch forecasting")
    st.write("Required columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, Product_MRP, "
             "Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, Store_Age_Years, Product_Type_Category")
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded is not None:
        st.dataframe(pd.read_csv(uploaded).head(), use_container_width=True)
        uploaded.seek(0)
        if st.button("Predict for all rows"):
            try:
                resp = requests.post(f"{BACKEND_URL}/v1/salesbatch", files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")}, timeout=120)
                if resp.status_code == 200:
                    result = pd.DataFrame(resp.json())
                    st.dataframe(result, use_container_width=True)
                    st.download_button("Download predictions", result.to_csv(index=False), "superkart_predictions.csv", "text/csv")
                else:
                    st.error(f"Backend error: {resp.text}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not reach the backend at {BACKEND_URL}: {exc}")
