from multiprocessing import Manager

# This shared dictionary will store the progress of all jobs.
# In a real-world scenario, a dedicated backend like Redis with Celery is recommended.
job_status = Manager().dict()