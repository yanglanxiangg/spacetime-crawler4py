import re
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse,urldefrag,urljoin
from simhash import Simhash
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

p1 = re.compile(r"(http|https):\/\/.*\.ics\.uci\.edu\/.*")
p2 = re.compile(r"(http|https):\/\/.*\.cs\.uci\.edu\/.*")
p3 = re.compile(r"(http|https):\/\/.*\.informatics\.uci\.edu\/.*")
p4 = re.compile(r"(http|https):\/\/.*\.stat\.uci\.edu\/.*")
p5 = re.compile(r"(http|https):\/\/today\.uci\.edu\/department\/information\_computer\_sciences\/.*")

global visited
visited = set()
global uniqueU
uniqueU = set()
global trap
trap = set()
global info
info = dict()



stop_words = set(stopwords.words('english'))

# This function is copied from the documentation of simhash library to be used with calculting hash values
# Source: https://leons.im/posts/a-python-implementation-of-simhash-algorithm/
def get_features(s):
    width = 3
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]


def compute_r(v1,v2):
    count = 0
    for i in range(len(v1)):
        if v1[i] == v2[i]:
            count += 1
    return count/len(v1)

def compute_r1(a,b):
    if b > a:
        return b-a
    elif a > b:
        return a-b
    elif a == b:
        return 0


def scraper(url, resp):
    if resp.status in [200,201,202]:
        defrag = urlparse(url)
        if url not in visited:
            visited.add(url)
            with open('allPage.txt', 'a') as file1:
                file1.write(url+'\n')
        if defrag.netloc not in uniqueU:
            uniqueU.add(defrag.netloc)
            with open('subdomains.txt', 'a') as file4:
                file4.write(defrag.netloc+'\n')
        response = resp.raw_response
        soup = bs(response.content, 'lxml')
        tags = soup.find_all('a')
        links = extract_next_links(url, resp)

        # Check for trap
        if len(visited) > 10:
            tra = soup.find_all("div", class_="comment-content")
            if len(tra) > 100:
                trap.add(urlparse(url).scheme + "://"+urlparse(url).netloc)
                return list()

        # Remove noise
        for tag in tags:
            if soup.a != None:
                soup.a.decompose()
        #Retrieve Info
        text = soup.get_text(" ", strip=True)
        text_tokens = word_tokenize(text)
        tokens_without_punc = [word for word in text_tokens if word.isalnum()]
        tokens_without_sw = [word for word in tokens_without_punc if word not in stop_words]

        #Check for Similarity
        if len(info.keys()) > 10:
            if len(tokens_without_sw) > 100:
                for link,link_info in info.items():
                    if len(text) != 0 and link_info[0] != 0:
                        if compute_r1(len(text),link_info[0]) <= 200:
                            if len(str(Simhash(get_features(text)).value)) == len(link_info[1]):
                                if compute_r(str(Simhash(get_features(text)).value),link_info[1]) >= 0.9:
                                    return list()

        if len(tokens_without_sw) > 100:
            with open('content.txt', 'a') as file2:
                for word in tokens_without_sw:
                    file2.write(word+' ')
                file2.write('\n')

            with open('longestPage.txt', 'a') as file3:
                 file3.write(url + "::::" + str(len(tokens_without_sw)) + "\n")
        
            info_l = [len(text),str(Simhash(get_features(text)).value)]
            info[url] = info_l

        return [link for link in links if is_valid(link)]

    else:
        return list()

def extract_next_links(url, resp):
    domain = "https://"+urlparse(url).netloc
    response = resp.raw_response
    soup = bs(response.text, 'lxml')
    tags = soup.find_all('a')
    lis = set()
    for tag in tags:
        ad = tag.get('href')
        ad = urljoin(domain,ad)
        if ad not in visited:
            if len(urlparse(ad).fragment) > 0:
                a = urlparse(ad).scheme + "://"+urlparse(ad).netloc + urlparse(ad).path
                lis.add(a)
                if (p1.match(a) is None and p1.match(a) is None and p2.match(a) is None and p3.match(a) is None and p4.match(a) is None and p5.match(a) is None) is False:
                    if urlparse(a).netloc not in uniqueU:
                        uniqueU.add(urlparse(a).netloc)
                        with open('subdomains.txt', 'a') as file4:
                            file4.write(urlparse(a).netloc+'\n')
            else:
                lis.add(ad)
    return list(lis)

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # Check for the specific urls
        if p1.match(url) is None and p1.match(url) is None and p2.match(url) is None and p3.match(url) is None and p4.match(url) is None and p5.match(url) is None:
            return False
        if "/pdf/" in url:
            return False
        if "calendar" in url.lower():
            return False
        if "http://http://" in url:
            return False
        if "attachment/" in url:
            return False
        if "wiki/public/wiki" in url:
            return False
        if "wics.ics.uci.edu/events/" in url:
            return False
        if "pdf" in urlparse(url).path or "replytocom" in urlparse(url).path:
            return False
        if "comment" in urlparse(url).fragment or "respond" in urlparse(url).fragment or "branding" in urlparse(url).fragment:
            return False
        if "do=" in urlparse(url).query or "idx=" in urlparse(url).query or "share=" in urlparse(url).query or "version=" in urlparse(url).query or "id=" in urlparse(url).query or 'action=history' in urlparse(url).query:
            return False
        if (urlparse(url).scheme + "://"+urlparse(url).netloc) in trap:
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|jpg|img|py"
            + r"|png|tiff?|mid|mp2|mp3|mp4|war|java|sh"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|odc|txt|ppsx|ipynb|sql"
            + r"|thmx|mso|arff|rtf|jar|csv|Z|ics|r|apk"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        

    except TypeError:
        print ("TypeError for ", parsed)
        raise