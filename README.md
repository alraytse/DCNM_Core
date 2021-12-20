# Enterprise Network Services DCNM API Core module
************************
<br/><br/> 

This package contains several modules related to creating, managing and
maintaining API Calls to DCNM.  It is a prerequisite to the scripts provided in
our dcnm_scripts repository.


<br/><br/> 
_Please see examples and documentation provided in the code for reference and use._


<br/><br/> 
### Local install from wheel package

* Clone code from the server:

>git clone https://github.com/alraytse/DCNM_Core.git

>cd dcnm_core/dist


* If updating existing installation:

>python3 -m pip install dcnm-0.1.0-py3-none-any.whl --upgrade

<br/><br/> 
### Remote install from bitbucket

This step requires that you have access to our repositories in bitbucket

* install over https:

>python3 -m pip install git+https://github.com/alraytse/DCNM_Core.git



<br/><br/> 
### Uninstall dcnm core module from python

>python3 -m pip uninstall dcnm

<br/><br/> 
### Download production scripts

This is a collection of scripts used to run jobs against DCNM including:
creating, attaching and deploying new networks and interfaces and also provide a
way to backout or dettach/undeploy networks and interfaces. This scripts require
the DCNM core module in order to run. You can install the scripts from:


>git clone 
https://github.com/alraytse/DCNM_Core.git
<br/><br/> 
## Install missing dependencies
****************************


      *** If the server already has requests module installed, just move on and run the
      scripts. there is no need to proceed with steps below. ***

      How do you know if its installed? Run a script, if you are presented with
      a username: prompt, there is no problem, just skip this section entirely.

      Sadly, the requests module included here no longer includes urllib3 so we
      need to install it for requests to work properly.

        If you have internet access and know how to work the proxy server just do:
          
          python3 -m pip install urllib3

        other wise you need to download this module and exact versions from
        pypi and do a manual install:

          python3 -m pip chardet-3.0.4-py2.py3-none-any.whl
          python3 -m pip idna-2.5-py2.py3-none-any.whl
          python3 -m pip urllib3-1.21.1-py2.py3-none-any.whl

<br/><br/> 
### Contributors
******************


<br/><br/> 

