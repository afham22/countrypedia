from flask import (
    Flask,
    json,
    redirect,
    url_for,
    render_template,
    request,
    jsonify,
    make_response,
)
#IMPORT EQUIRED LIBRARIES
import bs4,requests,webbrowser,docx,re,sqlite3,json,time
from selenium import webdriver

#FETCH DATA FROM DATABASE
def data(country):
    con=sqlite3.connect('World_Statistics.db')#CONNECT TO DB FILE
    c=con.cursor()
    data=c.execute('''select * from Statistics where CountryName=?''',[country.lower()]).fetchone()
    c.close()
    con.close()
    return data

#INSERT DATA INTO DATABASE
def insert(Countryname,hoState,hoGovt,capital,population,area,GDP,imageURL):
    con=sqlite3.connect('World_Statistics.db')
    c=con.cursor()
    c.execute('''insert into Statistics values(?,?,?,?,?,?,?,?)''',
    (Countryname.lower(),hoState,hoGovt,capital,population,area,GDP,imageURL))
    con.commit()
    c.close()
    con.close()

#SEARCH FOR COUNTRY IN DB AND FETCH DATA
def regularsearch(country):
    con=sqlite3.connect('World_Statistics.db')
    c=con.cursor()
    #CREATE TABLE 
    # c.execute('''create table Statistics(CountryName varchar,hoState varchar,
    # hoGovt varchar,capital varchar,population integer,Area float,GDP float,imageURL varchar,Primary Key(CountryName))''')
    check=c.execute('''select * from Statistics where CountryName=?''',[country]).fetchone()
    c.close()
    con.close()
    if check:  #IF COUNTRY IS PRESENT DISPLAY DATA
        countryInfo = data(country)
        return countryInfo

    else:#IF COUNTRY IS NOT PRESENT THEN SCRAPE THE DATA
        #WEB SCRAPPING
        try:
            URL="https://knoema.com/atlas/"+country.lower().replace(' ','-')
            res=requests.get(URL)
            res.raise_for_status
            bs=bs4.BeautifulSoup(res.text)
            Countryname=(bs.select('h1')[0].text)
            c=bs.select('.facts li')
            hoState=(c[0].text.split(':')[1])
            hoGovt=(c[1].text.split(':')[1])
            capital=(c[2].text.split(':')[1].split(' \r')[0])
            population=(c[6].text.split(':')[1].split(' ')[0])
            area=(c[7].text.split(':')[1].split(' \r')[0])
            GDP=(c[9].text.split(':')[1].split(' ')[0])
            imageURL=bs.select('img')[10].get('src')
            comicUrl="https:"+imageURL
            res = requests.get(comicUrl)
             #AFTER SCRAPPING INSERT DETAILS INTO DATABASE
            insert(Countryname,hoState,hoGovt,capital,population,area,GDP,imageURL)
             #CREATE AN IMAGE FILE THAT SAVES THE COUNTRY FLAG IMAGE
            imageFile = open(imageURL[30:], 'wb')
            for chunk in res.iter_content(100000):
                imageFile.write(chunk)
            imageFile.close()
            #CREATE A DOCUMENT THAT STORES THE DETAILS OF A COUNTRY FETCHED FROM DATABASE
            doc=docx.Document()
            doc.add_paragraph(Countryname,'Title')
            doc.add_picture(imageURL[30:],width=docx.shared.Cm(6),height=docx.shared.Cm(4))
            doc.add_paragraph('Head Of State : '+hoState)
            doc.add_paragraph('Head Of Goverment : '+hoGovt)
            doc.add_paragraph('Capital City : '+capital)
            doc.add_paragraph('Population : '+population)
            doc.add_paragraph('Area : '+area+"km2")
            doc.add_paragraph('GDP (PPP) : '+GDP+"(Billions)")
            doc.save(Countryname+'.docx')
            return(regularsearch(Countryname.lower()))
        except:
            print("Oops!! Couldn't load data")

    
batRegex = re.compile(r'(wiki|wikipedia)$',re.IGNORECASE)

def countrygetter(country):
#SELENIUM WEBDRIVER
#OPEN WIKIPEDIA AND DISPLAY COUNTRY DETAILS
    if(batRegex.search(country)):
        country=country.lower().split('wiki')[0]
        browser=webdriver.Chrome()
        browser.get('https://www.wikipedia.org/')
        elem=browser.find_element_by_id('searchInput')
        elem.send_keys(country)
        elm=browser.find_element_by_tag_name('button')
        elm.click()
        time.sleep(100)
        
    else:
        countryInfo =regularsearch(country.lower())
        return countryInfo

#FRONT END
app=Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def mainPage():
    return render_template("index.html", content="")

@app.route("/search", methods=["POST", "GET"])

def getJson():
    if request.method == "POST":
        print(request)
        req = request.get_json()
        print(req['name'])
        countryInfo = countrygetter(req['name'])
        print(countryInfo)

        res = make_response(
            json.dumps(
                {
                    "Country": countryInfo[0],
                    "HOS": countryInfo[1],
                    "HOG": countryInfo[2],
                    "Capital": countryInfo[3],
                    "Population": countryInfo[4],
                    "Area": countryInfo[5],
                    "GDP": countryInfo[6],
                    "img": countryInfo[7],
                }
            ),
            200,
        )
        print(res.data)
        return res
    return "get request"

if __name__ == "__main__":
    app.run(debug=True)