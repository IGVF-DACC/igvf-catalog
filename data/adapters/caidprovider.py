import requests
from rocksdict import Rdict, AccessType
import logging


class CAIDProvider:
    def __init__(self, caid_file_path: str):
        pass

    def get(self, hgvs: str) -> str:
        pass

    def close(self):
        self.caid_dict.close()


class ClingenCAIDProvider(CAIDProvider):

    CLINGEN_API_BASE_URL = 'https://reg.genome.network/allele?hgvs={hgvs}&fields=none+@id'

    def __init__(self, caid_file_path: str):
        self.caid_file_path = caid_file_path
        self.caid_dict = Rdict(
            caid_file_path, access_type=AccessType.read_only())

    def get(self, hgvs: str) -> str:
        caid = self.caid_dict.get(hgvs)
        if caid is None:
            try:
                caid = self._get_caid_from_clingen(hgvs)
            except Exception as e:
                logging.error(
                    f'Error getting CAID for {hgvs} from Clingen: {e}')
                return 'NULL'
            caid = self._format_caid(caid)
        return caid

    def _get_caid_from_clingen(self, hgvs: str) -> str:
        url = self.CLINGEN_API_BASE_URL.format(hgvs=hgvs)
        logging.info(f'Getting CAID from Clingen: {url}')
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['@id']

    def _format_caid(self, caid: str) -> str:
        if caid.startswith('http://reg.genome.network/allele/'):
            return caid.split('/')[-1]
        else:
            return 'NULL'


class LocalCAIDProvider(CAIDProvider):
    def __init__(self, caid_file_path: str):
        self.caid_file_path = caid_file_path
        self.caid_dict = Rdict(
            caid_file_path, access_type=AccessType.read_only())

    def get(self, hgvs: str) -> str:
        caid = self.caid_dict.get(hgvs)
        if caid is None:
            return 'NULL'
        return caid


def get_caid_provider(caid_file_path: str, local: bool = False) -> CAIDProvider:
    if local:
        return LocalCAIDProvider(caid_file_path)
    else:
        return ClingenCAIDProvider(caid_file_path)
