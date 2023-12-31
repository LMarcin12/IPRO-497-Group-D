import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

# List of all classes, each in JSON format
class_list = {}

# Choose the subject at index i and open that webpage
def choose_subject(i):
# Second PAGE #
    #Select a Subject
    selectSubject = Select(driver.find_elements(By.NAME, 'sel_subj')[1])
    selectSubject.deselect_all()
    selectSubject.select_by_index(i)

    #Click Submit
    classSearch = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
    classSearch.click()

# Return the enrollment for the specified class
def get_data(CRN):
# THIRD PAGE #
    #Get all of the Sections
    ddTitle = driver.find_elements(By.CLASS_NAME, 'ddtitle')
    mainGroup = driver.find_element(By.XPATH, "/html/body/div[3]/table[1]/tbody")
    children = mainGroup.find_elements(By.CSS_SELECTOR, "div > table > tbody > tr > td.dddefault")
    ddDefault = driver.find_elements(By.CLASS_NAME, 'dddefault')
    
    c = driver.find_element(By.XPATH, '/html/body/div[3]/table[1]/tbody/tr[1]/th')
    #print(c.text)
    

    for p in range(len(ddTitle)):
        list = ddTitle[p].text.split(" - ") # title, CRN, (sID, cID), sNum
        #Sometimes theres an extra first element, if so, remove it
        if(len(list) == 5):
            list.pop(0)
        if(list[1] == CRN):
            #print(list)
            #print(ddTitle[p].text)
            ddTitle[p].find_element(By.CSS_SELECTOR, 'a').click()
            table = driver.find_element(By.XPATH, '/html/body/div[3]/table[1]/tbody/tr[2]/td/table/tbody')
            seats = table.find_elements(By.CSS_SELECTOR, 'tr')[1].find_elements(By.CLASS_NAME, "dddefault")
            waitlist = table.find_elements(By.CSS_SELECTOR, 'tr')[2].find_elements(By.CLASS_NAME, "dddefault")

            seatsData = {"capacity": int(seats[0].text), 
                        "actual": int(seats[1].text), 
                        "remaining":  int(seats[2].text)}
            waitlistData = { "capacity": int(waitlist[0].text), 
                            "actual": int(waitlist[1].text), 
                            "remaining":  int(waitlist[2].text)}
            
            return { 
                    'seats': seatsData,
                    'waitlist': waitlistData
                    }
        
    # If we get here that means no class was found
    return None

def get_all_data():
# THIRD PAGE #
    #Get all of the Sections
    ddTitle = driver.find_elements(By.CLASS_NAME, 'ddtitle')
    mainGroup = driver.find_element(By.XPATH, "/html/body/div[3]/table[1]/tbody")
    children = mainGroup.find_elements(By.CSS_SELECTOR, "div > table > tbody > tr > td.dddefault")
    ddDefault = driver.find_elements(By.CLASS_NAME, 'dddefault')
    
    c = driver.find_element(By.XPATH, '/html/body/div[3]/table[1]/tbody/tr[1]/th')
    #print(c.text)
    

    for p in range(len(ddTitle)):
        ddTitle = driver.find_elements(By.CLASS_NAME, 'ddtitle')
        list = ddTitle[p].text.split(" - ") # title, CRN, (sID, cID), sNum
        
        if(len(list) == 5):
            list.pop(0)
        
        ddTitle[p].find_element(By.CSS_SELECTOR, 'a').click()
        table = driver.find_element(By.XPATH, '/html/body/div[3]/table[1]/tbody/tr[2]/td/table/tbody')
        seats = table.find_elements(By.CSS_SELECTOR, 'tr')[1].find_elements(By.CLASS_NAME, "dddefault")
        waitlist = table.find_elements(By.CSS_SELECTOR, 'tr')[2].find_elements(By.CLASS_NAME, "dddefault")

        seatsData = {
            "capacity": int(seats[0].text), 
            "actual": int(seats[1].text), 
            "remaining":  int(seats[2].text)
            }
        waitlistData = {
            "capacity": int(waitlist[0].text), 
            "actual": int(waitlist[1].text), 
            "remaining":  int(waitlist[2].text)
            }
        
        class_list[list[1]] = {"seats": seatsData, "waitlist": waitlistData}
        returnToPrev = driver.find_element(By.XPATH, '/html/body/div[3]/table[2]/tbody/tr/td/a')
        returnToPrev.click()

    returnToPrev = driver.find_element(By.XPATH, '/html/body/div[3]/table[2]/tbody/tr/td/a')
    returnToPrev.click()

def updateEnrollment(lID, CRN): #Subject, CRN
    #Open Chrome
    driver.get("https://ssb.iit.edu/bnrprd/bwckschd.p_disp_dyn_sched") 

        # FIRST PAGE #
    #Select the term of classes
    searchForTerm = Select(driver.find_element(By.NAME, 'p_term'))
    searchForTerm.select_by_index(3) #Third Term In the Dropdown

    #Click Submit
    submit = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
    submit.click()

    #Find the dropdown
    select = driver.find_elements(By.NAME, 'sel_subj')[1]

    #Look through all of the elements in the dropdown (every subject)
    for i in range (len(select.find_elements(By.CSS_SELECTOR, 'option'))):
        if(driver.find_elements(By.NAME, 'sel_subj')[1].text.split("\n")[i] == lID):
            choose_subject(i)
            data = get_data(CRN)

            if data is not None:
                return data
            
def getAllEnrollement(semester):
    #Open Chrome
    driver.get("https://ssb.iit.edu/bnrprd/bwckschd.p_disp_dyn_sched") 

        # FIRST PAGE #
    #Select the term of classes
    searchForTerm = Select(driver.find_element(By.NAME, 'p_term'))
    searchForTerm.select_by_index(3) #Third Term In the Dropdown

    #Click Submit
    submit = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
    submit.click()

    #Find the dropdown
    select = driver.find_elements(By.NAME, 'sel_subj')[1]

    #Look through all of the elements in the dropdown (every subject)
    for i in range (len(select.find_elements(By.CSS_SELECTOR, 'option'))):
        choose_subject(i)
        get_all_data()

    outputFileName = "IPRO-497-Group-D\DB Setup\data\\" + semester + "_Enrollment.json"
    with open(outputFileName, 'w') as json_file:  
        json_string = json.dump(class_list, json_file, indent = 4)
        print(json_string)
            
#    with open("IPRO-497-Group-D\DB Setup\data\\" + semester + ".json", 'r') as file:
#        classes = file.read()#
#
#    with open("IPRO-497-Group-D\DB Setup\data\subjects.json", 'r') as file:
#        subjects = file.read()
#
#    classesList = json.loads(classes)
#    subjectList = json.loads(subjects)
#
#    for i in range(len(classesList)):
#        for j in range(len(subjectList)):
#            if(subjectList[j].get('sID') == classesList[i].get('sID')):
#                lID = subjectList[j].get('lID')
#                break
#        print(lID, classesList[i].get('CRN'))
#        print(updateEnrollment(lID, classesList[i].get('CRN')))

op = webdriver.ChromeOptions()
op.add_argument('headless')
driver = webdriver.Chrome(options=op)

getAllEnrollement("Fall_2023")
#print(updateEnrollment("Chemistry", "10037"))

