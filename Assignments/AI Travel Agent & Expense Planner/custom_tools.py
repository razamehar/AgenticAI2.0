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
class Forex:
    """
    Tool to convert amounts from one currency to another using Fixer API.
    Uses EUR as the base currency for conversion rates.
    """

    def __init__(self) -> None:
        """
        Initialize Forex tool with the Fixer API endpoint.
        """
        self.latest_url = "http://data.fixer.io/api/latest"

    def get_rates(self) -> dict[str, float]:
        """
        Fetch the latest currency exchange rates from Fixer API.

        Returns:
            dict[str, float]: Mapping of currency codes to their rates relative to EUR.

        Raises:
            ValueError: If the API call is unsuccessful.
        """
        params = {"access_key": FOREX_API_KEY}
        response = requests.get(self.latest_url, params=params)
        data = response.json()
        if data.get("success"):
            return data["rates"]
        else:
            raise ValueError("Failed to fetch currency rates")

    def convert(self, amount: float, from_currency: str, to_currency: str) -> str:
        """
        Convert a given amount from one currency to another.

        Args:
            amount (float): The amount to convert.
            from_currency (str): The currency code to convert from (e.g., "USD").
            to_currency (str): The currency code to convert to (e.g., "PKR").

        Returns:
            str: A formatted string showing the conversion result.

        Notes:
            If from_currency equals to_currency, returns the same amount.
            Conversion is done via EUR as the base currency.
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

    def __call__(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> str:
        """
        Make the Forex instance callable for convenient conversions.

        Args:
            amount (float): The amount to convert.
            from_currency (str): The currency code to convert from.
            to_currency (str): The currency code to convert to.

        Returns:
            str: The conversion result or an error message.
        """
        try:
            return self.convert(amount, from_currency, to_currency)
        except Exception as e:
            return f"Error: {e}"



@tool
class Accommodation:
    """
    Tool for retrieving hotel information including prices and addresses
    in a specified city using DuckDuckGo search.
    """

    def hotel_info(self, city: str) -> list[str]:
        """
        Search for hotels in the given city and return a list of formatted hotel entries.

        Args:
            city (str): The name of the city to search hotels in.

        Returns:
            list[str]: A list of hotel info strings (title + snippet).
        """
        search = DuckDuckGoSearchResults()
        query = f"Hotels with prices and addresses in {city}"
        result = search.invoke(query)

        formatted_results = []
        for item in result:
            title = item.get("title", "No title")
            snippet = item.get("snippet", "")
            formatted_results.append(f"{title}: {snippet}")

        return formatted_results[:5]