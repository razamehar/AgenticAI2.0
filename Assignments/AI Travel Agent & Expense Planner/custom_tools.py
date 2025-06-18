from langchain.tools import tool
from typing import Union, List, Tuple, Optional
from langchain_community.tools import DuckDuckGoSearchResults
import requests
from dotenv import load_dotenv
load_dotenv()


@tool
class Weather:
    """
    A tool for retrieving current weather and weather forecast data using the WeatherAPI.
    
    Methods:
        - get_current_weather(city): Get real-time weather conditions for a specific city.
        - get_weather_forecast(city, days): Get the weather forecast for a specific number of days.
    """

    def get_current_weather(self, city: str) -> dict:
        """
        Fetches the current weather data for a given city.

        Args:
            city (str): The name of the city for which to get current weather.

        Returns:
            dict: A dictionary containing:
                - location (str): City name.
                - country (str): Country name.
                - temperature_c (float): Current temperature in Celsius.
                - condition (str): Weather condition text.
                - humidity (int): Current humidity percentage.
                - wind_kph (float): Wind speed in kilometers per hour.
                - error (str, optional): Error message if the API call fails.
        """
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            return {
                "location": data["location"]["name"],
                "country": data["location"]["country"],
                "temperature_c": data["current"]["temp_c"],
                "condition": data["current"]["condition"]["text"],
                "humidity": data["current"]["humidity"],
                "wind_kph": data["current"]["wind_kph"]
            }
        else:
            return {
                "error": data.get("error", {}).get("message", "Failed to fetch data")
            }

    def get_weather_forecast(self, city: str, days: int = 3) -> dict:
        """
        Fetches the weather forecast for a given city and number of days.

        Args:
            city (str): The name of the city for which to get the forecast.
            days (int): Number of days to forecast (default is 3, max is 10 as per API limits).

        Returns:
            dict: A dictionary containing:
                - location (str): City name.
                - country (str): Country name.
                - forecast (list): List of daily forecast dictionaries, each with:
                    - date (str): Forecast date.
                    - max_temp_c (float): Maximum temperature in Celsius.
                    - min_temp_c (float): Minimum temperature in Celsius.
                    - condition (str): Forecast weather condition.
                    - chance_of_rain (str or int): Chance of rain percentage.
                - error (str, optional): Error message if the API call fails.
        """
        url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days={days}&aqi=no&alerts=no"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            forecast_days = []
            for day in data["forecast"]["forecastday"]:
                forecast_days.append({
                    "date": day["date"],
                    "max_temp_c": day["day"]["maxtemp_c"],
                    "min_temp_c": day["day"]["mintemp_c"],
                    "condition": day["day"]["condition"]["text"],
                    "chance_of_rain": day["day"].get("daily_chance_of_rain", "N/A")
                })
            return {
                "location": data["location"]["name"],
                "country": data["location"]["country"],
                "forecast": forecast_days
            }
        else:
            return {
                "error": data.get("error", {}).get("message", "Failed to fetch forecast")
            }
        

@tool
class TopAttractions:
    """
    A tool to fetch top attractions or points of interest in a specified city
    using the Foursquare Places API.

    Methods:
        get_places(city): Returns a list of top places in the city with their names and addresses.
    """
    def get_places(self, city: str) -> Union[List[Tuple[str, str]], str]:
        """
        Fetches top attractions (points of interest) in a given city using the Foursquare Places API.

        Args:
            city (str): Name of the city to search places in.

        Returns:
            list of tuples: Each tuple contains (name, address) of a place.
            If the API request fails, returns an error message string.
        """
        url = "https://api.foursquare.com/v3/places/search"
        headers = {
            "Accept": "application/json",
            "Authorization": FOURSQUARE_API_KEY
        }
        params = {
            "near": city,
            "limit": 10
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            places = data.get("results", [])
            results = []
            for place in places:
                name = place.get("name")
                address_list = place.get("location", {}).get("formatted_address", [])
                address = ", ".join(address_list) if isinstance(address_list, list) else address_list
                results.append((name, address))
            return results
        else:
            return f"Error: {response.status_code} - {response.text}"


@tool
class CurrencyExchange:
    """
    Tool for converting amounts between currencies using the Fixer API.
    All conversion rates are based on EUR as the base currency.
    """

    def get_rates(self) -> dict[str, float]:
        """
        Fetches the latest exchange rates from the Fixer API with EUR as the base.

        Returns:
            dict[str, float]: A dictionary mapping currency codes to their exchange rates 
            relative to EUR.

        Raises:
            ValueError: If the API call fails or returns an unsuccessful response.
        """
        params = {"access_key": FOREX_API_KEY}
        self.url = "http://data.fixer.io/api/latest"
        response = requests.get(self.url, params=params)
        data = response.json()
        if data.get("success"):
            return data["rates"]
        else:
            raise ValueError("Failed to fetch currency rates")

    def convert(self, amount: float, from_currency: str, to_currency: str) -> str:
        """
        Converts a monetary amount from one currency to another using live exchange rates.

        Args:
            amount (float): The amount of money to convert.
            from_currency (str): The 3-letter currency code to convert from (e.g., "USD").
            to_currency (str): The 3-letter currency code to convert to (e.g., "PKR").

        Returns:
            str: A formatted string showing the converted amount.

        Notes:
            - If both currencies are the same, the original amount is returned unchanged.
            - Conversion is done indirectly using EUR as the intermediary currency.
            - If either currency is not supported, a message is returned indicating that.
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return f"{amount:.2f} {from_currency} = {amount:.2f} {to_currency}"

        rates = self.get_rates()

        if from_currency not in rates or to_currency not in rates:
            return "Currency not supported"

        rate_from = rates[from_currency]
        rate_to = rates[to_currency]

        amount_in_eur = amount / rate_from
        converted_amount = amount_in_eur * rate_to

        return f"{amount:.2f} {from_currency} = {converted_amount:.2f} {to_currency}"



@tool
class Accommodation:
    """
    Tool for retrieving hotel information in a specified city.

    This tool uses DuckDuckGo to search for hotels and returns key details such as 
    ratings, prices, addresses, and official websites.
    """

    def hotel_info(self, city: str) -> list[str]:
        """
        Retrieves a list of hotels in the specified city with summarized information.

        Args:
            city (str): Name of the city to search for hotels in.

        Returns:
            list[str]: A list of up to five formatted strings, each containing 
                       the hotel's title and a brief description including 
                       rating, price, address, and website if available.
        """
        search = DuckDuckGoSearchResults(output_format="list")
        query = f"Hotels with ratings, prices, addresses and websites in {city}"
        result = search.invoke(query)

        formatted_results = []
        for item in result:
            title = item.get("title", "No title")
            snippet = item.get("snippet", "")
            formatted_results.append(f"{title}: {snippet}")

        return formatted_results[:5]
