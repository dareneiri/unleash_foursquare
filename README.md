# Unleash Foursquare Swarm
Get your Foursquare Swarm check-in history in JSON or CSV and visualize a summary of your data in a micro web framework.

# Introduction
I am not aware of any repository that has been updated to get Foursquare Swarm check-in history of a user using OAuth2 (which Foursquare API now requires). I am also not anywhere of any solution that exists online where any user can pull their data through an existing web application. You can [preview how this code works right now](http://dareneiri.pythonanywhere.com/). 

This project obtains all your Foursquare Swarm check-in history and allows you to download that information in JSON or CSV for your own downstream analyses. I use Chart.js to visualize some aspects of that check-in history and implemented a heatmap using Mapbox to visualize all your check-ins on a map. 

You do not need to fork this repo to get your data -- you can [get your data now](http://dareneiri.pythonanywhere.com/). 
Many improvements can be made. Feel free to fork this repo!

# Requirements
1. I used PythonAnywhere and clicked the "Add a new web app" button [to set up the Flask environment](https://help.pythonanywhere.com/pages/Flask/) and use Python 3.6. 
2. Create a Static File such that `/downloads/` is the URL and `/home/YOUR_PYTHONANYWHERENAME/downloads/` is the Directory for your web app in PythonAnywhere. This is where .json, .csv, and .geojson files are placed. 
3. My code uses `DataFrame.transform` which is available starting in pandas 0.20.0. You should update pandas using `pip3 install --upgrade --user pandas`
4. Get your developer keys for Foursquare and Mapbox APIs. 
5. Optionally, create a task that runs daily to delete files in `/downloads`

# Summary
The process to get your Foursquare Swarm Check-in history involves the following: 
1. An API call to Foursquare via OAuth2 to authenticate user
2. Get check-in history of authenticated user
3. Save check-in history as .json and .csv to optionally download
4. The .csv file is used in pandas to generate data needed for charts
5. User can optionally view thew charts to get a visual summary of data

* I used CDNJS for Chart.js 2.7.2 and Mapbox v0.44.2
* Boostrap 4.1 is used for CSS framework and hosted locally since I made modifications

# Directory Structure
Place files hosted here into a directory called `mysite` which by default PythonAnywhere created.
* `flask_app.py` is the file that contains all the variables that need to be modified, specifically for your API keys. 

```
├── downloads
│   ├── (directory where .json, .csv, .geojson files are placed)
├── mysite
│   ├── flask_app.py
│   ├── static
│   │   ├── Chart.min.js
│   │   ├── bootstrap41.min.css
│   │   ├── cover.css
│   │   ├── ie10-viewport-bug-workaround.css
│   │   ├── preview.png
│   │   ├── preview1.png
│   │   └── styles.css
│   └── templates
│       ├── about.html
│       ├── charts.html
│       ├── index.html
│       ├── layout.html
│       ├── profile.html
│       └── test_fs.html
```

# Sample of Visualization

![preview](https://github.com/dareneiri/unleash_foursquare/blob/master/static/preview.png "preview")
![preview1](https://github.com/dareneiri/unleash_foursquare/blob/master/static/preview1.png "preview1")

