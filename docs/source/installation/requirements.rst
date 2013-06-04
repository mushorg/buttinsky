============
Requirements
============

Buttinsky Installation
======================

Prerequisites 
-------------

Install the basic packages::

    apt-get install python2.7 python-dev libevent-dev git

Install hpfeeds::

    cd /opt
    git clone git://github.com/rep/hpfeeds.git
    cd hpfeeds
    python setup.py install
    
Install requirements::

    pip install -r requirements.txt


Set-Up
------

Modify and rename conf/buttinsky.cfg.dist to conf/buttinsky.cfg
