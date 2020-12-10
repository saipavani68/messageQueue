# CPSC 449 Web Back-End Engineering - Fall 2020

# Project description: 

This project involves adding asynchronous posting and hashtag analytics.

The following are the steps to run the project:
1. Clone the github repository https://github.com/nagisettipavani/messageQueue.git
2. Install the pip package manager by running the following commands
    sudo apt update
    sudo apt install --yes python3-pip
   
3. Install Flask by:
    python3 -m pip install Flask python-dotenv
   
4. Run the following commands to install Foreman and HTTPie:
    sudo apt update
    sudo apt install --yes ruby-foreman httpie(However, we tested using Postman)

5. To install and start Redis on Tuffix, use the following commands:
    sudo apt update
    sudo apt install --yes redis

6. Verify that Redis is up and running:
    redis-cli ping 
    PONG

7. Install RQ using the following command:
    sudo apt install --yes python3-rq

    Then verify that RQ is available:
    $ rq info
    
    0 queues, 0 jobs total

    0 workers, 0 queues

    Updated: 2020-11-23 14:24:53.725242

8. Then cd into the messageQueue folder
    
    In one tab of the terminal, run the following command

    redis-server

9. In another tab of the terminal, run the worker

    foreman run rq worker

10. In another tab of the terminal, run the following commands:
    flask init
    foreman start


Now the apis can be tested either using Postman(the one we followed) or using HTTPie(https://httpie.org/#examples).

We also make use of the Apache HTTP Server benchmarking tool (https://httpd.apache.org/docs/2.4/programs/ab.html) to compare the synchronous and asynchronous versions of postTweet(username, text) with some simple load testing.





