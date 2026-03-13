import time


def retry(operation, retries=3, delay=2):

	for attempt in range(retries):

		try:
			return operation()

		except Exception as e:

			if attempt == retries - 1:
				raise e

			time.sleep(delay * (attempt + 1))