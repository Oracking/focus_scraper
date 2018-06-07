'''
This file is to help brief you on how to use the FocusScraper object to
get information from focus.
'''
from Authorizations import Credentials # Remove this line. It is for testing.
from little_focus_scraper import FocusScraper

# Replace Credentials.USERNAME and Credentials.PASSWORD with strings of your
# username and password
username = Credentials.USERNAME
password = Credentials.PASSWORD

# Create your scraper object
f_scraper = FocusScraper(username, password)

# Scraper object has 4 main useful methods. The first is the login. You will
# always be required to login after creating your scraper objects
f_scraper.login()

# You can call the login method right after creating the object to avoid
# forgetting to call it later in your script like so:
f_scraper = FocusScraper(Credentials.USERNAME, Credentials.PASSWORD).login()

# You can then check all your results for a particular year and semester.
# Semester values can be one of the following: [fall, spring, summer]
print(f_scraper.get_sem_results(2017, "fall"))

# You can check your results in a semester for one particular subject.
# Note: The last argument, which is the course, can be any substring of the
# course you are searching for, such that it is unique to that course. So if
# your courses are: [Multivariable Calculus, Physics, Multiple Differentiation],
# you can call the function like so
print(f_scraper.check_course_grade(2017, "fall", "Multiv"))


# The last is a decorator to constantly monitor a semester. You can use it to
# decorate your handler class, which will handle the results like so:
@f_scraper.monitor_semester(interval_seconds=20, args=(2017, "spring"))
def monitor_handler(results, changes):
	'''
	Over here you define a function that will handle results from the
	scraper. It should have two parameters: [results, changes], where
	results is your complete results for the semester, and changes is
	the changes that has occurred since it started monitoring. Naturally,
	it will return all your grades as changes for the first time it checks
	so you may want to handle that.
	'''
	print(changes)

# After that, you have to explicitly call your monitor for it to start
monitor_handler.start()
