import sys
import re

try:
    # Python 3
    from urllib.request import urlopen
    import urllib.parse as parse
    from urllib.error import URLError
except ImportError:
    # Python 2
    from urllib2 import urlopen, URLError
    import urlparse as parse


def getUrl(domain):
    """
    Given a domain, return a valid URL, inserting a scheme if necessary.
    """

    p = parse.urlparse(domain)
    if p.scheme == '':
        p = parse.urlparse('http://' + domain)

    return p.geturl()


def findEmailAddresses(domain):
    """
    Given a domain name, find and return a list of email addresses on that
    web page, and any discoverable web page in the domain.
    """

    # First, construct a valid url from the domain name
    url = getUrl(domain)

    # Crawl 
    addresses = crawlForEmail(url)
    return addresses


def getPage(url):
    """
    Retrieve webpage stream for a given URL. If the requested resource is not 
    found or an error occurs, the empty string "" will be returned.
    """

    try:
        resp = urlopen(url)
        return resp
    except URLError as err:
        return ""


def getEmails(s):
    """
    Find and return all email addresses in the given string s.
    """

    # A regex pattern for email addresses
    email_pattern = re.compile(r"([A-Za-z0-9#\-_~!$&'()*+,;=:]+"
                                "(?:\.[A-Za-z0-9#\-_~!$&'()*+,;=:]+)*"
                                "@[A-Za-z0-9\-]+\.[A-Za-z0-9\-]+)")
    emails = email_pattern.findall(s)

    # Strip off the "mailto:" before returning, for cases where an email link
    # is given, but not the email text
    emails = [email [7:] if email.startswith("mailto:") else email 
              for email in emails] 
    return emails


def getLinks(s, domain):
    """
    Find and return all clickable links in the given string s.
    """

    # Find all links of the form <a href="(link)"
    link_pattern = re.compile(r"""<a[^<>]+href\s*=\s*"([^"]+)""")
    links = list(set(link_pattern.findall(s)))

    # Add the domain to relative links
    links = [parse.urljoin(domain, link) for link in links]

    # Finally, remove any links not in the domain
    links = [link for link in links 
             if parse.urlparse(link).geturl().startswith(domain)]

    return links


def crawlForEmail(url, domain="", visited=set()):
    """
    Recursive function that scans for emails in the text on the page at url,
    then recursively calls on each link on that page in the same domain that
    is not in the visited set, and returns all emails found in this way.
    """

    # First get all text, and get all emails and links
    resp = getPage(url)
    if resp == "":
        # On error, return the empty set; no emails found
        return set()

    rtext = resp.read()
    if domain == "":
        # If no domain was given, the url was the domain
        domain = resp.geturl()
        visited.add(domain)

    # Find the emails and links from the page text
    emails = set(getEmails(rtext))
    links = getLinks(rtext, domain)

    # Remove any links already visited
    links = [link for link in links if link not in visited]

    # Add all of the links intended to visit to the visited set
    visited.update(set(links))

    for link in links:
        # Recur on this function, adding any found emails to the email set
        emails.update(crawlForEmail(link, domain, visited))       

    return emails


def printUsage():
    """
    Prints the usage statement for the program. A domain name should
    be given as the first and only argument to the program.
    """

    print "USAGE: find_email_addresses.py [DOMAIN.EXT]"


if __name__ == "__main__":
    # Verify the correct number of arguments
    if len(sys.argv) != 2:
        printUsage()
    else:
        emails = findEmailAddresses(sys.argv[1])
        if len(emails) > 0:
            print "Found these email addresses:"
            for email in emails:
                print email