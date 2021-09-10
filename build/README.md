# How to Build for Release on PyPi

Part of these instructions are cribbed from [https://packaging.python.org/tutorials/packaging-projects/](https://packaging.python.org/tutorials/packaging-projects/), and are meant for a Linux OS. They assume you've already set up an account and [gotten an API token on pypi.org](https://pypi.org/manage/account/#api-tokens).

. Create a branch named with the new version number, if you haven't already
. Ensure that the version number is set in ```setup.py```
. Make sure to update ```CHANGELOG.md```
. Update the documentation as necessary
. Make sure all the tests pass per the instructions at [../tests/readme.md](../tests/readme.md)
. Push the branch to Github with ```git push --set-upstream origin VERSION``` where ```VERSION``` is the version number/name of the branch
. Make sure the documentation for that version builds at [https://readthedocs.org/projects/rpi-rfm69/builds/](https://readthedocs.org/projects/rpi-rfm69/builds/)
. Do ```source build.sh``` in this directory to create a virtual environment and build the release files
. Upload the new packages to pypi by doing ```python3 -m twine upload -u __token__ dist/*``` and entering your API token

To clean up the build, just do ```source clean.sh```.
