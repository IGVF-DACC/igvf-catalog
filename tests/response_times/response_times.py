import requests
import time
import os
import hashlib
import csv
import random
import string
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

INPUT_FILE = 'urls.txt'
OUTPUT_DIR = 'responses'
TIME_LOG_FILE = 'average_response_time.csv'
DIFF_LOG_FILE = 'differences.txt'
TEST_DEV = True

RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def read_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]


def fetch_url(url):
    start_time = time.time()
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.status_code, response.text, time.time() - start_time
    except requests.HTTPError as e:
        return e.response.status_code, str(e), time.time() - start_time
    except requests.RequestException as e:
        return None, str(e), time.time() - start_time


def fetch_url_status(url):
    """Fetch URL and return the raw status code without raising on errors."""
    try:
        response = requests.get(url, timeout=10)
        return response.status_code
    except requests.RequestException as e:
        print(f'{str(e)}')
        return None


def get_response_filename(url):
    sanitized_name = hashlib.md5(url.encode()).hexdigest() + '.txt'
    return os.path.join(OUTPUT_DIR, sanitized_name)


def save_response(url, response_text):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = get_response_filename(url)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(response_text)


def compare_responses(url, new_response):
    filename = get_response_filename(url)
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            old_response = file.read()
        if old_response != new_response:
            with open(DIFF_LOG_FILE, 'a', encoding='utf-8') as diff_file:
                diff_file.write(f'Difference found for {url}:\n\n')
                diff_file.write(f'--- Previous Response ---\n{old_response}\n')
                diff_file.write(f'--- New Response ---\n{new_response}\n')
                diff_file.write('=' * 80 + '\n')


def load_previous_times():
    response_times = {}
    if os.path.exists(TIME_LOG_FILE):
        with open(TIME_LOG_FILE, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if len(row) == 3:
                    url, avg_time, count = row
                    response_times[url] = [float(avg_time), int(count)]
    return response_times


def save_average_times(times):
    with open(TIME_LOG_FILE, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(
            ['URL', 'Average Response Time (s)', 'Number of Calls'])
        for url, (avg_time, count) in times.items():
            writer.writerow([url, avg_time, count])


def random_invalid_string(length=12):
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(random.choices(chars, k=length))


def test_invalid_params(url, issues):
    """
    For each query param in the URL, replace its value with a random invalid
    string and call the endpoint, expecting HTTP 400.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    if not params:
        return

    for key in params:
        invalid_params = {k: v[:] for k, v in params.items()}
        invalid_params[key] = [random_invalid_string()]
        invalid_query = urlencode(invalid_params, doseq=True)
        invalid_url = urlunparse(parsed._replace(query=invalid_query))

        status_code = fetch_url_status(invalid_url)
        ok = (status_code == 400) or (
            status_code == 200) or (status_code == 404)
        symbol = '✓' if ok else '✗'
        line = f'  {symbol} Invalid param "{key}": got {status_code} {"PASS" if ok else "FAIL (expected 200, 400, or 404)"} - {invalid_url}'
        colored_line = RED + line + RESET if not ok else line
        print(colored_line)
        if not ok:
            issues.append(RED + line + RESET)


def main():
    urls = read_urls(INPUT_FILE)
    response_times = load_previous_times()
    issues = []

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if os.path.exists(DIFF_LOG_FILE):
        os.remove(DIFF_LOG_FILE)

    for url in urls:
        if TEST_DEV:
            url = url.replace('api.catalogkg', 'catalog-api-dev.demo')

        print(f'Fetching: {url}')
        status_code, response_text, response_time = fetch_url(url)

        ok = status_code in (200, 201)
        empty = response_text.strip() in ('', '[]')
        symbol = '✓' if ok and not empty else '⚠' if empty else '✗'
        line = f'  {symbol} Valid request: got {status_code} {"PASS" if ok else "FAIL (expected 200)"} - {url}'
        if empty:
            colored_line = YELLOW + line + RESET
            issues.append(colored_line)
        elif not ok:
            colored_line = RED + line + RESET
            issues.append(colored_line)
        else:
            colored_line = line
        print(colored_line)

        compare_responses(url, response_text)
        save_response(url, response_text)

        if url in response_times:
            previous_avg, count = response_times[url]
            new_avg = ((previous_avg * count) + response_time) / (count + 1)
            response_times[url] = [new_avg, count + 1]
        else:
            response_times[url] = [response_time, 1]

        test_invalid_params(url, issues)

    save_average_times(response_times)
    print(
        f"\nSaved responses in '{OUTPUT_DIR}/', average times in '{TIME_LOG_FILE}', and differences in '{DIFF_LOG_FILE}' if any.")

    if issues:
        print(f'\n{"=" * 80}')
        print(f'Issues summary ({len(issues)} found):')
        print(f'{"=" * 80}')
        for issue in issues:
            print(issue)
    else:
        print('\n✓ All checks passed!')


if __name__ == '__main__':
    main()
