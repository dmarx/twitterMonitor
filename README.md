Webapp that monitors twitter for breaking news. Currently visible at http://52.32.156.77/

To setup an instance:

1. Add twitter OAuth credentials to connection.cfg.template and save as connection.cfg. 
2. Install dependencies. With anaconda:  
    `$ conda env create -f environment.yml`  
    `$ source activate twitter-monitor`
    
To run, simply run the following three scripts in parallel:

* app.py - The flask webapp that serves the front-end
* scraper.py - The component that actually monitors twitter for trending items
* title_daemon.py - Separate process for pulling down titls from trending URLs
