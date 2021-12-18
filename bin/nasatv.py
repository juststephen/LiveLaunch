import json
import os
from os.path import isfile
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread

class NASATV:
    """
    Retrieve and store NASA TV streams on YouTube.

    Notes
    -----
    Use the `.update()` method to try to find new streams.
    """
    def __init__(self):
        # NASA TV
        self._nasatv_file = 'LiveLaunch_NASATV.json'
        self._nasatv_url = 'https://www.nasa.gov/multimedia/nasatv/index.html'

    def __contains__(self, url: str) -> bool:
        """
        Checks of the given url string is contained in the `.nasatv` list.

        Parameters
        ----------
        url : str
            The url to check.

        Returns
        -------
        bool
            Whether the given url is a NASA TV YouTube stream.
        """
        return url in self.nasatv

    def _defaultNASAlive(self) -> None:
        """
        Reads the `._nasatv_file` json file and sets the `.nasatv` variable.

        Notes
        -----
        Stores the NASA TV YouTube stream URLs into the `.nasatv` variable.
        """
        # Default NASA TV URLs
        nasatv_default = ['https://www.youtube.com/watch?v=21X5lGlDOfg', \
                          'https://www.youtube.com/watch?v=nA9UZF-SZoQ']
        # Open self._nasatv_file json to find previously found NASA TV URLs
        if isfile(self._nasatv_file):
            with open(self._nasatv_file, 'r', encoding='utf-8') as f:
                f = json.load(f)
            try:
                self.nasatv = f['nasatv']
            except:
                self.nasatv = nasatv_default
        # If self._nasatv_file json doesn't exist, create one with the defaults
        else:
            self.nasatv = nasatv_default
            with open(self._nasatv_file, 'w', encoding='utf-8') as f:
                json.dump({'nasatv': self.nasatv}, f, indent=2)

    def _findNASAlive(self) -> None:
        """
        finds the permanent NASA TV livestreams and stores it using webpage scraping.
        Stores found URLs in a list at `.nasatv` and in the `._nasatv_file` json file.

        Notes
        -----
        Stores the NASA TV YouTube stream URLs into the `.nasatv` variable.
        """
        # Finds href by using the link text.
        get_href = lambda text: element.find_element(By.LINK_TEXT, text).get_property('href')
        # Check wether this is running in Windows (64bit) or Linux (64bit)
        if os.name == 'nt':
            extension = '.exe'
        else:
            extension = ''
        # Render NASA page to get URLs
        options = Options()
        options.headless = True
        with Firefox(executable_path=f'{os.getcwd()}/geckodriver{extension}', options=options) as driver:
            try:
                # Opening the webpage and wait for it to render
                driver.get(self._nasatv_url)
                element = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'link-block')))
                # Getting URLs
                streams = [get_href(i) for i in ('Public-Education Channel', 'Media')]
            except:
                pass
            else:
                # Find new streams
                newstreams = [i for i in streams if i not in self.nasatv]
                # Only continue if there are new NASA TV streams
                if newstreams:
                    # Add new streams
                    self.nasatv += newstreams
                    # Store new NASA TV streams in the self._nasatv_file json
                    with open(self._nasatv_file, 'w', encoding='utf-8') as f:
                        json.dump({'nasatv': self.nasatv}, f, indent=2)
            finally:
                driver.quit()

    def update(self) -> None:
        """
        Updates the object if there are any new NASA TV streams found.
        """
        # Read json containing NASA TV streams
        self._defaultNASAlive()
        # Get NASA TV live streams in a different thread
        thread = Thread(target=self._findNASAlive)
        thread.start()