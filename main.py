from playwright.sync_api import sync_playwright
import requests
import xml.etree.ElementTree as ET
import re

mpd_file_urls = []

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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.route('**/*', handle_route)
    page.goto('https://360tka.sk/videos/s-jakubcik-je-jednoduchsie-teraz-velke-veci-nestihat-lebo-je-s-tym-spojene-velke-riziko')
    page.wait_for_timeout(10000)
    browser.close()
    
mpd_text = None
if len(mpd_file_urls) > 0:
    response = requests.get(mpd_file_urls[0])
    if response.status_code == 200:
        mpd_text = response.text
    else:
        print(f"Error: {response.status_code}")

pattern = r"(?:und_)?(\d+)\.m4s"
query_pattern = r"contentId=([^&\"]+)"
namespace = "urn:mpeg:dash:schema:mpd:2011"
ET.register_namespace("", namespace)

if mpd_text:
    root = ET.fromstring(mpd_text)

    # Use namespace-aware searching
    def ns(tag):
        return f"{{{namespace}}}{tag}"

    representations = root.findall(f".//{ns('Representation')}")
    
    first_rep = representations[0]
    first_base_url = first_rep.find(f".//{ns('BaseURL')}").text
    first_segment_urls = first_rep.findall(f".//{ns('SegmentURL')}")
    last_segment = first_segment_urls[-1].get("media")
    second_segment = first_segment_urls[1].get("media")
    query = re.search(query_pattern, second_segment).group(0)
    match = re.search(pattern, last_segment)
    
    if not match:
        print("No matching segment found.")
        exit()
    
    new_string = latest_string = last_segment
    while True:
        # increase the number for the next iteration
        new_string = re.sub(pattern, increase_number, new_string)
        
        full_url = first_base_url + new_string + f"?{query}"  # construct the full url
        response = requests.get(full_url)
        
        if response.status_code != 200:
            print(f"request failed for: {full_url} (status {response.status_code})")
            break
            
        latest_string = new_string

        print(f"success: {full_url}")

    if latest_string == last_segment:
        print("video is unlocked")
    else:
        print("video is locked")
        
        for idx, rep in enumerate(representations):
            rep_id = rep.get("id")
            print(f"\nrepresentation id: {rep_id}")
            base_url = rep.find(f".//{ns('BaseURL')}")
            print(f"base url: {base_url.text}")

            segment_list = rep.find(f".//{ns('SegmentList')}")
            if segment_list is not None:
                for i in range(int(re.search(pattern, last_segment).group(1)) + 1, int(re.search(pattern, latest_string).group(1))):
                    prefix = "und_" if idx == len(representations) - 1 else ""
                    new_segment = ET.Element(ns("SegmentURL"), {"media": f"{prefix}{i}.m4s?{query}"})
                    segment_list.append(new_segment)

    final_mpd = ET.tostring(root, encoding="unicode")
    with open("index.mpd", "w") as file:
        file.write(final_mpd)
