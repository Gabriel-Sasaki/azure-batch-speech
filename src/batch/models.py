from datetime import datetime
import requests
import json

class TranscriptionResult:
    def __init__(self, response: dict) -> None:
        self.transcriptions = []
        self.diarization_data = []
        self.transcriptions_data = []
        self.__fill_transcriptions(response)
        self.__fill_diarization_data()
        self.__fill_transcriptions_data()

    def __fill_transcriptions(self, response: dict) -> None:
        values = response['values'] if response.get('values') else []
        for value in values:
            self.transcriptions.append(Transcription(name=value.get('name'),
                                                     kind=value.get('kind'),
                                                     properties=value.get('properties'),
                                                     created_date_time=value.get('createdDateTime'),
                                                     links=value.get('links')))

    def __fill_diarization_data(self) -> None:
        for index, transcription in enumerate(self.transcriptions):
            if transcription.kind == 'Transcription':
                self.diarization_data.append({
                    'transcription_name': transcription.name,
                    'phrases': []
                })
                response = requests.get(transcription.content, timeout=20)
                response_dict = json.loads(response.text)
                recognized_phrases = response_dict.get('recognizedPhrases')
                for recognized_phrase in recognized_phrases:
                    phrase = recognized_phrase.get('nBest')[0]
                    confidence = phrase.get('confidence')
                    display = phrase.get('display')
                    speaker = recognized_phrase.get('speaker')
                    self.diarization_data[index-1]['phrases'].append({
                        'speaker': speaker,
                        'confidence': confidence,
                        'display': display
                    })

    def __fill_transcriptions_data(self) -> None:
        for transcription in self.transcriptions:
            if transcription.kind == 'Transcription':
                response = requests.get(transcription.content, timeout=20)
                response_dict = json.loads(response.text)
                display_text = response_dict.get('combinedRecognizedPhrases')[0].get('display')
                audio_name = response_dict.get('source')[80:90]
                transcription_data = TranscriptionData(audio_name, display_text)
                self.transcriptions_data.append(transcription_data)

    def __repr__(self) -> str:
        return str(self.transcriptions)

    def __str__(self) -> str:
        return str(self.transcriptions)

class Transcription:
    def __init__(self,
                 name: str,
                 kind: str,
                 properties: dict,
                 created_date_time: str,
                 links: dict) -> None:
        self.name = name
        self.kind = kind
        self.properties = properties
        self.created_date_time = datetime.fromisoformat(created_date_time)
        self.content = links.get('contentUrl')

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __str__(self) -> str:
        return str(self.__dict__)

class TranscriptionData:
    def __init__(self, audio_name, display_text) -> None:
        self.audio_name = audio_name
        self.display_text = display_text

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __str__(self) -> str:
        return str(self.__dict__)

class TranscriptionJob:
    def __init__(self,
                 transcription_id: str,
                 files: str,
                 diarization_enabled: bool,
                 channels: list[int],
                 candidate_locales: list[str],
                 diarization_speakers_min: int,
                 diarization_speakers_max: int,
                 status: str,
                 created_date_time: str,
                 display_name: str) -> None:
        self.transcription_id = transcription_id
        self.files = files
        self.diarization_enabled = diarization_enabled
        self.channels = channels
        self.candidate_locales = candidate_locales
        self.diarization_speakers_min = diarization_speakers_min
        self.diarization_speakers_max = diarization_speakers_max
        self.status = status
        self.created_date_time = datetime.fromisoformat(created_date_time)
        self.display_name = display_name

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __str__(self) -> str:
        return str(self.__dict__)

class TranscriptionReport:
    def __init__(self) -> None:
        pass
