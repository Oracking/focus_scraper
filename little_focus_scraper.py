from littlesoup import LittleSoup
import requests
import time
import threading
import functools

class FocusScraper():

    LOGIN_URL = "https://sis.ashesi.edu.gh/focus/index.php"
    BASE_URL = "https://sis.ashesi.edu.gh/focus/"
    LOGGED_IN_URL = "https://sis.ashesi.edu.gh/focus/index.php?modfunc" \
                    "=loggedin"
    LOGGED_IN_URL_S = "https://sis.ashesi.edu.gh/focus/index.php"
    SESSIONS_URL = "https://sis.ashesi.edu.gh/focus/Modules.php" \
                    "?modname=misc/Portal.php"
    GRADE_SHORT_HREF = "Modules.php?modname=Grades/StudentGBGrades.php?" \
                       "course_period_id="
    COURSENAME_HREF = "http://sis.ashesi.edu.gh/focus/modules/moodle/" \
                            "course/view.php?side_period="

    # Initialize the object to store user credentials
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.mem_cache = {}
        self.grades_cache = {}
        self.threads = []
        # self.mem_cache = {2016:
        #                      {'Fall Session':
        #                          {'Statistics for Engineering':
        #                               {'grade_tag_href': grade_tag_href}
        #                          }
        #                      }
        #                   }

    # Create a session and respective object attributes that will be used
    # for the rest of the scraping process
    def login(self):
        self.session = requests.Session()
        response = self.session.post(self.LOGIN_URL, data={
                                           "USERNAME": self.username,
                                           "PASSWORD": self.password})

        # Error handling to check if login failed
        soup = LittleSoup(response.content, response.encoding)
        login_form_query = soup.find_all('form', {'name': 'loginform'})
        if len(login_form_query) > 0:
            raise ValueError("\n\nFailed to login to focus with the given" \
                             " credentials. Please check and try again")

        # Get frame that loads the body content
        self.main_page = soup

        # This gets the body html and assigns it to self.main_body
        self.extract_body_from_frame()
        self.init_page_details = {}

        # Get initial details
        sessions_selector = self.main_body.find('select',
                                                {'name': 'side_mp'})
        fall_option = sessions_selector.find('option', string="Fall Session")
        side_mp = fall_option['value']

        year_selector = self.main_body.find('select', {'name': 'side_syear'})
        year_options = year_selector.find_all('option')

        for option in year_options:
            try:
                t = option['selected']
                year_option = option
            except:
                pass
        side_syear = year_option['value']
        self.init_page_details = {'side_mp': side_mp, 'side_syear': side_syear}


        print("Logged in as: {0}".format(self.username))
        return self


    # Method to check the grade of a particular course in a particular semester
    def check_course_grade(self, academic_year, semester, course_name):
        # Errors with method:
            # There is no way to catch bad academic_year values

        course_grades = self.get_sem_results(academic_year, semester)

        course_names = list(set(course_grades.keys()))

        matching_names = [name for name in course_names if course_name in name]
        matching_names = list(set(matching_names))

        str_course_list = "\n"
        for i_course_name in course_names:
            str_course_list += i_course_name + "\n"

        str_matching_names = "\n"
        for i_matching_name in matching_names:
            str_matching_names += i_matching_name + "\n"

        error_surround = "------"
        if len(matching_names) == 0:
            raise ValueError("\n\nNo matching course found for: '{0}'" \
                             " within {1} of {2} academic year. " \
                             "Available courses in that period are:\n" \
                             "{3}".format(course_name, semester, \
                                          academic_year, str_course_list))

        elif len(matching_names) > 1:
            raise ValueError("\n\nFound multiple courses matching '{0}'." \
                              " The following courses showed up as"
                              " possible matches:\n {1}\n\n" \
                              "Please be more specific with your query" \
                              " such that only one match is found" \
                              "".format(course_name, str_matching_names))
        else:
            matching_name = matching_names[0]
            grade = course_grades[matching_name]

        return tuple(grade)



    def get_sem_results(self, academic_year, semester, cache_results=True):
        semesters = ['spring', 'summer', 'fall']
        semester = semester.lower()

        # Try to catch invalid semester option
        if semester not in semesters:
            raise ValueError("Not a valid semester. Semester can either be"
                             " 'spring', 'fall', or 'summer'")

        else:
            if semester == "summer":
                semester = semester.title() + " " + "Semester"
            else:
                semester = semester.title() + " " + "Session"

            course_names = []
            retrieved_from_cache = False
            courses_dict = {}

            try:
                courses_dict = self.mem_cache[academic_year][semester]
                retrieved_from_cache = True

            except KeyError:
                # Raise exception if it not expected
                pass


            sessions_selector = self.main_body.find('select',
                                                    {'name': 'side_mp'})
            option = sessions_selector.find('option', string=semester)
            side_mp = option['value']

            # This request returns the main body not the main frame
            response = self.login_required_request(self.SESSIONS_URL,
                                             {"side_mp": side_mp,
                                             "side_syear": academic_year},
                                             "POST")

            self.main_page = LittleSoup(response.content, response.encoding)
            self.extract_body_from_frame()

            # Do two things:
            #   - Cache courses and their grade_tag_href
            #   - Return course and grade tuple
            if not retrieved_from_cache:
                a_tags = self.main_body.find_all('a')
                course_name_tags = []
                course_names = []

                try:
                    self.mem_cache[academic_year][semester] = {}
                except KeyError:
                    self.mem_cache[academic_year] = {semester: {}}

                for a_tag in a_tags:
                    try:
                        link = str(a_tag['href'])
                        if self.COURSENAME_HREF in link:
                            course_name = str(a_tag.string).split("-")[0] \
                                              .strip()

                            period_id = a_tag['href'].split("=")[1]
                            grade_tag_href = self.GRADE_SHORT_HREF + period_id

                            self.mem_cache[academic_year][semester] \
                                          [course_name] = {'grade_tag_href':
                                                            grade_tag_href}

                    except Exception as e:
                        # If it is not an expected exception do not pass
                        pass
                courses_dict = self.mem_cache[academic_year][semester]


            if len(courses_dict.keys()) == 0:

                # Navigate back to the main page
                fall_option = sessions_selector.find('option', string="Fall Session")
                side_mp = fall_option['value']
                #side_mp = self.init_page_details['side_mp']
                side_syear = self.init_page_details['side_syear']

                d = {'side_mp': side_mp, 'side_syear': side_syear}


                response = self.login_required_request(self.SESSIONS_URL,
                                             {"side_mp": side_mp,
                                              "side_syear": academic_year},
                                              "POST")

                #self.main_body = LittleSoup(response.content, response.encoding)

                # Page needs to be reloaded twice
                response = self.login_required_request(self.LOGGED_IN_URL, {},
                                                       "GET")

                self.main_page = LittleSoup(response.content, response.encoding)
                self.extract_body_from_frame()


                raise ValueError(f"You entered an invalid year. You have not" \
                                 f" taken any courses within {semester}" \
                                 f" of {academic_year} academic year.")

            results = {}
            for course_name, course_details in courses_dict.items():
                grade_tag_href = course_details['grade_tag_href']
                grade_tag = self.main_body.find('a', {'href': grade_tag_href})
                grade = grade_tag.string.split(" ")
                results[course_name] = grade

            if cache_results:
                try:
                    self.grades_cache[academic_year][semester] = results
                except KeyError:
                    self.grades_cache[academic_year] = {semester: results}
            return results


    def monitor_semester(self, interval_seconds, args):

        if not isinstance(interval_seconds, type(1)):
            type_got = type(interval_seconds)
            raise TypeError("Expected wait time to be of type 'int' got {0}" \
                .format(type_got))

        def function_decorator(function):
            def threaded_monitor():
                while True:
                    try:
                        academic_year, semester = tuple(args)
                        results = self.get_sem_results(academic_year, semester, cache_results=False)
                        try:
                            cached_results = self.grades_cache[academic_year][semester]
                        except Exception as e:
                            # Handle exception properly
                            cached_results = {}

                        # Compare cached results to results and send updates
                        changes = {}
                        for course, grade in results.items():
                            try:
                                cached_grade = cached_results[course]
                                if str(grade) != str(cached_grade):
                                    changes[course] = grade
                            except KeyError:
                                changes[course] = grade

                        try:
                            self.grades_cache[academic_year][semester] = results
                        except KeyError:
                            self.grades_cache[academic_year] = {semester: results}

                        function(results, changes)
                    except Exception as e:
                        print(e)
                    time.sleep(interval_seconds)

            thread = threading.Thread(target=threaded_monitor)
            # thread.daemon = True
            self.threads.append(thread)
            return thread
        return function_decorator


    def monitor_course(self, function, interval_seconds, academic_year, semester, course_name):
        pass

    # Try to load the page and re-login if needed
    def login_required_request(self, url, params, method):
        # Try to get page
        if method == 'POST':
            response = self.session.post(url, data=params)
        if method == 'GET':
            response = self.session.get(url, data=params)

        # Use the login form to determine if we are on login page
        soup = LittleSoup(response.content, response.encoding)
        login_form_query = soup.find_all('form', {'name': 'loginform'})
        if len(login_form_query) > 0:
            self.login()
            if method == 'POST':
                response = self.session.post(url, data=params)
            if method == 'GET':
                response = self.session.get(url, data=params)

        return response


    def extract_body_from_frame(self):
        main_frame = self.main_page.find("frame", {"name": "body"})

        # Get the source of frame and load the body content as a new request
        if main_frame:
            self.body_src = self.BASE_URL + main_frame['src']
            response = self.session.get(self.body_src)
            self.main_body = LittleSoup(response.content, response.encoding)
        else:
            self.main_body = self.main_page
