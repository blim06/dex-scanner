from flask import Flask, request, render_template
import pandas as pd
import threading
import time
import requests

# Flask app initialization
app = Flask(__name__)

# API URL
BASE_URL = "https://api.geckoterminal.com/api/v2/networks/base/new_pools"

# Shared data
data_lock = threading.Lock()
all_data = []


# Function to fetch data continuously
def fetch_data():
    page = 1
    while True:
        try:
            response = requests.get(BASE_URL, params={"page": page})
            if response.status_code == 200:
                results = response.json()
                with data_lock:
                    for item in results.get("data", []):
                        attributes = item.get("attributes", {})
                        price_changes = attributes.get("price_change_percentage", {})
                        volumes = attributes.get("volume_usd", {})
                        transactions = attributes.get("transactions", {})
                        pool_id = item.get("id")

                        # Append the desired fields
                        all_data.append({
                            "pool_id": pool_id,
                            "name": attributes.get("name"),
                            "base_token_price_usd": attributes.get("base_token_price_usd"),
                            "fdv_usd": attributes.get("fdv_usd"),
                            "market_cap_usd": attributes.get("market_cap_usd"),
                            "reserve_in_usd": attributes.get("reserve_in_usd"),
                            "price_change_m5": price_changes.get("m5"),
                            "price_change_h1": price_changes.get("h1"),
                            "price_change_h6": price_changes.get("h6"),
                            "price_change_h24": price_changes.get("h24"),
                            "volume_m5": volumes.get("m5"),
                            "volume_h1": volumes.get("h1"),
                            "volume_h6": volumes.get("h6"),
                            "volume_h24": volumes.get("h24"),
                            "transactions_m5_buys": transactions.get("m5", {}).get("buys"),
                            "transactions_m5_sells": transactions.get("m5", {}).get("sells"),
                            "transactions_m15_buys": transactions.get("m15", {}).get("buys"),
                            "transactions_m15_sells": transactions.get("m15", {}).get("sells"),
                            "pool_created_at": attributes.get("pool_created_at"),
                            "address": attributes.get("address"),
                        })

            page = page + 1 if page < 10 else 1
            time.sleep(2)  # Respect API rate limits
        except Exception as e:
            print(f"Error fetching data: {e}")
            time.sleep(5)


# Start data fetching in a separate thread
threading.Thread(target=fetch_data, daemon=True).start()


@app.route("/", methods=["GET", "POST"])
def index():
    with data_lock:
        # Create a DataFrame for current data
        df = pd.DataFrame(all_data)

    filtered_df = df
    if request.method == "POST":
        attribute = request.form.get("attribute")
        condition = request.form.get("condition")
        try:
            value = float(request.form.get("value"))
            if condition == "greater":
                filtered_df = df[df[attribute].astype(float) > value]
            elif condition == "less":
                filtered_df = df[df[attribute].astype(float) < value]
        except ValueError:
            filtered_df = pd.DataFrame()  # Empty DataFrame for invalid input

    return render_template(
        "index.html",
        data=filtered_df.to_dict(orient="records"),
        columns=df.columns.tolist(),
    )


if __name__ == "__main__":
    app.run(debug=True)
