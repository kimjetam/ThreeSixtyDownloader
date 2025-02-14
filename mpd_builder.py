from playwright.sync_api import sync_playwright
import requests
import xml.etree.ElementTree as ET
import re
import sys
import argparse
import os

sys.stdout.reconfigure(line_buffering=True)
mpd_file_urls = []
namespace = "urn:mpeg:dash:schema:mpd:2011"
ET.register_namespace("", namespace)
m4s_pattern = r"(?:und_)?(\d+)\.m4s"
query_pattern = r"contentId=([^&\"]+)"

def handle_route(route):
    if "index.mpd" in route.request.url or "m4s" in route.request.url:
        print(f"Blocking request to: {route.request.url}")
        mpd_file_urls.append(route.request.url)
        route.abort()  
    else:
        route.continue_()

def increase_number(match):
    number = int(match.group(1))  
    return match.group(0).replace(str(number), str(number + 1))  
    
def run_browser(url, timeout):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.route('**/*', handle_route)
        page.goto(url)
        page.wait_for_timeout(timeout)
        browser.close()
        
def fetch_mpd_content():
    mpd_text = None
    if len(mpd_file_urls) > 0:
        response = requests.get(mpd_file_urls[0])
        if response.status_code == 200:
            mpd_text = response.text
        else:
            print(f"Error of fetching mpd file: {response.status_code}")
    return mpd_text
    
def is_valid_xml(xml_string):
    try:
        ET.fromstring(xml_string)  # Try to parse the XML string
        return True
    except ET.ParseError:
        return False

def ns(tag):
    return f"{{{namespace}}}{tag}"
    
def get_missing_segments(xml):
    representations = xml.findall(f".//{ns('Representation')}")
    
    if not representations or len(representations) == 0:
        print("Error: MPD is missing representation elements")
        print(-1)
        
    rep = representations[0]
    base_url = rep.find(f".//{ns('BaseURL')}").text
    segment_url_elements = rep.findall(f".//{ns('SegmentURL')}")
    last_original_segment_url = segment_url_elements[-1].get("media")
    second_segment_url = segment_url_elements[1].get("media")
    
    query_param = re.search(query_pattern, second_segment_url)
    if query_param == None:
        query_param = ""
    else:
        query_param = query_param.group(0)
    
    if not re.search(m4s_pattern, last_original_segment_url):
        print("No matching segment found.")
        exit()
    
    missing_segments = []
    latest_string = last_original_segment_url
    while True:
        # increase the number for the next iteration
        new_string = re.sub(m4s_pattern, increase_number, latest_string)
        
        full_url = base_url + new_string + f"?{query_param}"  # construct the full url
        response = requests.get(full_url)
        
        if response.status_code != 200:
            print(f"request failed for: {full_url} (status {response.status_code})")
            break
        
        latest_string = new_string
        missing_segments.append(latest_string)

        print(f"success: {full_url}")
        
    return missing_segments, query_param, last_original_segment_url
    
def enrich_mpd(mpd_content):
    if not is_valid_xml(mpd_content):
        print("Error: The fetched MPD file has incorrect format", flush=True)
        sys.exit(1)  # Exits the script with a non-zero status (indicating an error)

    xml_root = ET.fromstring(mpd_content)
     
    missing_segments, query_param, last_segment = get_missing_segments(xml_root)
    representations = xml_root.findall(f".//{ns('Representation')}")
    
    if len(missing_segments) == 0:
        print("MPD file was already complete. Video is not locked to public.")
    else:
        print("MPD file was incomplete. Updating MPD file with missing segments.")
        
        for idx, rep in enumerate(representations):
            rep_id = rep.get("id")
            print(f"\nrepresentation id: {rep_id}")
            base_url = rep.find(f".//{ns('BaseURL')}")
            print(f"base url: {base_url.text}")

            segment_list = rep.find(f".//{ns('SegmentList')}")
            if segment_list is not None:
                for ms in missing_segments:
                    num = re.search(m4s_pattern, ms).group(1)
                    prefix = "und_" if idx == len(representations) - 1 else ""
                    new_segment = ET.Element(ns("SegmentURL"), {"media": f"{prefix}{num}.m4s?{query_param}"})
                    segment_list.append(new_segment)

    return ET.tostring(xml_root, encoding="unicode")

        
def main(url, filename, output_dir, timeout):
    run_browser(url, timeout)
    mpd_content = fetch_mpd_content()
    
    if mpd_content == None:
        print("Error: Failed to fetch MPD content.", flush=True)
        sys.exit(1)  # Exits the script with a non-zero status (indicating an error)
    
    final_mpd = enrich_mpd(mpd_content)
    full_path = os.path.join(output_dir, filename)

    print(f"DONE. Saving to {full_path}")
    with open(full_path, "w") as file:
        file.write(final_mpd)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MPD Builder")
    parser.add_argument("--url", required=True, help="(required) URL of the video page")
    parser.add_argument("--filename", default="index.mpd", help="MPD output file name")
    parser.add_argument("--output_dir", default=".", help="output folder for mpd file")
    parser.add_argument("--timeout", type=int, default=10000, help="Timeout for video page request interception in milliseconds (default: 10000)")
    
    args = parser.parse_args()
    
    main(args.url, args.filename, args.output_dir, args.timeout)

