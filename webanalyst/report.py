from bs4.element import ResultSet
from webanalyst import clerk
import re
from webanalyst import HTMLinator as html
from bs4 import BeautifulSoup
import logging
from webanalyst import validator as val
import os
from webanalyst.CSSinator import Stylesheet as stylesheet
from webanalyst import stylesheet_analyst as css_analyst

logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')
report_template_path = "webanalyst/report_template.html"
report_path = "report/report.html"


class Report:
    def __init__(self, dir_path):
        self.__readme_path = dir_path + "README.md"
        self.__readme_text = clerk.file_to_string(self.__readme_path)
        self.__readme_list = re.split("[\n]", self.__readme_text)
        self.general_report = None
        self.html_report = None
        self.css_report = None
        self.__dir_path = dir_path

    def get_readme_text(self):
        return self.__readme_text

    def get_readme_list(self):
        return self.__readme_list

    @staticmethod
    def get_report_results_string(tr_class, type_column, target, 
                                  results, results_key):
        results_key = str(results_key)
        if tr_class:
            results_string = '<tr class="' + tr_class + '">'
        else:
            results_string = '<tr>'
        results_string += '<td>' + type_column + '</td>'
        if target != "":
            results_string += '<td>' + str(target) + '</td>'
        if results != "":
            results_string += "<td>" + str(results) + "</td>"
        if results_key == "True":
            meets = "Meets"
        else:
            meets = "Does Not Meet"
        results_string += "<td>" + meets + "</td>"
        results_string += "</tr>"
        return results_string

    @staticmethod
    def get_header_details(header_string):
        header_list = header_string.split(":")
        title = header_list[0]
        title = title.strip()
        if "* " in title[:]:
            title = title[2:]
        description = header_list[1]
        return {"title": title, "details": {"description": description.strip()}}

    @staticmethod 
    def foo():
        pass

    def generate_report(self):
        # pull readme text
        self.get_readme_text()

        # instantiate all reports
        self.general_report = GeneralReport(self.__readme_list,
                                            self.__dir_path)
        self.html_report = HTMLReport(self.__readme_list,
                                      self.__dir_path)
        self.css_report = CSSReport(self.__readme_list,
                                    self.__dir_path)

        # run each report
        self.prep_report()
        self.general_report.generate_report()
        self.html_report.generate_report()
        # self.css_report.generate_report(self.html_report.html_files)

        # send linked stylesheets to css report
        self.css_report.linked_stylesheets = self.html_report.linked_stylesheets
        
        # Get CSS validation and send to css report
        try:
            css_validation_results = self.html_report.validator_errors["CSS"]
        except:
            css_validation_results = {}
        self.css_report.set_css_validation(css_validation_results)
        self.css_report.generate_report(self.html_report.html_files)

    def prep_report(self):
        # Create a report HTML file in the report folder
        report_template_content = clerk.file_to_string(report_template_path)
        with open('report/report.html', 'w') as f:
            f.write(report_template_content)


class GeneralReport:
    def __init__(self, readme_list, dir_path):
        self.__dir_path = dir_path
        self.title = ""
        self.description = ""
        self.paragraphs = []
        self.sentences = []
        self.word_count = 0
        self.__readme_list = readme_list
        self.num_html_files = 0
        self.num_css_files = 0
        self.words_per_sentence = 0.0
        self.sentences_per_paragraph = 0.0
        self.report_details = {
            "min_number_files": {
                "HTML": None,
                "CSS": None
            },
            "num_files_results": {
                "Meets HTML": False,
                "Meets CSS": False
            },
            "writing_goals": {
                "average_SPP": [1, 5],
                "average_WPS": [10, 20],
            },
            "writing_goal_results": {
                "actual_SPP": 0,
                "meets_SPP": False,
                "actual_WPS": 0,
                "meets_WPS": False,
            }
        }

    def generate_report(self):
        self.set_title()
        self.set_description()
        self.set_paragraphs()
        self.set_sentences()
        self.set_word_count()
        self.set_min_number_files()
        self.analyze_results()
        self.publish_results()

    def get_report_details(self):
        return self.report_details

    def set_title(self):
        # extract title from the readme text (str)
        for i in self.__readme_list:
            if "Project Name:" in i:
                self.title = i
                break
        row_list = re.split(":", self.title)
        self.title = row_list[1].strip()

    def get_title(self):
        return self.title

    def set_description(self):
        # extract description from the readme text
        for i in self.__readme_list:
            if "***GOAL***" in i:
                self.description = i
                break
        row_list = re.split(":", self.description)
        self.description = row_list[1].strip()

    def get_description(self):
        return self.description

    def set_min_number_files(self):
        min_html_files = 0
        min_css_files = 0
        for row in self.__readme_list:
            if "* [HTML]" in row:
                num = re.search(r'[0-9]+', row)
                if num:
                    min_html_files = num.group(0)
            if "* [CSS]" in row:
                num = re.search(r'[0-9]+', row)
                if num:
                    min_css_files = num.group(0)

        self.report_details["min_number_files"]["HTML"] = int(min_html_files)
        self.report_details["min_number_files"]["CSS"] = int(min_css_files)

    def get_min_number_files(self, filetype):
        """ receives filetype and returns minimum # of that file"""
        if filetype.lower() == "html":
            return self.report_details["min_number_files"]["HTML"]
        elif filetype.lower() == "css":
            return self.report_details["min_number_files"]["CSS"]
        else:
            return "NA"

    def set_paragraphs(self):
        html_files = clerk.get_all_files_of_type(self.__dir_path, "html")
        for file in html_files:
            if not self.paragraphs:
                self.paragraphs = list(html.get_elements("p", file))
            else:
                try:
                    # get list of any p elements
                    paragraphs = html.get_elements("p", file)
                    # then loop through and append each
                    for p in enumerate(paragraphs):
                        self.paragraphs.append(p[1])
                except:
                    print("We have a problem")

    def get_paragraphs(self):
        return self.paragraphs

    def set_word_count(self):
        for p in self.paragraphs:
            self.word_count += self.get_num_words(p)

    def get_word_count(self):
        return self.word_count

    def get_num_words(self, element):
        # Get words from element
        words = html.get_element_content(element)

        # Get a word count
        word_list = words.split()
        return len(word_list)

    def set_sentences(self):
        sentence_list = self.paragraphs
        paragraphs = ""
        for i in enumerate(sentence_list):
            p = clerk.remove_tags(str(i[1]))
            p = p.strip()
            paragraphs += p
        self.sentences = clerk.split_into_sentences(paragraphs)

    def get_num_sentences(self):
        return len(self.sentences)

    def meets_num_html_files(self):
        # compare actual number of files to min
        # number of files.
        self.num_html_files = len(
            clerk.get_all_files_of_type(self.__dir_path, "html"))
        min_required = self.report_details["min_number_files"]["HTML"]
        self.report_details["num_files_results"]["Meets HTML"] = self.num_html_files >= min_required

    def meets_num_css_files(self):
        self.num_css_files = len(
            clerk.get_all_files_of_type(self.__dir_path, "css"))
        min_required = self.report_details["min_number_files"]["CSS"]
        self.report_details["num_files_results"]["Meets CSS"] = self.num_css_files >= min_required

    def analyze_results(self):
        # Does it meet min file requirements?
        self.meets_num_html_files()
        self.meets_num_css_files()

        # calculate WPS and SPP
        try:
            SPP = len(self.sentences) / len(self.paragraphs)
        except ZeroDivisionError:
            SPP = 0
        self.report_details["writing_goal_results"]["actual_SPP"] = SPP

        # Is SPP within range?
        minSPP, maxSPP = self.report_details["writing_goals"]["average_SPP"]
        self.report_details["writing_goal_results"]["meets_SPP"] = SPP > minSPP and SPP < maxSPP

        # calculate words per sentence WPS
        try:
            WPS = self.word_count / self.get_num_sentences()
        except ZeroDivisionError:
            WPS = 0
        self.report_details["writing_goal_results"]["actual_WPS"] = WPS

        # Is WPS within range?
        min_wps, max_wps = self.report_details["writing_goals"]["average_WPS"]
        self.report_details["writing_goal_results"]["meets_WPS"] = WPS > min_wps and WPS < max_wps

    def publish_results(self):
        # Get report
        report_content = html.get_html(report_path)
        # report_content = report_template

        goals_details = self.report_details["min_number_files"]
        goals_results = self.report_details["num_files_results"]
        writing_goals = self.report_details["writing_goals"]
        writing_results = self.report_details["writing_goal_results"]

        # Modify table in section#general

        # Append the following tds
        # Min HTML files & Actual HTML files
        # Report.get_report_results_string()
        html_results_string = Report.get_report_results_string(
            "general-html-files-results", "HTML", goals_details['HTML'], self.num_html_files, goals_results['Meets HTML'])
        html_results_tag = BeautifulSoup(html_results_string, "html.parser")
        report_content.find(
            id="general-html-files-results").replace_with(html_results_tag)

        # Min CSS files & Actual CSS files
        css_results_string = Report.get_report_results_string(
            "general-css-files-results", "CSS",  
            goals_details['CSS'], self.num_css_files, 
            goals_results['Meets CSS'])

        css_results_tag = BeautifulSoup(css_results_string, "html.parser")
        report_content.find(
            id="general-css-files-results").replace_with(css_results_tag)

        spp_results_string = Report.get_report_results_string("general-spp-results", 
            "Avg. Sentences / Paragraph", str(writing_goals["average_SPP"]), 
            writing_results["actual_SPP"], writing_results["meets_SPP"])
        
        spp_results_tag = BeautifulSoup(spp_results_string, "html.parser")
        report_content.find(
            id="general-spp-results").replace_with(spp_results_tag)

        wps_results_string = Report.get_report_results_string("general-wps-results", "Avg. Words / Sentence", str(
            writing_goals["average_WPS"]), writing_results["actual_WPS"], writing_results["meets_WPS"])
        wps_results_tag = BeautifulSoup(wps_results_string, "html.parser")
        report_content.find(
            id="general-wps-results").replace_with(wps_results_tag)

        # Save new HTML as report/general_report.html
        with open(report_path, 'w') as f:
            f.write(str(report_content.contents[2]))


class HTMLReport:
    def __init__(self, readme_list, dir_path):
        self.__dir_path = dir_path
        self.html_level = "0"
        self.__readme_list = readme_list
        self.html_requirements_list = []
        self.html_files = []
        self.linked_stylesheets = {}
        self.style_tags = []
        self.validator_errors = { 
                                 "HTML": {},
                                 "CSS": {}
                                 }
        self.validator_warnings = {
                                 "HTML": {},
                                 "CSS": {}
                                 }
        self.report_details = {
            "html_level": "",
            "can_attain_level": False,
            "html_level_attained": None,
            "validator_goals": 0,
            "uses_inline_styles": False,
            "validator_results": {
                "CSS Errors": 0,
                "HTML Errors": 0
            },
            "num_html_files": 0,
            "required_elements": {
                "HTML5_essential_elements": {
                    "DOCTYPE": 1,
                    "HTML": 1,
                    "HEAD": 1,
                    "TITLE": 1,
                    "BODY": 1
                },
            },
            "required_elements_found": {
                "HTML5_essential_elements_found": {},
            },
            "meets_required_elements": {
                "meets_HTML5_essential_elements": False,
                "meets_other_essential_elements": False},
            "meets_requirements": False
        }

    def generate_report(self):
        self.get_html_files_list()
        self.get_html_requirements_list()
        self.get_html_level()
        self.get_validator_goals()
        self.ammend_required_elements()
        self.set_linked_stylesheets()
        self.analyze_results()
        self.publish_results()

    def get_html_files_list(self):
        self.html_files = clerk.get_all_files_of_type(self.__dir_path, "html")
        return self.html_files

    def get_required_elements(self):
        # get a list of all required elements: the keys
        required_elements = []
        for element in enumerate(self.report_details["required_elements"].keys()):
            if element[1] == "HTML5_essential_elements":
                for nested_el in enumerate(self.report_details["required_elements"]["HTML5_essential_elements"].keys()):
                    required_elements.append(nested_el[1])
            else:
                required_elements.append(element[1])
        return required_elements

    def get_validator_goals(self):
        """ gets number of validator errors allowed """
        readme_list = self.html_requirements_list[:]
        # Looking for Allowable Errors
        for line in readme_list:
            if "* Allowable Errors" in line:
                allowable_errors = re.search("[0-9]", line).group()
                self.report_details["validator_goals"] = int(allowable_errors)
                return int(allowable_errors)
            else:
                continue
        return 0

    def set_required_elements_found(self):
        # get a copy of the required elements
        required_elements = self.get_required_elements().copy()

        # remove the HTML5_essential_elements
        # that was already covered
        html_essential_elements = ["DOCTYPE", "HTML", "HEAD", "TITLE", "BODY"]
        for i in html_essential_elements:
            required_elements.remove(i)

        # iterate through each element and get the total number
        # then compare to required number
        for el in required_elements:
            actual_number = html.get_num_elements_in_folder(
                el, self.__dir_path)

            # get how many of that element is required
            number_required = self.report_details['required_elements'][el]

            # do we have enough of that element to meet?
            el_meets = actual_number >= number_required

            # modify the report details on required elements found
            self.report_details["required_elements_found"][el] = [
                number_required, actual_number, el_meets]

    def set_html5_required_elements_found(self):
        # Get HTML5_essential_elements
        html5_elements = self.report_details["required_elements"]["HTML5_essential_elements"].copy(
        )
        # get # of html files in folder - this is our multiplier
        for el in enumerate(html5_elements):
            element = el[1].lower()
            # how many were found
            number_found = html.get_num_elements_in_folder(
                element, self.__dir_path)
            number_required = self.report_details['required_elements']['HTML5_essential_elements'][element.upper(
            )]
            element_meets = number_found >= number_required

            self.report_details["required_elements_found"]["HTML5_essential_elements_found"][element.upper(
            )] = [number_required, number_found, element_meets]

    def meets_required_elements(self):
        all_elements_meet = True  # assume they meet until proved otherwise
        # Get all essential_elements
        html5_elements = self.report_details["required_elements"].copy(
        )
        html5_elements.pop('HTML5_essential_elements', None)
        # remove essential HTML5 elements
        print(html5_elements)
        # check all other tags to see if they meet - record whether each one meets individually
        for i in enumerate(html5_elements.items()):
            all_elements_meet = True
            key, min_value = i[1]
            actual_value = html.get_num_elements_in_folder(
                key, self.__dir_path)
            element_meets = actual_value >= min_value
            if not element_meets:
                all_elements_meet = False  # it just takes one not meeting
        return all_elements_meet

    def check_element_for_required_number(self, file_path, element, min_num):
        num_elements = html.get_num_elements_in_file(element, file_path)
        return num_elements >= min_num

    def get_html_requirements_list(self):
        h_req_list = []
        # create a flag to switch On when in the HTML section and off
        # when that section is over (### CSS)
        correct_section = False
        for row in enumerate(self.__readme_list):
            # 1st row in the section should be ### HTML
            if row[1] == "### HTML":
                # it's the beginning of the correct section
                correct_section = True
            if row[1] == "### CSS":
                break
            if correct_section:
                h_req_list.append(row[1])

        self.html_requirements_list = h_req_list
        return self.html_requirements_list

    def get_html_level(self):
        # extract HTML level from readme_list
        for i in self.__readme_list:
            if "### HTML Level" in i:
                self.report_details["html_level"] = i
                break
        row_list = re.split("=", self.report_details["html_level"])
        self.report_details["html_level"] = row_list[1].strip()
        self.html_level = self.report_details["html_level"]
        return self.report_details["html_level"]

    def get_num_html_files(self):
        html_files = clerk.get_all_files_of_type(self.__dir_path, "html")
        return len(html_files)

    def can_attain_level(self):
        # Determine whether or not this project is enough
        # to qualify to meet the level
        description = ""
        for i in range(len(self.__readme_list)):
            row = self.__readme_list[i]
            if "### HTML Level" in row:
                # set description to next row (after the header)
                description = self.__readme_list[i+1]
                break
        self.report_details["can_attain_level"] = "does meet" in description
        return "does meet" in description

    def ammend_required_elements(self):
        """ adds remaining required HTML elements """
        # extract all elements and their minimum #
        # using a regex to capture the pattern: `EL` : ##
        ptrn = r"((`(.*)`\s*):(\s*\d*))"
        for i in self.html_requirements_list:
            if "`DOCTYPE`" in i:
                # skip the row with required HTML 5 elements
                continue
            match = re.search(ptrn, i)
            if match:
                key, val = match.group(2, 4)
                key = key.strip()[1:-1]
                # add key and value to required elements
                self.report_details["required_elements"][key] = int(val)

    def get_report_details(self):
        return self.report_details

    def validate_html(self):
        # create a dictionary with doc titles for keys
        # and num of errors for value

        # get titles and run them through validator
        for file_path in self.html_files:
            # Get error objects
            errors_in_file = val.get_markup_validity(file_path)
            # Get number of errors
            num_errors = len(errors_in_file)
            page_name = clerk.get_file_name(file_path)
            if num_errors > 0:
                self.process_errors(page_name, errors_in_file)

    def process_errors(self, page_name, errors):
        """ receives errors and records warnings and errors """
        errors_dict = {"HTML": {},
                       "CSS": {}}
        warnings_dict = {"HTML": {},
                         "CSS": {}}

        # Loop through all the errors and separate
        # error from warning and CSS from HTML
        # Must use try/except whenever adding an item
        # because it will crash if we try and append it
        # to a non-existant list
        for item in errors:
            if item["type"] == "error":
                if "CSS" in item["message"]:
                    self.report_details["validator_results"]["CSS Errors"] += 1
                    try:
                        errors_dict["CSS"][page_name].append(item)
                    except:
                        errors_dict["CSS"][page_name] = [item, ]
                else:
                    self.report_details["validator_results"]["HTML Errors"] += 1
                    try:
                        errors_dict["HTML"][page_name].append(item)
                    except:
                        errors_dict["HTML"][page_name] = [item, ]
            elif item["type"] == "info":
                if "CSS" in item["message"]:
                    try:
                        warnings_dict["CSS"][page_name].append(item)
                    except:
                        warnings_dict["CSS"][page_name] = [item, ]
                else:
                    try:
                        warnings_dict["HTML"][page_name].append(item)
                    except:
                        warnings_dict["HTML"][page_name] = [item, ]
            elif item["type"] == 'alert':
                try:
                    warnings_dict["HTML"][page_name].append(item)
                except:
                    warnings_dict["HTML"][page_name] = [item, ]

        self.augment_errors(errors_dict) # we might need to change to a function
        self.add_warnings(warnings_dict)

    def augment_errors(self, new_dict):
        """ appends any errors from a dict to validator errors """
        for page, errors in new_dict['HTML'].items():
            self.validator_errors['HTML'][page] = errors
    
    def add_warnings(self, warnings):
        for page, warning in warnings['HTML'].items():
            self.validator_warnings['HTML'][page] = warning

    def add_errors(self, errors):
        for page, error in errors['HTML'].items():
            self.validator_errors[page] = error

    def analyze_results(self):
        self.can_attain_level()
        self.validate_html()
        self.set_html5_required_elements_found()
        self.set_required_elements_found()
        self.meets_required_elements()
        self.meets_html5_essential_requirements()
        self.check_for_inline_styles()

    def publish_results(self):
        # Get report
        report_content = html.get_html(report_path)

        # HTML Overview Table
        html_overview_tr = self.get_html_overview_row()
        report_content.find(id="html-overview").replace_with(html_overview_tr)

        # Validation Report
        # HTML Validation
        # get the results of the validation as a string
        validation_results_string = self.get_validation_results_string('HTML')

        # create our tbody contents
        tbody_contents = BeautifulSoup(
            validation_results_string, "html.parser")
        tbody_id = 'html-validation'
        report_content.find(id=tbody_id).replace_with(tbody_contents)

        # CSS Validation
        # get the results of the validation as a string
        validation_results_string = self.get_validation_results_string('CSS')

        # create our tbody contents
        tbody_contents = BeautifulSoup(
            validation_results_string, "html.parser")
        tbody_id = 'css-validation'
        report_content.find(id=tbody_id).replace_with(tbody_contents)

        # Generate Error report
        # For HTML Errors
        error_report_contents = self.get_validator_error_report()
        tbody_contents = BeautifulSoup(error_report_contents, "html.parser")
        tr_id = "html-validator-errors"
        report_content.find(id=tr_id).replace_with(tbody_contents)

        # For CSS Errors
        error_report_contents = self.get_validator_error_report('CSS')
        tbody_contents = BeautifulSoup(error_report_contents, "html.parser")
        tr_id = "css-validator-errors"
        report_content.find(id=tr_id).replace_with(tbody_contents)

        html_goals_results = list(
            self.report_details["required_elements_found"].items())
        html5_goals_results = list(html_goals_results.pop(0)[1].items())

        html_elements_results_string = ""
        # we have to modify an entire tbody (not just a tr)
        tbody_id = "html-elements-results"
        for el in html5_goals_results:
            # get element, goal, actual, and results
            element = el[0]
            goal = el[1][0]
            actual = el[1][1]
            results = str(el[1][2])
            html_elements_results_string += Report.get_report_results_string(
                "", element, goal, actual, results)
        # add remaining elements
        for el in html_goals_results:
            # get element, goal, actual, and results
            element = el[0]
            goal = el[1][0]
            actual = el[1][1]
            results = el[1][2]
            html_elements_results_string += Report.get_report_results_string(
                "", element, goal, actual, results)
        ######
        ######
        # create our tbody contents
        tbody_contents = BeautifulSoup(
            html_elements_results_string, "html.parser")
        report_content.find(id=tbody_id).replace_with(tbody_contents)

        # Save new HTML as report/report.html
        with open(report_path, 'w') as f:
            f.write(str(report_content.contents[0]))

    def get_html_overview_row(self):
        # get a string version of can_attain_level
        can_attain = str(self.can_attain_level())
        html_overview_string = Report.get_report_results_string(
            "html-overview", self.html_level, can_attain, "", "")
        overview_row = BeautifulSoup(html_overview_string, "html.parser")
        return overview_row

    def get_validation_results_string(self, validation_type="HTML"):
        results = ""
        if not self.validator_errors:
            return '<tr><td rowspan="4">Congratulations! No Errors Found</td></tr>'
        else:
            try:
                validation_report = self.validator_errors[validation_type].copy()
            except:
                print("Whoah Nelly")
            cumulative_errors = 0
            for page, errors in validation_report.items():
                num_errors = len(errors)
                error_str = str(num_errors) + " error"
                if num_errors != 1:
                    error_str += 's'
                cumulative_errors += num_errors
                cumulative_errors_string = str(
                    cumulative_errors) + " total errors"
                meets = str(cumulative_errors <=
                            self.report_details["validator_goals"])
                results += Report.get_report_results_string(
                    "", page, error_str, cumulative_errors_string, meets)
            return results

    def get_validator_error_report(self, validation_type="HTML"):
        results = ""
        if not self.validator_errors:
            # write 1 column entry indicating there are no errors
            congrats = "Congratulations, no errors were found."
            results = '<tr><td colspan="4">' + congrats + '</td></tr>'
            return results
        else:
            errors_dict = self.validator_errors[validation_type]
            tr_class = "html-validator-errors"

            for page, errors in errors_dict.items():
                for error in errors:
                    message = error['message']

                    # clean message of smart quotes for HTML rendering
                    message = message.replace('“', '"').replace('”', '"')
                    last_line = error['lastLine']
                    try:
                        first_line = error['firstLine']
                    except:
                        first_line = last_line
                    last_column = error['lastColumn']
                    try:
                        first_column = error['firstColumn']
                    except:
                        first_column = last_column
                    # render any HTML code viewable on the screen
                    extract = error['extract'].replace(
                        "<", "&lt;").replace(">", "&gt;")

                    # place extract inside of a code tag
                    extract = "<code>" + extract + "</code>"

                    location = 'From line {}, column {}; to line {}, column {}.'.format(first_line,
                                                                                        first_column, last_line, last_column)

                    new_row = Report.get_report_results_string(
                        tr_class, page, message, location, extract)
                    new_row = new_row.replace("Meets", extract)
                    results += new_row
        return results

    def extract_el_from_dict_key_tuple(self, the_dict):
        """ converts all keys from a tuple to 2nd item in tuple """
        new_dict = {}
        for t, i in the_dict.items():
            new_dict[t[1]] = i
        return new_dict

    def meets_html5_essential_requirements(self):
        required_elements = self.report_details["required_elements_found"]["HTML5_essential_elements_found"]
        for element in required_elements.values():
            if element[-1] == False:
                return False
        return True

    def set_linked_stylesheets(self):
        """ will generate a list of HTML docs and the CSS they link to """
        linked = {}
        # loop through html_files
        # in each file get the href of any link if that href matches a file in the folder
        for file in self.html_files:
            contents = clerk.file_to_string(file)
            link_hrefs = clerk.get_linked_css(contents)
            filename = clerk.get_file_name(file)
            linked[filename] = link_hrefs
        self.linked_stylesheets = linked

    def check_for_inline_styles(self):
        files_with_inline_styles = []
        for file in self.html_files:
            markup = clerk.file_to_string(file)
            has_inline_styles = html.uses_inline_styles(markup)
            if has_inline_styles:
                filename = clerk.get_file_name(file)
                files_with_inline_styles.append(filename)

        self.report_details["uses_inline_styles"] = files_with_inline_styles

class CSSReport:
    def __init__(self, readme_list, dir_path):
        self.__dir_path = dir_path
        self.html_level = "0"
        self.readme_list = readme_list
        self.html_files = []
        self.project_css_by_html_file = {}
        self.font_families_used = []
        self.min_num_css_files = 0
        self.max_num_css_files = 0
        self.css_errors = {}
        self.css_files = []
        self.style_tag_contents = []
        self.num_style_tags = 0
        self.linked_stylesheets = {}
        self.pages_contain_same_css_files = False
        self.repeat_selectors = {}
        self.repeat_declarations_blocks = {}
        self.set_readme_list()
        self.stylesheet_objects = []
        self.report_details = {
            "css_level": "",
            "css_level_attained": False,
            "css_validator_goals": 0,
            "css_validator_results": {},
            "num_css_files": 0,
            "style_tags": [],
            "repeat_selectors": 0,
            "repeat_declaration_blocks": 0,
            "general_styles_goals": {},
            "standard_requirements_goals": {},
            "standard_requirements_results": {},
            "project_specific_goals": {},
            "project_specific_results": {},
            "meets_requirements": False
        }

    def set_css_validation(self, css_validation_results):
        self.report_details['css_validator_results'] = css_validation_results
        self.css_errors.update(css_validation_results)
        self.report_details['css_validator_errors'] = len(
            css_validation_results)

    def generate_report(self, html_files):
        self.html_files = html_files
        self.get_project_css_by_file(html_files)
        self.get_num_css_files()
        self.get_style_tags()
        self.get_num_style_tags()
        self.get_css_code()
        self.check_pages_for_same_css_files()
        self.set_repeat_selectors()
        self.validate_css()
        self.set_repeat_declaration_blocks()
        self.get_standard_requirements()
        self.get_standard_requirements_results()
        self.get_general_styles_goals()
        self.get_general_styles_results()
        self.publish_results()
        
    def get_general_styles_goals(self):
        try:
            start = self.readme_list.index("* General Styles:") + 1
        except ValueError:
            # There's no general styles goals
            logging.warn("There's no General Styles Goals in README. Look into it.")
            return
        if "* Project-specific Requirements:" in self.readme_list:
            stop = self.readme_list.index("* Project-specific Requirements:")
        else:
            stop = len(self.readme_list)

        # take a slice in between for reqs
        requirements = self.readme_list[start:stop]
        details = {}
        for req in requirements:
            if '    * Font Families' in req:
                response = Report.get_header_details(req)
                details = response
            elif '+ minimum' in req.lower() or '+ min' in req.lower():
                min = req.split(":")[1].strip()
                details["details"]["minimum"] = min
            elif '+ maximum' in req.lower() or '+ max' in req.lower():
                max = req.split(":")[1].strip()
                details["details"]["maximum"] = max
            elif '* color settings' in req.lower():
                # If we had already gathered requirements,
                # Let's add them before clearing them out for the next round
                if details:
                    # add details to report_details
                    item = details.pop("title")
                    self.report_details["general_styles_goals"][item]=details

                    # reset details
                    details = {"Color Settings":{}}
                    
            elif '+ entire page colors set' in req.lower():
                description, title = self.get_title_and_description(req)
                details["Color Settings"][title] = description
            elif '+ headers' in req.lower():
                description, title = self.get_title_and_description(req)
                details["Color Settings"][title] = description
            elif '+ color contrast' in req.lower():
                description, title = self.get_title_and_description(req)
                details["Color Settings"][title] = {"description": description}
            elif '- normal' in req.lower():
                description, title = self.get_title_and_description(req)
                details["Color Settings"]['Color Contrast (readability)'][title] = description
            elif '- large' in req.lower():
                description, title = self.get_title_and_description(req)
                details["Color Settings"]['Color Contrast (readability)'][title] = description
        
        self.report_details["general_styles_goals"]["Color Settings"]=details["Color Settings"]

    def get_title_and_description(self, req):
        full_details = req.split(": ")
        title = full_details[0].strip()[2:]
        description = full_details[1].strip()
        return description,title

    def get_general_styles_results(self):
        results = {}
        goals = list(self.report_details['general_styles_goals'].items())
        for goal, details in goals:
            if goal == "Font Families":
                # get actual # of font families and compare to range (min max)
                font_families = self.get_font_families()
                font_count = self.get_font_count(font_families)
                min = int(details['details']['minimum'])
                max = int(details['details']['maximum'])
                meets = font_count >= min and font_count <= max
                self.report_details['general_styles_goals']['Font Families']['details']['actual']=str(font_count)
                self.report_details['general_styles_goals']['Font Families']['details']['meets']=meets
            elif goal == "Color Settings":
                color_rulesets = self.get_color_data()
                passes_page_colors = self.meets_page_colors(details)
                print(passes_page_colors)

    def get_color_data(self):
        """ Initialize background & foreground to white & black
            Get background & foreground colors for:
            * global styles
            * headers
            * anchors (default is blue and purple for hover)
            * any other selectors
            If any declarations leave out color or background-color, use the global setting
            
            NOTE: we will NOT worry about the context (like applying inheritance of an li from ul). That's beyond my paygrade
        """
        color_data = self.set_color_data_defaults()
        print(color_data)
        # TODO:
        # get all properties, values, specificity, cascade
        print("Here we go")

    def set_color_data_defaults(self):
        default_colors = {"color": "#000000",
                       "background": "#ffffff"}
        general_data = {
                       "specificity": 1,
                       "colors": {},
                       "contrast": ""}
        global_colors = {"name": "global",
                         "selector": "body"}
        anchor_defaults = {"color": "#0000ff",
                           "background": "#ffffff"}
        color_data = {
            "global": {},
            "headers": {},
            "anchors": {},
            "others": {}
        }
        general_data["colors"] = default_colors
        color_data["global"] = general_data.copy()
        color_data["headers"] = general_data.copy()
        color_data["anchors"] = general_data.copy()
        color_data["anchors"]["colors"] = anchor_defaults
        return color_data

    def meets_page_colors(self, goals):
        meets = False
        try:
            if goals['Entire Page colors set'] == "background and foreground":
                for sheet in self.style_tag_contents:
                    if sheet.color_rulesets:
                        if self.are_background_and_foreground_set(sheet):
                            return True
                for sheet in self.stylesheet_objects:
                    if sheet.color_rulesets:
                        if self.are_background_and_foreground_set(sheet):
                            return True
            return meets
        except:
            print("We have an exception most likely with the key for goals.")
            return False
           
    def are_background_and_foreground_set(self, sheet):
        for rule in sheet.color_rulesets:
            if rule.selector in ('body', 'html'):
                if "background-color:" in rule.declaration_block.text and rule.declaration_block.text.count("color") > 1:
                            # both are set
                    print(rule.declaration_block.text)
                    return True
    
    def get_font_count(self, font_families):
        # Make sure there are no duplicates
        for font in font_families:
            num = font_families.count(font)
            if num > 1:
                font_families.pop(font)
        return len(font_families)

    def get_font_families(self):
        font_families = []
        rulesets = []
        for declaration in self.style_tag_contents:
            families = self.get_families(declaration)
            if families:
                for fam in families:
                    font_families.append(fam)
        for declaration in self.stylesheet_objects:
            families = self.get_families(declaration)
            if families:
                for fam in families:
                    font_families.append(fam)
        return font_families

    def get_families(self, declaration):
        families = []
        for ruleset in declaration.rulesets:
            for declaration in ruleset.declaration_block.declarations:
                if declaration.property in ("font", "font-family"):
                    families.append(declaration.value)
        return families

    def get_standard_requirements(self):
        # get index position of Standard Req and General Styles headers
        try:
            start = self.readme_list.index("* Standard Requirements:") + 1
        except ValueError:
            # there's no Standard Requirements
            logging.warn("There's no Standard Requirements in README? Is that intentional? Typo?")
            return
        if "* General Styles:" in self.readme_list:
            stop = self.readme_list.index("* General Styles:")
        elif "* Project-specific Requirements:" in self.readme_list:
            stop = self.readme_list.index("* Project-specific Requirements:")
        else:
            stop = len(self.readme_list)
        # take a slice in between for reqs
        requirements = self.readme_list[start:stop]

        # get each req and put into standard reqs dictionary
        for req in requirements:
            req = req.strip()
            split_req = req.split(":", 1)
            description = split_req[0][2:]
            goal_raw = split_req[1]
            min = 0
            if '0' in goal_raw or 'None' in goal_raw:
                max = 0
            else:
                max = re.findall(r'\d+', split_req[1])
                max = int(max[0])

            # add requirements to dictionary
            self.report_details['standard_requirements_goals'][description]={"min": min, "max": max}

    def get_standard_requirements_results(self):
        errors = self.get_css_errors()
        self.get_standard_requirements_results_by_key(errors, "CSS Errors")

        repeats = len(list(self.repeat_selectors.keys()))
        self.get_standard_requirements_results_by_key(repeats, "Repeat selectors")
         
        repeats = len(list(self.repeat_declarations_blocks.keys()))
        self.get_standard_requirements_results_by_key(repeats, "Repeat declaration blocks")
   
    def get_standard_requirements_results_by_key(self, results, key):
        range = self.report_details["standard_requirements_goals"][key]
        min = range["min"]
        max = range["max"]
        passed = results >= min and results <= max
        if passed:
            results = "Passed"
        else:
            results = "Failed"
        
        self.report_details["standard_requirements_results"][key] = results

    def get_css_errors(self):
        number = 0
        for errors in self.css_errors.values():
            if errors != "No errors":
                number += len(errors)
        return number

    def set_repeat_selectors(self):
        all_selectors = []
        # get the names of all linked stylesheets
        linked_stylesheets = self.get_linked_stylesheets()
        filenames = self.get_filenames_from_paths(linked_stylesheets)
        implemented_selectors = self.get_implemented_selectors(all_selectors, filenames)
        # sort then get repeated selectors (if any)
        all_selectors.sort()
        self.get_repeated_selectors(all_selectors, implemented_selectors)

    def get_repeated_selectors(self, all_selectors, implemented_selectors):
        for selector in all_selectors:
            count = all_selectors.count(selector)
            if count > 1:
                # get the stylesheets that "own" the selector
                for page in implemented_selectors.keys():
                    if selector in implemented_selectors[page]:
                        pages = self.repeat_selectors.get(selector)
                        if not pages:
                            self.repeat_selectors[selector] = [page, ]
                        elif page not in pages:
                            self.repeat_selectors[selector].append(page) 
                        else:
                            # At this point, only append if we have not yet matched the number of pages to the count
                            if len(self.repeat_selectors[selector]) < count:    
                                self.repeat_selectors[selector].append(page)
                       
                # sort the pages
                self.repeat_selectors[selector].sort()

    def get_implemented_selectors(self, all_selectors, filenames):
        implemented_selectors = self.get_selectors_from_implemented_stylesheets(all_selectors, filenames)
        # get selectors from style_tag_contents
        self.get_selectors_from_style_tags(all_selectors, implemented_selectors)
        return implemented_selectors

    def get_selectors_from_style_tags(self, all_selectors, implemented_selectors):
        for stylesheet in self.style_tag_contents:
            for selector in stylesheet.selectors:
                all_selectors.append(selector)
                try:
                    implemented_selectors[stylesheet.href].append(selector)
                except KeyError:
                    implemented_selectors[stylesheet.href] = [selector,]

    def get_selectors_from_implemented_stylesheets(self, all_selectors, filenames):
        implemented_selectors = {}
        for stylesheet_object in self.stylesheet_objects:
            if stylesheet_object.href in filenames:
                for selector in stylesheet_object.selectors:
                    if (selector, stylesheet_object.href) not in all_selectors:
                        all_selectors.append(selector)
                        try:
                            implemented_selectors[stylesheet_object.href].append(selector)
                        except KeyError:
                            implemented_selectors[stylesheet_object.href] = [selector,]
        return implemented_selectors

    def get_filenames_from_paths(self, linked_stylesheets):
        filenames = []
        for filename in linked_stylesheets:
            filename = clerk.get_file_name(filename)
            filenames.append(filename)
        return filenames

    def set_repeat_declaration_blocks(self):
        # no repeat blocks (per page)
        # any repeat blocks from a style tag?
        declaration_blocks = self.get_all_declaration_blocks()
        # just_blocks = list(declaration_blocks.keys())
        for block, sheets in declaration_blocks.items():
            count = len(sheets)
            if count > 1:
                self.repeat_declarations_blocks[block]= sheets

    def get_all_declaration_blocks(self):
        declaration_blocks = {}
        for sheet in self.style_tag_contents:
            for ruleset in sheet.rulesets:
                declaration_block = "{" + ruleset.declaration_block.text
                source = sheet.href
                try:
                    if declaration_blocks[declaration_block]:
                        declaration_blocks[declaration_block].append(source)
                    else:
                        declaration_blocks[declaration_block] = [source, ]
                except KeyError:
                    declaration_blocks[declaration_block] = [source, ]
        for sheet in self.stylesheet_objects:
            for ruleset in sheet.rulesets:
                declaration_block = "{" + ruleset.declaration_block.text
                source = sheet.href
                try:
                    if declaration_blocks[declaration_block]:
                        declaration_blocks[declaration_block].append(source)
                    else:
                        declaration_blocks[declaration_block] = [source, ]
                except KeyError:
                    declaration_blocks[declaration_block] = [source, ]
        return declaration_blocks

    def get_linked_stylesheets(self):
        stylesheets = []
        try:
            for file, sheets in self.linked_stylesheets.items():
                for sheet in sheets:
                    if sheet not in stylesheets:
                        stylesheets.append(sheet)
        except TypeError:
            print("no stylesheet found in {}".format(file))
        return stylesheets

    def set_readme_list(self):
        readme_list = self.readme_list[:]
        for i in range(len(self.readme_list)):
            if self.readme_list[i] == "### CSS":
                break
        self.readme_list = readme_list[i:] 

    def get_project_css_by_file(self, html_files):
        # create a dictionary of files in the project 
        # each with a list of CSS applied
        file_dict = {}
        for file in html_files:
            filename = clerk.get_file_name(file)
            file_dict[filename] = []
            head_children = self.get_children(file, "head")
            styles = self.get_css_elements(head_children)
            body_children = self.get_children(file, "body")
            styles += self.get_css_elements(body_children)
            file_dict[filename] = styles
        self.project_css_by_html_file = file_dict
    
    def check_pages_for_same_css_files(self):
        if len(self.html_files) == 1:
            # Should we also check to make sure that one page is using css?
            linked_stylesheets = list(self.linked_stylesheets.values())
            for sheet in linked_stylesheets:
                if sheet:
                    return True
            return False
        files = self.extract_only_style_tags_from_css_files(self.project_css_by_html_file)
        files = list(files.values())
        self.pages_contain_same_css_files = all(file == files[0] for file in files)
        
    def extract_only_style_tags_from_css_files(self, files_with_css):
        results = {}
        for page, styles in files_with_css.items():
            results[page] = []
            for style in styles:
                if "style_tag=" not in style:
                    results[page].append(style) 
        return results

    def get_children(self, path, parent):
        code = html.get_html(path)
        try:
            head = code.find(parent)
            children = head.findChildren()
            return children
        except:
            return None

    def get_css_elements(self, nodes):
        styles=[]
        if not nodes:
            return styles
        for el in nodes:
            if el.name == 'link':
                if el.attrs["href"] and el.attrs['href'][-4:] == '.css':
                    styles.append(el.attrs['href'])
            if el.name == 'style':
                # append styles to file_dict
                css_string = el.string
                css_string = str(css_string)
                styles.append("style_tag=" + css_string)
        return styles

    def get_num_css_files(self):
        css_files = clerk.get_all_files_of_type(self.__dir_path, 'css')
        num_css_files = len(css_files)
        self.report_details["num_css_files"] = num_css_files
        return num_css_files

    def get_style_tags(self):
        # get HTML files
        html_files = clerk.get_all_files_of_type(self.__dir_path, 'html')
        # get the contents of any style tag in each html doc
        for file in html_files:
            style_tags = html.get_elements("style", file)
            for tag in style_tags:
                filename = os.path.basename(file)
                css_object = stylesheet(filename, tag.string)
                self.style_tag_contents.append(css_object)
            self.report_details["style_tags"].append((file, len(style_tags)))
        return self.report_details["style_tags"]
    
    def get_num_style_tags(self):
        self.num_style_tags = len(self.report_details['style_tags'])
        return self.num_style_tags

    def get_css_code(self):
        # extract content from all CSS files
        self.css_files = clerk.get_all_files_of_type(self.__dir_path, "css")
        for file in self.css_files:
            # First check to make sure the file was actually used in the project
            filename = clerk.get_file_name(file)
            is_linked = self.file_is_linked(filename)
            if not is_linked:
                continue
            try:
                css_code = clerk.get_css_from_stylesheet(file)
                
                css = stylesheet(filename, css_code)
                self.stylesheet_objects.append(css)
            except:
                print("Something went wrong with getting stylesheet objects")
    
    def file_is_linked(self, filename):
        for sheets in self.linked_stylesheets.values():
            if sheets:
                for sheet in sheets:
                    if filename in sheet:
                        return True
        return False
    
    def validate_css(self):
        # Get CSS validation on CSS files
        errors = 0
        for file_path in self.css_files:
            # Run css code through validator
            # Get code
            code = clerk.file_to_string(file_path)
            errors_in_file = val.validate_css(code)
            # Add to number of errors
            errors += len(errors_in_file)
            page_name = clerk.get_file_name(file_path)
            if errors > 0:
                self.process_errors(page_name, errors_in_file)
        # Get CSS validation from style tag
        for tag in self.style_tag_contents:
            tag_errors = val.validate_css(tag.text)
            # No need to process an error if we have none
            if "Congratulations!" in tag_errors[0].text:
                continue
            errors += len(tag_errors)
            if len(tag_errors) > 0:
                self.process_errors(tag.href, tag_errors)

        # add any errors to css_errors
        self.css_errors = self.report_details["css_validator_results"]

    def process_errors(self, page_name, errors):
        """ receives errors and records warnings and errors """
        errors_dict = {}
        warnings_dict = {}

        # Loop through all the errors and separate
        # error from warning
        # Must use try/except whenever adding an item
        # because it will crash if we try and append it
        # to a non-existant list
        for item in errors:
            # We need to grab all tr.error contents for errors
            error_rows = self.get_error_rows(item)

            # process errors
            if error_rows:
                errors_dict[page_name] = []
                for row in error_rows:
                    row_dict = self.get_results_details("error", row)
                    errors_dict[page_name].append(row_dict)
                

            # process warnings
            warning_rows = self.get_warning_rows(item)
            if warning_rows:
                warnings_dict[page_name] = []
                for row in warning_rows:
                    row_dict = self.get_results_details("warning", row)
                    warnings_dict[page_name].append(row_dict)

        if errors_dict:
            self.report_details["css_validator_results"][page_name] = errors_dict[page_name]
        else:
            self.report_details["css_validator_results"][page_name] = "No errors"
        if warnings_dict:
            self.report_details["css_validator_results"][page_name] = warnings_dict[page_name]

    def get_error_rows(self, item):
        item_string = item.contents
        item_string = "".join([str(elem) for elem in item_string])
        error_soup = BeautifulSoup(item_string, 'html.parser')
        error_rows = error_soup.find_all('tr', {'class':'error'})
        return error_rows

    def get_results_details(self, type, tag):
        details = {}
        # check for warning or error
        details[type] = type
        line_number = tag.contents[1]['title']
        details["line_number"] = line_number
        context = tag.contents[3].text
        details["context"] = context
        message = tag.contents[5].text
        message = clerk.clear_extra_text(message)
        details["error_msg"] = message
        code = tag.contents[5].find('span')
        details['extract'] = code
        return details
    
    def get_warning_rows(self, item):
        item_string = item.contents
        item_string = "".join([str(elem) for elem in item_string])
        error_soup = BeautifulSoup(item_string, 'html.parser')
        rows = error_soup.find_all('tr', {'class':'warning'})
        return rows

    def publish_results(self):
        # Get report	
        report_content = html.get_html(report_path)
        # TODO Process all the CSS info into our CSS tables
        
        # Generate Validator Reports
        general_results = ""
        specific_results = ""
        has_errors = self.has_css_errors(self.css_errors)
        if not has_errors:
            # write 1 column entry indicating there are no errors
            congrats = "Congratulations, no errors were found."
            general_results = '<tr><td colspan="4">' + congrats + '</td></tr>'
        else:
            cumulative_errors = 0
            specific_results = '<tr>'
            for page, errors in self.css_errors.items():
                # Process general results
                num_errors = len(errors) 
                cumulative_errors += num_errors
                general_results += '<tr><td>' + page + '</td>'
                general_results += '<td>' + str(num_errors) + '</td>'
                general_results += '<td>' + str(cumulative_errors) + '</td></tr>'

                # process specific results
                for error in errors:
                    # get page, message, location, and extract
                    message = error['error_msg']
                    location = error['line_number']
                    extract = error['extract'].contents[0]
                    specific_results += '<td>' + page + '</td>'
                    specific_results += '<td>' + message + '</td>'
                    specific_results += '<td>' + location + '</td>'
                    specific_results += '<td><pre>' + extract.strip() + '</pre></td></tr>'
                
        # create our tbody contents
        tbody_contents = BeautifulSoup(
            results, "html.parser")
        tbody_id = 'html-validation'
        report_content.find(id=tbody_id).replace_with(tbody_contents)
        
        # Generate Validator Errors Table
        
        # Generate CSS Goals Report 
        
        # Save new HTML as report/report.html
        with open(report_path, 'w') as f:
            f.write(str(report_content.contents[0]))
    
    def has_css_errors(self, css_errors):
        result = False
        for page, item in css_errors.items():
            if isinstance(item, list):
                for el in item:
                    if isinstance(el, dict):
                        error = el.get('error')
                        if error:
                            return True
            else:
                if item == 'error':
                    return True
        return False
    
    def get_css_validation_results(self):
        results = ""
        cumulative_errors = 0
        for page in self.report_details['css_validator_results'].values():
            if page != 'No errors':
                errors = 0
                for item in page:
                    if 'error' in item.keys():
                        errors += 1
                        
        print(errors)
        if not self.validator_errors:
            return '<tr><td rowspan="4">Congratulations! No Errors Found</td></tr>'
        else:
            try:
                validation_report = self.validator_errors[validation_type].copy()
            except:
                print("Whoah Nelly")
            cumulative_errors = 0
            for page, errors in validation_report.items():
                num_errors = len(errors)
                error_str = str(num_errors) + " error"
                if num_errors != 1:
                    error_str += 's'
                cumulative_errors += num_errors
                cumulative_errors_string = str(
                    cumulative_errors) + " total errors"
                meets = str(cumulative_errors <=
                            self.report_details["validator_goals"])
                results += Report.get_report_results_string(
                    "", page, error_str, cumulative_errors_string, meets)
            return results
if __name__ == "__main__":
    # How to run a report:
    # 1. Set the path to the folder:    path = "path/to/project/folder"
    # 2. Create a report object:        project_name = Report(path)
    # 3. Generate a report:             project_name.generate_report()
    # 4. Go to report/report.html for results

    # about_me_dnn_readme_path = "tests/test_files/projects/about_me_does_not_meet/"
    # project = Report(about_me_dnn_readme_path)
    # project.generate_report()

    # large_project_readme_path = "tests/test_files/projects/large_project/"
    # large_project = Report(large_project_readme_path)
    # large_project.generate_report()
    
    multi_meets_path = "tests/test_files/projects/multi_page_meets/"
    project = Report(multi_meets_path)
    project.generate_report()

    about_meets_path = "tests/test_files/projects/about_me/"
    project = Report(about_meets_path)
    project.generate_report()
    
    print("done")