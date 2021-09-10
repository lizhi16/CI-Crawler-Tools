# Crawling dockerhub for all Dockerfile, and checking this Dockerfile whether has malicious behaviors
import sys
from travis import Start_analyze_travis
from circleci import Start_analyze_circleci

if __name__ == '__main__':
    #(440080000, 440900000)
    #Start_analyze_travis(600000000, 650000000, 5000)
    Start_analyze_circleci(sys.argv[1])
