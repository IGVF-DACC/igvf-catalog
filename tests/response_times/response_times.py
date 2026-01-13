import requests
import time
import os
import hashlib
import csv

INPUT_FILE = 'urls.txt'
OUTPUT_DIR = 'responses'
TIME_LOG_FILE = 'average_response_time.csv'
DIFF_LOG_FILE = 'differences.txt'
TEST_DEV = True


def read_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]


def fetch_url(url):
    start_time = time.time()
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text, time.time() - start_time
    except requests.RequestException as e:
        print(f'{str(e)}')
        return str(e), time.time() - start_time


def get_response_filename(url):
    # using md5 of endpoint to avoid very large filenames
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


def main():
    urls = read_urls(INPUT_FILE)
    response_times = load_previous_times()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if os.path.exists(DIFF_LOG_FILE):
        os.remove(DIFF_LOG_FILE)  # Clear previous diff logs

    for url in urls:
        if TEST_DEV:
            url = url.replace('api.catalog', 'catalog-api-dev.demo')

        print(f'Fetching: {url}')

        response_text, response_time = fetch_url(url)

        if response_text == '[]':
            print('^^^ Warning: Empty response')

        compare_responses(url, response_text)
        save_response(url, response_text)

        if url in response_times:
            previous_avg, count = response_times[url]
            new_avg = ((previous_avg * count) + response_time) / (count + 1)
            response_times[url] = [new_avg, count + 1]
        else:
            response_times[url] = [response_time, 1]

    save_average_times(response_times)

    print(
        f"Saved responses in '{OUTPUT_DIR}/', average times in '{TIME_LOG_FILE}', and differences in '{DIFF_LOG_FILE}' if any.")


if __name__ == '__main__':
    main()
