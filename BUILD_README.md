Building module as python  package for PIP install
**************************************************

* Project directory structure

```
dcnm_bb/
├── README.md
├── data
│   └── __init_.py
├── dcnm
│   ├── __init__.py       
│   └── requests
│   └── core
│       ├── __init__.py   
│       ├── dcnm_calls.py
│       ├── dcnm_parsers.py
│       ├── session.py
│       └── utilities.py
├── setup.py 

```

Build/Rebuild package
*********************

The following commands should run from the root directory where setup.py exists.
</br>

* If present, clean up build directory

>rm -rf build/

* Build/rebuild package

>python3 setup.py sdist bdist_wheel

</br>

Built binaries will be placed in dist/ and can be installed using PIP

Example:

* New install
>python3 -m pip install git+https://github.com/alraytse/DCNM_Core.git


