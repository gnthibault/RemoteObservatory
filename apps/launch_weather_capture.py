# Generic import
import pandas
import time

# plotly
from plotly import graph_objs as plotly_go
from plotly import plotly
from plotly import tools as plotly_tools

# local
from Service.DummyCloudSensor import DummyCloudSensor

names = [
    'date',
    'safe',
    'ambient_temp_C',
    'sky_temp_C',
    'rain_sensor_temp_C',
    'rain_frequency',
    'wind_speed_KPH',
    'ldr_resistance_Ohm',
    'pwm_value',
    'gust_condition',
    'wind_condition',
    'sky_condition',
    'rain_condition',
]

header = ','.join(names)


def write_header(filename):
    # Write out the header to the CSV file
    with open(filename, 'w') as f:
        f.write(header)


def write_capture(filename=None, data=None):
    """ A function that reads the AAG weather can calls itself on a timer """
    entry = "{},{},{},{},{},{},{},{:0.5f},{:0.5f},{},{},{},{}\n".format(
        data['date'].strftime('%Y-%m-%d %H:%M:%S'),
        data['safe'],
        data['ambient_temp_C'],
        data['sky_temp_C'],
        data['rain_sensor_temp_C'],
        data['rain_frequency'],
        data['wind_speed_KPH'],
        data['ldr_resistance_Ohm'],
        data['pwm_value'],
        data['gust_condition'],
        data['wind_condition'],
        data['sky_condition'],
        data['rain_condition'],
    )

    if filename is not None:
        with open(filename, 'a') as f:
            f.write(entry)


if __name__ == '__main__':
    import argparse

    # Get the command line option
    parser = argparse.ArgumentParser(
        description="Make a plot of the weather for a given date.")

    parser.add_argument('--loop', action='store_true', default=True,
                        help="If should keep reading, defaults to True")
    parser.add_argument("-d", "--delay", dest="delay", default=30.0, type=float,
                        help="Interval to read weather")
    parser.add_argument("-f", "--filename", dest="filename", default=None,
                        help="Where to save results")
    parser.add_argument('--serial-port', dest='serial_port', default=None,
                        help='Serial port to connect')
    parser.add_argument('--store-result', action='store_true',
                        default=False, help="Save to db")
    parser.add_argument('--send-message', action='store_true',
                        default=False, help="Send message")
    args = parser.parse_args()

    # Weather object
    #aag = weather.AAGCloudSensor(serial_address=args.serial_port,
    #                             store_result=args.store_result)
    aag = DummyCloudSensor(store_result=args.store_result)

    while True:
        data = aag.capture(store_result=args.store_result,
                           send_message=args.send_message)

        # Save to file
        if args.filename is not None:
            write_capture(filename=args.filename, data=data)

        if not args.loop:
            break

        time.sleep(args.delay)

