#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
import py2deb
import os
if __name__ == "__main__":
    try:
        os.chdir(os.path.dirname(sys.argv[0]))
    except:
        pass
    print
    p=py2deb.Py2deb("witter")   
    p.description="A twitter client in python"
    p.author="Jon Staley"
    p.mail="jon@spandexbob.co.uk"
    p.depends = "python2.5 (>= 2.5.1-1osso5), python2.5-osso, python-hildon, python-simplejson, python2.5-pycurl, python-twitter, python-conic, python-dbus, python-location, python-oauth2"
    p.section="user/network"
    p.icon = "/home/jon/devel/witter/fremantle/witter.jpg"
    p.arch="all"                #should be all for python, any for all arch
    p.urgency="low"             #not used in maemo onl for deb os
    p.distribution="fremantle"
    p.repository="extras-devel"
    p.xsbc_bugtracker="https://garage.maemo.org/tracker/?group_id=1153"
    p.postinstall="""#!/bin/sh
if [ -f ~/.witterdm ]; then
  rm ~/.witterdm
else
  :
fi

if [ -f ~/.wittermen ]; then
  rm ~/.wittermen
else
  :
fi

if [ -f ~/.wittertl ]; then
  rm ~/.wittertl
else
  :
fi

if [ -f ~/.witterUser ]; then
  sed "/last_id\|last_dm\|last_men/d" ~/.witterUser > ~/.tmp_user
  mv ~/.tmp_user ~/.witterUser
  chown user:users ~/.witterUser
else
  :
fi
    """
    version = "0.3.8"           #Version of your software, e.g. "1.2.0" or "0.8.2"
    build = "17"                 #Build number, e.g. "1" for the first build of this version of your software. Increment for later re-builds of the same version of your software.
                                #Text with changelog information to be displayed in the package "Details" tab of the Maemo Application Manager
    changeloginformation = "make sure witter.py has correct permissions" 
    dir_name = "src"            #Name of the subfolder containing your package source files (e.g. usr\share\icons\hicolor\scalable\myappicon.svg, usr\lib\myapp\somelib.py). We suggest to leave it named src in all projects and will refer to that in the wiki article on maemo.org
    #Thanks to DareTheHair from talk.maemo.org for this snippet that recursively builds the file list 
    for root, dirs, files in os.walk(dir_name):
        real_dir = root[len(dir_name):]
        fake_file = []
        if not '.svn' in root:
            for f in files:
                fake_file.append(root + os.sep + f + "|" + f)
        if len(fake_file) > 0:
            p[real_dir] = fake_file
    print p
    r = p.generate(version,build,changelog=changeloginformation,tar=True,dsc=True,changes=True,build=False,src=True)
 
