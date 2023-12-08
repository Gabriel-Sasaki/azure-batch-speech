import time
import requests
from requests.models import Response
from requests.exceptions import ConnectionError
from datetime import datetime
from src.batch.models import TranscriptionResult, TranscriptionJob
import json

class SpeechClient:
    def __init__(self,
                 token: str,
                 host: str,
                 version: str,
                 log: bool = False) -> None:
        self._token = token
        self._base_url = f'https://{host}/speechtotext/v{version}/transcriptions'
        self._headers = {
            'Ocp-Apim-Subscription-Key': self._token,
            'Content-Type': 'application/json',
            'Host': f'{host}'
        }
        self._log = log

    def __create_data_transcription(self, **kwargs) -> dict:
        body = {
                    'locale': 'pt-BR',
                    'displayName': str(datetime.now()).replace(' ', '-'),
                    'contentContainerUrl': kwargs.get('content_container_url'),
                    'properties': {
                        'languageIdentification': {
                            'candidateLocales': [candidate for candidate in
                                                    kwargs['candidate_locales']
                                                    if kwargs.get('candidate_locales')]
                        },
                    },
                }

        if kwargs.get('content_urls'):
            content_urls = [content for content in kwargs['content_urls']]
            body.update({'contentUrls': content_urls})

        if kwargs.get('diarization_enabled'):
            body.get('properties', {}).update({
                'diarizationEnabled': kwargs.get('diarization_enabled'),
                'diarization': {
                    'speakers': {
                        'minCount': kwargs['diarization_speakers_min']\
                            if kwargs.get('diarization_speakers_min') else 2,
                        'maxCount': kwargs['diarization_speakers_max']\
                            if kwargs.get('diarization_speakers_max') else 2
                    }
                }
            })

        return body

    def __create_job_transcription(self, response: dict) -> TranscriptionJob:
        splitted_url = response.get('self', []).split('/')
        transcription_id = splitted_url[len(splitted_url) - 1]
        properties = response.get('properties', {})
        language_identification = response.get('languageIdentification', {})
        speakers = properties.get('speakers', {})
        return TranscriptionJob(transcription_id=transcription_id,
                                files=response.get('links', {}).get('files'),
                                diarization_enabled=properties.get('diarizationEnables'),
                                channels=properties.get('channels'),
                                candidate_locales=language_identification.get('candidateLocales'),
                                diarization_speakers_min=speakers.get('minCount'),
                                diarization_speakers_max=speakers.get('maxCount'),
                                status=response.get('status', ''),
                                created_date_time=response.get('createdDateTime', ''),
                                display_name=response.get('displayName', ''))

    def create_job_transcription(self,
                             *,
                             diarization_enabled: bool = False,
                             content_container_url: str | None = None,
                             content_urls: str | list | None = None,
                             channels: list[int] | None = None,
                             candidate_locales: list[str],
                             destination_container_url: str | None = None,
                             time_to_live: str | None = None,
                             diarization_speakers_min: int | None = None,
                             diarization_speakers_max: int | None = None) -> TranscriptionJob:
        if content_container_url and content_urls:
            raise ValueError('The \'content_container_url\' and \'content_urls\' parameters cannot '
                             'have values at the same time. Choose one of them.')
        if not (content_container_url or content_urls):
            raise ValueError('The \'content_container_url\' or \'content_urls\' parameters need '
                             'to have value.')

        data = self.__create_data_transcription(is_create=True,
                                                diarization_enabled=diarization_enabled,
                                                content_container_url=content_container_url,
                                                content_urls=content_urls,
                                                channels=channels,
                                                candidate_locales=candidate_locales,
                                                destination_container_url=destination_container_url,
                                                time_to_live=time_to_live,
                                                diarization_speakers_min=diarization_speakers_min,
                                                diarization_speakers_max=diarization_speakers_max)

        response = requests.post(url=self._base_url,
                                 data=json.dumps(data),
                                 headers=self._headers,
                                 timeout=20)
        if self._log:
            print(f'Response: {response}')
            print(f'Body: {data}')
            print(f'Headers: {self._headers}')

        self.__check_response(response)
        return self.__create_job_transcription(response.json())

    def get_job_transcription(self,
                          transcription_id: str) -> TranscriptionJob:
        get_url = f'{self._base_url}/{transcription_id}'
        response = requests.get(url=get_url, headers=self._headers, timeout=20).json()
        return self.__create_job_transcription(response)

    def get_transcription(self,
                                transcription_id: str,
                                time_to_retry: int = 20) -> TranscriptionResult:
        get_url = f'{self._base_url}/{transcription_id}'
        response = requests.get(url=get_url, headers=self._headers, timeout=20).json()
        while response.get('status') not in ['Succeeded', 'Failed']:
            response = requests.get(url=get_url, headers=self._headers, timeout=20).json()
            time.sleep(time_to_retry)
        final_transcription = response.get('links').get('files')
        response = requests.get(url=final_transcription, headers=self._headers, timeout=20).json()
        return TranscriptionResult(response)

    def __check_response(self, response: Response) -> None:
        if response.status_code not in [200, 201, 202, 203, 204]:
            raise ConnectionError(f'HTTP Error. Status Code: {response.status_code}'\
                                  f' - {response.reason}',
                                  response=response)
