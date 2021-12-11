# 05-07-2020 10:40:21 AM, pytest suite for dcnm core module

* requires flask for real api calls to mocked server
* can run configured as fixture in conftest.py or standalone

e.g.

  $ pytest -m live_calls -sv



