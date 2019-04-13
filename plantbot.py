import inspect
import logging
import os
from datetime import datetime as dt
from datetime import timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from constants import INTERVAL
from utils import get_daylight_hours, get_plant_data

load_dotenv(dotenv_path='.envrc')

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

scheduler = BlockingScheduler()

# get geolocation from ENV
LAT = os.environ.get("LAT")
LON = os.environ.get("LON")


@scheduler.scheduled_job(CronTrigger(minute='0', hour='0', day='*', month='*', day_of_week='*'))
def daily_trigger():
    """
    PlantBot trigger for connecting to all Mi Flora sensors (based on MAC address). Note that data is collected in
    different frequencies between day and night. Night is hourly, while day is based on INTERVAL between sunrise and
    sunset.

    """
    func_name = inspect.stack()[0][3]

    logging.info('[{}] -> Starting Job'.format(func_name))

    # get daylight times based on location
    today = dt.now().date()
    sunrise, sunset = get_daylight_hours(LAT, LON, today)

    # build trigger based on time of the day
    tomorrow = today + timedelta(days=1)
    morning = CronTrigger(minute='0', hour='0-{}'.format(sunrise), day='*', month='*', day_of_week='*',
                          end_date=tomorrow)
    day = CronTrigger(minute='0/{}'.format(INTERVAL), hour='{}-{}'.format(sunrise, sunset), day='*', month='*',
                      day_of_week='*', end_date=tomorrow)
    night = CronTrigger(minute='0', hour='{}-23'.format(sunset), day='*', month='*', day_of_week='*', end_date=tomorrow)
    trigger = OrTrigger([morning, day, night])

    # add new scheduled jobs
    logging.info("[{}] -> Adding scheduled job".format(func_name))
    scheduler.add_job(get_plant_data, trigger)


if __name__ == "__main__":
    scheduler.start()
