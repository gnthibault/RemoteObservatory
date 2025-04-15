# Basic stuff
import logging

# Local stuff : Camera
from Service.IndiWeather import IndiWeather
from Service.NTPTimeService import HostTimeService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')

def test_indiSimulatorCamera():
    config = dict(
        service_name="Weather Simulator",
        key_path="/opt/RemoteObservatory/keys.json",
        delay_sec=60,
        observatory=dict(
            latitude=43.56, # Degrees
            longitude=5.43, # Degrees
            elevation=150.0), # Meters
        limits=dict(
            MAX_WEATHER_WIND_SPEED_KPH=25,
            MAX_WEATHER_WIND_GUST_KPH=30,
            MAX_WEATHER_CLOUD_COVER=5),
        indi_client=dict(
            indi_host="localhost",
            indi_port="7624")
    )
    # test indi virtual camera class
    w = IndiWeather(serv_time=HostTimeService(),
                    config=config,
                    connect_on_create=False,
                    loop_on_create=False)
    w.connect()
    status, features = w.get_weather_features()
    data = w._fill_in_weather_data()
    w._make_safety_decision(data)
    w.disconnect()