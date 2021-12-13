""" package setup """
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dcnm",
    version="0.1.0",
    author="",
    author_email="",
    description="Handles API calls to Cisco Data Center Network Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alraytse/DCNM_Core.git",
    # scripts=[
    #     'dcnm_bulk_create_deploy', 'dcnm_bulk_create_deploy_backout',
    #     'dcnm_bulk_interface_attach', 'dcnm_bulk_interface_attach_backout'
    # ],
    packages=setuptools.find_packages(),
    install_requires=["chardet<=3.0.2", "requests<=2.22.0", "urllib3<=1.24.3"],
    python_requires="~=3.6",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
    ],
)
