# How to Build for Release on PyPi

These instructions are cribbed from [https://packaging.python.org/tutorials/packaging-projects/](https://packaging.python.org/tutorials/packaging-projects/), and are meant for a Linux OS. They assume you've already set up an account and [gotten an API token on pypi.org](https://pypi.org/manage/account/#api-tokens).

1. Make sure all the tests in ```tests``` pass
2. Ensure that the version number is set in ```setup.py```
3. Make sure to update ```CHANGELOG.md```
4. Make sure to update the documentation as necessary
4. Do ```source build.sh``` in this directory to create a virtual environment and build the release files
5. Upload the new packages to pypi by doing ```python3 -m twine upload -u __token__ dist/*``` and entering your API token
6. 

To clean up the build, just do ```source clean.sh```.
