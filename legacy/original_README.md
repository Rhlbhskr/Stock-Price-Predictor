# 📈 LSTM Stock Trend Prediction Web App

This Streamlit-based web app uses an **LSTM neural network** to predict stock prices. The app fetches historical stock data, preprocesses it, trains an LSTM model, evaluates it using RMSE and MAE, and forecasts prices for the next 60 days. Everything is visualized interactively for easy understanding.

---

## 🧠 How It Works

1. 📥 Fetches historical data from Yahoo Finance (2015–2025)
2. 🔄 Scales and reshapes the data for LSTM input
3. 🧪 Trains an LSTM model (or loads a pre-trained one)
4. 📊 Predicts test set prices and evaluates accuracy
5. 🔮 Forecasts next 60 days of stock prices
6. 📈 Visualizes actual vs predicted trends

---

## 🛠 Technologies Used

- **Python**
- **Streamlit**
- **TensorFlow / Keras**
- **scikit-learn**
- **yfinance**
- **Matplotlib**
- **NumPy / Pandas**

---
