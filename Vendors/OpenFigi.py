import config, requests
import pandas as pd

class OpenFigi:

    def __init__(self):
        self.api_url = config.OPEN_FIGI_URL
        self.openfigi_key = config.OPEN_FIGI_KEY
        self.openfigi_headers = {'Content-Type': 'text/json'}

    def map_jobs(self, jobs):

        if self.openfigi_key:
            self.openfigi_headers['X-OPENFIGI-APIKEY'] = self.openfigi_key
        response = requests.post(url=self.api_url, headers=self.openfigi_headers,json=jobs)

        if response.status_code != 200:
            raise Exception('Bad response code: {}'.format(str(response.status_code)))
        return response.json()

    # # Returns dataframe where compositeFigi = Figi and exchCode == 'US' when only a Ticker is Passed
    # def get_figi_eq_cfigi(self, jobs):
    #     job_results = self.map_jobs(jobs)
    #     just_dictionaries = [d['data'][i] for d in job_results for i in range(len(job_results[0]['data']))]
    #     df_figi = pd.DataFrame.from_dict(just_dictionaries)
    #     df_figi = df_figi.loc[(df_figi['compositeFIGI'] == df_figi['figi']) & (df_figi['exchCode'] == 'US')]
    #     return (df_figi)







