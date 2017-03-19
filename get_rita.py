#!/usr/bin/env python

""" get_rita.py
"""

import os.path

import smart_open

import datetime
from calendar import month_name
import requests
import click

import logging
import logging.config
logging.config.fileConfig('logging.cfg')
logger = logging.getLogger('rita')


from time import clock

from post_data import POST_DATA

## Some constants needed in the request's header 
HOSTNAME = "www.transtats.bts.gov"
TRANSTAT_URL = "https://{host}/DownLoad_Table.asp?" + \
               "Table_ID=236&Has_Group=3&Is_Zipped=0"
REFERER="https://{host}/DL_SelectFields.asp?Table_ID=236"
ORIGIN="https://{host}"
USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/55.0.2883.87 Chrome/55.0.2883.87 Safari/537.36"
CONTENT_TYPE="application/x-www-form-urlencoded"


def _max_valid_date():
    ## the available data set is generally about 3 months behind, make
    ## sure that we never ask for data that is within the last 3 months
    max_date = datetime.date.today() + datetime.timedelta(days=-90)

    max_year = int(max_date.strftime('%Y'))
    max_month = int(max_date.strftime('%m'))

    return(max_year, max_month)

def _validate_year(ctx, param, year):
    max_year, _ = _max_valid_date()

    if year > max_year:
        raise click.BadParameter("You are requesting data from the future!: ({}) should be less or equal than {}".format(year, max_year))

    if year < 1987:
        raise click.BadParameter("You are requesting a year ({}), that is less than 1987 . The site doesn't have data for that!".format(year))

    return year

def _validate_month(ctx, param, month):
    max_year, max_month = _max_valid_date()

    if month not in range(1,13):
        raise click.BadParameter("The month should be specified between 1 and 12")
    return month

@click.command(short_help="Downloads a month from the BTS Airline On-Time Performance Data")
@click.option('--year', type=click.INT, help="The year to download (YYYY, and YYYY >= 1987)", callback=_validate_year)
@click.option('--month', type=click.INT, help="The month to download ([1-12])", callback=_validate_month)
@click.option('--data_path', type=click.Path(), help="The directory where the data would be stored (could be a Amazon S3 bucket)", default="/tmp")
def download_data(year, month, data_path):
    """

    Downloads a month from the BTS Airline On-Time Performance Data

    DATA_PATH could be a local file or a Amazon S3 bucket.

    The downloaded data will be compressed as a ZIP file.


    """

    logger.info("Collecting RITA for: {}/{}".format(month, year))
    logger.info("We will download the data to: {}".format(data_path))

    ## Fixing the data to POST
    ## For some weird reason, FREQUENCY is equal to the month ... (¬_¬)
    post_data = POST_DATA.format(year=year, month_name=month_name[month], month=month, frequency=month)

    ## Fixing EOLs
    post_data = post_data.replace("\n", "")

    ## Make a friendly file name
    output_file_name = os.path.join(data_path,'{0}-{1}'.format(str(month).zfill(2), year))
    zip_file_name = '{}.zip'.format(output_file_name)

    ## Create a session object, so we can keep the cookies, headers, etc. between requests
    with requests.Session() as s:
        ## Get the cookie and a good header from the server
        host = TRANSTAT_URL.format(host=HOSTNAME)
        r = s.get(host)

        ## Add info to the session's headers
        s.headers['User-Agent'] = USER_AGENT
        s.headers['Referer'] = REFERER.format(host=HOSTNAME)
        s.headers['Origin'] = ORIGIN.format(host=HOSTNAME)
        s.headers['Content-Type'] = CONTENT_TYPE

        logger.info("Sending POST to {}".format(host))

        tic = clock()
        ## We don't want to follow the redirect
        response = s.post(host, data=post_data, allow_redirects=False)

        if not response.status_code == 302:
            raise Exception("Request was not successful with responde {}".format(response.status_code))

        ## The Location of the file created for us is in the header in 'Location'
        remote_file = response.headers['Location']

        response = s.get(remote_file)

        ## Write the remote file to local disk
        with smart_open.smart_open(zip_file_name, "wb") as local_file:
            local_file.write(response.content)

        tac = clock()

        logger.info("Downloaded: {} in {} seconds".format(zip_file_name, tac-tic))


if __name__ == '__main__':
    download_data()
