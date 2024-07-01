import requests
import os
from tqdm import tqdm
import re

# Nome do arquivo M3U
m3u_file = 'playlist.m3u'

# Função para baixar um arquivo a partir de um URL com barra de progresso
def download_file(url, local_filename):
    # Verifica se o arquivo local já existe
    if os.path.exists(local_filename):
        print(f'O arquivo {local_filename} já existe. Pulando o download.')
        return local_filename
    
    max_retries = 4
    for attempt in range(max_retries):
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                with open(local_filename, 'wb') as f, tqdm(
                    desc=local_filename,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))
            print(f'{url} baixado com sucesso!')
            return local_filename
        except (requests.RequestException, OSError) as e:
            print(f'Erro ao baixar {url}. Tentativa {attempt + 1} de {max_retries}. Detalhes: {e}')
            if os.path.exists(local_filename):
                os.remove(local_filename)
            if attempt == max_retries - 1:
                print(f'Falha ao baixar {url} após {max_retries} tentativas.')
                return None

# Função para substituir caracteres inválidos em nomes de diretório
def clean_filename(filename):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '-')
    return filename

# Função principal
def main():
    # Pergunta ao usuário onde ele quer baixar os arquivos
    destination_base_folder = input('Digite o diretório onde deseja baixar os arquivos: ')

    # Verifica se o diretório base existe
    if not os.path.isdir(destination_base_folder):
        print(f'O diretório {destination_base_folder} não existe.')
        return

    # Verifica se o arquivo M3U existe
    if not os.path.isfile(m3u_file):
        print(f'Arquivo {m3u_file} não encontrado.')
        return

    # Lê o arquivo M3U
    with open(m3u_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Variáveis para armazenar o nome da série, do episódio e do grupo
    series_name = ""
    episode_name = ""
    group_name = ""
    url_pattern = re.compile(r'^http.*\.mp4$')

    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF'):
            # Extraindo o nome da série, do episódio e do grupo
            try:
                series_name = re.search(r'tvg-name="([^"]+)"', line).group(1)
                episode_parts = series_name.split()
                series_name = ' '.join(episode_parts[:-2])
                episode_name = episode_parts[-2] + episode_parts[-1]
                group_name = re.search(r'group-title="([^"]+)"', line).group(1)
            except AttributeError as e:
                print(f'Erro ao extrair informações da linha: {line}. Detalhes: {e}')
                continue
        elif url_pattern.match(line):
            # Baixando o arquivo
            url = line
            print(f'Baixando {url}...')
            clean_group_name = clean_filename(group_name)
            group_folder = os.path.join(destination_base_folder, clean_group_name)
            if not os.path.exists(group_folder):
                os.makedirs(group_folder)
            clean_series_name = clean_filename(series_name)
            series_folder = os.path.join(group_folder, clean_series_name)
            if not os.path.exists(series_folder):
                os.makedirs(series_folder)
            local_filename = os.path.join(series_folder, f"{episode_name}.mp4")
            if not local_filename:
                print(f'Nome de arquivo inválido para {url}. Pulando download.')
                continue
            download_file(url, local_filename)

if __name__ == '__main__':
    main()
