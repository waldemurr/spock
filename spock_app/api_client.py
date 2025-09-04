import requests


class APIClient:
    def __init__(self):
        self.base_url = "https://api.mexc.com/api/v3"

    def get_price(self, symbol):
        try:
            response = requests.get(f"{self.base_url}/ticker/price?symbol={symbol}USDT")
            data = response.json()
            return float(data["price"])
        except Exception as e:
            print(f"Ошибка при получении цены для {symbol}: {e}")
            # Попробуем альтернативный источник (CoinGecko)
            try:
                coin_id = self.get_coin_id(symbol)
                if coin_id:
                    response = requests.get(
                        f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
                    )
                    data = response.json()
                    return data[coin_id]["usd"]
            except Exception as e:
                print(f"Error occured : {e}")
                return 0.0
        return 0.0

    def get_coin_id(self, symbol):
        # Простое сопоставление символов с ID CoinGecko
        coin_mapping = {
            "TON": "the-open-network",
            "STG": "stargate-finance",
            "BTC": "bitcoin",
            "ETH": "ethereum",
            # Добавьте другие символы по необходимости
        }
        return coin_mapping.get(symbol, None)
