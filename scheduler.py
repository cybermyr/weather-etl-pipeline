import schedule
import time 
from main import run_pipeline

schedule.every(45).minutes.do(run_pipeline)

while True:
    schedule.run_pending()
    time.sleep(60)